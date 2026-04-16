"""This module contains the main process of the robot."""

import json

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from OpenOrchestrator.database.queues import QueueStatus
from itk_dev_shared_components.kmd_nova.authentication import NovaAccess
from itk_dev_shared_components.graph import authentication as graph_authentication
from itk_dev_shared_components.graph.mail import Email
from itk_dev_shared_components.graph.authentication import GraphAccess
from itk_dev_shared_components.graph import mail as graph_mail

from robot_framework import config
from robot_framework.sub_process import mail_process, nova_process, open_postbud_process


task_count = 0


def process(orchestrator_connection: OrchestratorConnection) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")

    openpostbud_key = orchestrator_connection.get_credential(config.OPENPOSTBUD_KEY).password
    op_headers = {"X-API-key": openpostbud_key}
    op_domain = orchestrator_connection.get_constant(config.OPENPOSTBUD_DOMAIN).value

    nova_creds = orchestrator_connection.get_credential(config.NOVA_API)
    nova_access = NovaAccess(nova_creds.username, nova_creds.password)

    graph_credentials = orchestrator_connection.get_credential(config.GRAPH_API)
    graph_access = graph_authentication.authorize_by_username_password(graph_credentials.username, **json.loads(graph_credentials.password))

    # Handle incoming emails and append queue
    emails = mail_process.get_emails(graph_access)

    for mail in emails:
        handle_mail_request(mail, orchestrator_connection, graph_access, op_headers, op_domain)

    # Handle queue
    global task_count
    while task_count < config.MAX_TASK_COUNT and (queue_element := orchestrator_connection.get_next_queue_element(config.QUEUE_NAME)):
        task_count += 1
        letter_id = queue_element.reference.split(":")[1]

        json_data =json.loads(queue_element.data)
        nova_params = mail_process.NovaParams(**json_data["nova_params"])
        shipment_name = json_data["shipment_name"]

        letter_status, recipient_cpr, letter_pdf = open_postbud_process.download_letter(letter_id, op_headers, op_domain)

        if letter_status not in ("Afsendt", "Leveret"):
            orchestrator_connection.set_queue_element_status(queue_element.id, status=QueueStatus.DONE, message=f"Letter has not been sent. Status: {letter_status}")
            continue

        if nova_params.reuse_case:
            nova_case = nova_process.search_for_case(recipient_cpr, nova_params.case_title, nova_access)
            if not nova_case:
                error_message = f"No case with the title '{nova_params.case_title}' exists for '{recipient_cpr}'"
                orchestrator_connection.set_queue_element_status(queue_element.id, status=QueueStatus.FAILED, message=error_message)
                raise ValueError(error_message)
        else:
            nova_case = nova_process.create_case(recipient_cpr, nova_params, nova_access)

        nova_process.attach_letter_to_case(nova_case, letter_pdf, shipment_name, nova_access)

        orchestrator_connection.set_queue_element_status(queue_element.id, QueueStatus.DONE, message=f"Journalised at {nova_case.case_number}")


def handle_mail_request(email: Email, orchestrator_connection: OrchestratorConnection, graph_access: GraphAccess, op_headers: dict[str, str], op_domain: str):
    """Create queue elements based on an incoming email request.

    Args:
        email: The email request.
        orchestrator_connection: The connection to Orchestrator.
        graph_access: The access to Graph.
        op_headers: The headers to use in OpenPostbud api calls.
        op_domain: The domain of OpenPostbud.
    """
    shipment_id, nova_params, user = mail_process.html_to_params(email.body)

    if not mail_process.check_az(user.az, orchestrator_connection):
        mail_process.send_rejection(user.email, shipment_id)
        graph_mail.delete_email(email, graph_access)
        return

    # Create queue elements
    shipment_name, letter_ids = open_postbud_process.get_letter_ids(shipment_id, op_headers, op_domain)
    for letter_id in letter_ids:
        reference = f"{shipment_id}:{letter_id}"
        data = {
            "nova_params": nova_params.to_dict(),
            "shipment_name": shipment_name
        }

        if not orchestrator_connection.get_queue_elements(config.QUEUE_NAME, reference=reference):
            orchestrator_connection.create_queue_element(
                queue_name=config.QUEUE_NAME,
                reference=reference,
                data=json.dumps(data, ensure_ascii=False),
                created_by="Robot"
            )
        else:
            raise ValueError(f"Queue element with reference '{reference}' already exists in queue.")

    mail_process.send_confirmation(user.email, shipment_id, len(letter_ids))
    graph_mail.delete_email(email, graph_access)


if __name__ == '__main__':
    import os

    conn_string = os.getenv("OpenOrchestratorConnString")
    crypto_key = os.getenv("OpenOrchestratorKey")
    oc = OrchestratorConnection("OpenPostbud journalisering", conn_string, crypto_key, '{"accepted_azs": ["az123456789"]}', "")
    process(oc)
