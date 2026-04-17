"""This module handles interactions with Graph and smtp."""

from dataclasses import dataclass, asdict
import json

from bs4 import BeautifulSoup
from itk_dev_shared_components.graph.authentication import GraphAccess
from itk_dev_shared_components.graph import mail as graph_mail
from itk_dev_shared_components.graph.mail import Email
from itk_dev_shared_components.smtp import smtp_util
from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework import config


@dataclass
class NovaParams:
    """A dataclass representing parameters for creating a Nova case."""
    case_title: str
    reuse_case: bool
    kle: str | None = None
    facet: str | None = None
    sensitivity: str | None = None
    department: str | None = None
    close_case: bool | None = None

    def to_dict(self):
        """Convert to a dictionary for use in a queue element."""
        if self.reuse_case:
            return {
                "case_title": self.case_title,
                "reuse_case": self.reuse_case
            }

        return asdict(self)


@dataclass
class User:
    """A dataclass representing a user."""
    email: str
    az: str


def get_emails(graph_access: GraphAccess) -> list[Email]:
    """Get all emails to be handled by the robot.

    Args:
        graph_access: The GraphAccess object used to authenticate against Graph.

    Returns:
        A filtered list of email objects to be handled.
    """
    # Get all emails from the relevant folder.
    mails = graph_mail.get_emails_from_folder("itk-rpa@mkb.aarhus.dk", config.MAIL_SOURCE_FOLDER, graph_access)

    # Filter the emails on sender and subject
    mails = [mail for mail in mails if mail.sender == "noreply@aarhus.dk" and mail.subject == config.MAIL_INBOX_SUBJECT]

    return mails


def html_to_params(html_content) -> tuple[str, NovaParams, User]:
    ''' Convert a OS2Forms email to an InputParams object.

    Args:
        html_content: OS2 email content containing headlines followed by data

    Returns:
        A tuple of the shipment id, a NovaParams object, a User object.
    '''
    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    result = {}
    for p in soup.find_all('p'):
        parts = p.get_text(separator='|').split('|')
        if len(parts) == 2:
            key, value = parts
            result[key.strip()] = value.strip()

    email_tag = soup.find('a', href=True, string=lambda text: text and '@' in text)
    if email_tag:
        email = email_tag.get_text()
        az_ident = email_tag.find_next_sibling(string=True).strip().split(': ')[1]
        result['Bruger'] = {"E-mail": email, "AZ-ident": az_ident}

    return (
        result["Forsendelses id"],
        NovaParams(
            case_title=result["Sagsoverskrift"],
            reuse_case=result["Brug eksisterende sag"] == "Valgt",
            kle=result.get("KLE-nummer"),
            facet=result.get("Handlingsfacet"),
            sensitivity=result.get("Følsomhed"),
            department=result.get("Afdeling"),
            close_case=result["Afslut sag"] == "Valgt" if "Afslut sag" in result else None
        ),
        User(
            email=result["Bruger"]["E-mail"],
            az=result["Bruger"]["AZ-ident"]
        )
    )


def check_az(az: str, orchestrator_connection: OrchestratorConnection) -> bool:
    """Check AZ from email against accepted list of AZ in process arguments.

    Args:
        orchestrator_connection: Connection containing process arguments with some accepted AZs
        email_az: A user identification (AZ) read from an email
    """
    accepted_azs = json.loads(orchestrator_connection.process_arguments)["accepted_azs"]
    return az.lower() in [az.lower() for az in accepted_azs]


def send_rejection(recipient: str, shipment_id: str):
    """Send a rejection email to the given recipient."""
    body = (
        f"Du har anmodet om at få OpenPostbud forsendelsen {shipment_id} journaliseret i Nova.\n"
        "Du er ikke på listen over brugere med adgang til dette. Din anmodning er derfor blevet afvist.\n"
        "Venlig hilsen\n"
        "Robotten"
    )

    smtp_util.send_email(
        receiver=recipient,
        sender=config.STATUS_SENDER,
        subject="Journaliseringsjob afvist",
        body=body,
        smtp_server=config.SMTP_SERVER,
        smtp_port=config.SMTP_PORT
    )


def send_confirmation(recipient: str, shipment_id: str, letter_count: int):
    """Send a confirmation email to the given recipient."""
    body = (
        f"Du har anmodet om at få OpenPostbud forsendelsen {shipment_id} journaliseret i Nova.\n"
        f"Alle {letter_count} breve i forsendelsen er nu blevet tilføjet til jobkøen og vil blive journaliseret snarest.\n"
        "Venlig hilsen\n"
        "Robotten"
    )

    smtp_util.send_email(
        receiver=recipient,
        sender=config.STATUS_SENDER,
        subject="Journaliseringsjob modtaget",
        body=body,
        smtp_server=config.SMTP_SERVER,
        smtp_port=config.SMTP_PORT
    )
