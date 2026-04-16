"""This module handles interactions with KMD Nova."""

from datetime import datetime
import uuid
from io import BytesIO

from itk_dev_shared_components.kmd_nova.authentication import NovaAccess
from itk_dev_shared_components.kmd_nova.nova_objects import NovaCase, Document, CaseParty, Department
from itk_dev_shared_components.kmd_nova import nova_cases, nova_documents
from itk_dev_shared_components.kmd_nova import cpr as nova_cpr

from robot_framework import config
from robot_framework.sub_process.mail_process import NovaParams


def search_for_case(cpr: str, case_title: str, nova_access: NovaAccess) -> NovaCase | None:
    """Find an existing case in Nova with the given title."""
    cases = nova_cases.get_cases(cpr=cpr, case_title=case_title, nova_access=nova_access)

    for case in cases:
        if case.title == case_title:
            return case

    return None


def create_case(cpr: str, input_params: NovaParams, nova_access: NovaAccess) -> NovaCase:
    """Create a new case in Nova.

    Args:
        cpr: The cpr to create the case for.
        input_params: A NovaParams object describing the case parameters.
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

    department = _get_department(input_params.department)
    security_unit = _get_department(config.KMD_DEPARTMENT_SECURITY_PAIRS[input_params.department])

    # Create a new case
    case = NovaCase(
        uuid=str(uuid.uuid4()),
        title=input_params.case_title,
        case_date=datetime.now(),
        progress_state='Afsluttet' if input_params.close_case else "Opstaaet",
        case_parties=[case_party],
        kle_number=input_params.kle,
        proceeding_facet=input_params.facet,
        sensitivity=input_params.sensitivity,
        caseworker=config.CASEWORKER,
        responsible_department=department,
        security_unit=security_unit
    )

    nova_cases.add_case(case, nova_access)
    return case


def _get_department(department_code: str) -> Department:
    """Make a department object from department code

    Args:
        department_code: A KMD code matching a department

    Returns:
        A Department object created from data in config
    """
    data = config.KMD_DEPARTMENTS[department_code]
    department = Department(
            id=int(data["id"]),
            name=data["name"],
            user_key=department_code
        )
    return department


def attach_letter_to_case(case: NovaCase, letter_pdf: bytes, letter_title: str, nova_access: NovaAccess):
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
        title=letter_title,
        sensitivity="Fortrolige",
        document_type="Udgående",
        document_date=datetime.now(),
        approved=True,
        description="Udsendt via OpenPostbud. Automatisk journaliseret af robot.",
    )

    nova_documents.attach_document_to_case(case.uuid, doc, nova_access)

