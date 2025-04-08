"""This module contains the main process of the robot."""

import base64
from datetime import datetime
import uuid
from io import BytesIO

import requests
from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from OpenOrchestrator.database.queues import QueueStatus
from itk_dev_shared_components.kmd_nova.authentication import NovaAccess
from itk_dev_shared_components.kmd_nova.nova_objects import NovaCase, Document, CaseParty, Task
from itk_dev_shared_components.kmd_nova import nova_cases, nova_documents, nova_tasks
from itk_dev_shared_components.kmd_nova import cpr as nova_cpr

from robot_framework import config


def process(orchestrator_connection: OrchestratorConnection) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")

    openpostbud_key = orchestrator_connection.get_credential(config.OPENPOSTBUD_KEY).password
    headers = {"X-API-key": openpostbud_key}
    domain = orchestrator_connection.get_constant(config.OPENPOSTBUD_DOMAIN)

    nova_creds = orchestrator_connection.get_credential(config.NOVA_API)
    nova_access = NovaAccess(nova_creds.username, nova_creds.password)

    letter_ids = get_letter_ids("hej", headers, domain)

    for letter_id in letter_ids:
        if not check_queue(letter_id, orchestrator_connection):
            continue

        queue_element = orchestrator_connection.create_queue_element(config.QUEUE_NAME, reference=letter_id, created_by="Robot")
        orchestrator_connection.set_queue_element_status(queue_element.id, QueueStatus.IN_PROGRESS)

        letter_pdf = download_letter(letter_id, headers, domain)
        nova_case = create_case("Cpr", nova_access)
        attach_letter_to_case(nova_case, letter_pdf, nova_access)

        orchestrator_connection.set_queue_element_status(queue_element.id, QueueStatus.DONE)


def get_letter_ids(shipment_id: str, headers: str, domain: str) -> list[str]:
    """Get all the letter ids in the given OpenPostbud shipment.

    Args:
        shipment_id: The id of the shipment.
        headers: The security header for OpenPostbud.
        domain: The domain of OpenPostbud.

    Returns:
        A list of letter ids.
    """
    response = requests.get(f"{domain}/api/shipment/{shipment_id}", headers=headers, timeout=10)
    response.raise_for_status()

    return response.json()['letter_ids']


def download_letter(letter_id: str, headers: str, domain: str) -> bytes:
    """Get the merged pdf file for the given letter in OpenPostbud.

    Args:
        letter_id: The id of the letter.
        headers: The security header for OpenPostbud.
        domain: The domain of OpenPostbud.

    Returns:
        The merged pdf file as bytes.
    """
    response = requests.get(f"{domain}/api/letter/{letter_id}", headers=headers, timeout=30)
    response.raise_for_status()

    return base64.b64decode(response.json()['letter_pdf'])


def check_queue(letter_id: str, orchestrator_connection: OrchestratorConnection) -> bool:
    """Check if a letter has already been handled.

    Args:
        letter_id: The id of the letter.
        orchestrator_connection: the connection to the Orchestrator.

    Returns:
        False if the letter is already in the queue.
    """
    queue_elements = orchestrator_connection.get_queue_elements(config.QUEUE_NAME, reference=letter_id)

    if queue_elements:
        return False

    return True


def create_case(cpr: str, nova_access: NovaAccess) -> NovaCase:
    """Create a new case in Nova.

    Args:
        cpr: The cpr to create the case for.
        nova_access: The access to the Nova api.

    Returns:
        The new case.
    """
    name = nova_cpr.get_address_by_cpr(cpr, nova_access)['name']

    case_party = CaseParty(
        role="Primær",
        identification_type="CprNummer",
        identification=cpr,
        name=name,
        uuid=None
    )

    # Create a new case
    case = NovaCase(
        uuid=str(uuid.uuid4()),
        title=,
        case_date=datetime.now(),
        progress_state='Afsluttet',
        case_parties=[case_party],
        kle_number=,
        proceeding_facet=,
        sensitivity=,
        caseworker=,
        responsible_department=,
        security_unit=
    )

    nova_cases.add_case(case, nova_access)
    return case


def attach_letter_to_case(case: NovaCase, letter_pdf: bytes, nova_access: NovaAccess):
    """Attach the given letter as a document on the given Nova case.

    Args:
        case: The case in Nova.
        letter_pdf: The letter as bytes.
        nova_access: The access to the Nova api.
    """
    letter_io = BytesIO(letter_pdf)
    doc_uuid = nova_documents.upload_document(letter_io, "Brev.pdf", nova_access)

    doc = Document(
        uuid=doc_uuid,
        title="Brev",
        sensitivity=,
        document_type="Udgående",
        document_date=datetime.now(),
        approved=True,
        description="Automatisk journaliseret af robot.",
        caseworker=
    )

    nova_documents.attach_document_to_case(case.uuid, doc, nova_access)
