"""This module handles interactions with OpenPostbud API."""

import base64

import requests


def get_letter_ids(shipment_id: str, headers: str, domain: str) -> tuple[str, list[str]]:
    """Get all the letter ids in the given OpenPostbud shipment.

    Args:
        shipment_id: The id of the shipment.
        headers: The security header for OpenPostbud.
        domain: The domain of OpenPostbud.

    Returns:
        The name of the shipment and a list of letter ids.
    """
    response = requests.get(f"{domain}/api/shipment/{shipment_id}", headers=headers, timeout=10)
    response.raise_for_status()
    response_json = response.json()

    return response_json["name"], response_json['letter_ids']


def download_letter(letter_id: str, headers: str, domain: str) -> tuple[str, str, bytes]:
    """Get the merged pdf file for the given letter in OpenPostbud.

    Args:
        letter_id: The id of the letter.
        headers: The security header for OpenPostbud.
        domain: The domain of OpenPostbud.

    Returns:
        The status and recipient of the letter and the merged pdf file as bytes.
    """
    response = requests.get(f"{domain}/api/letter/{letter_id}", headers=headers, timeout=30)
    response.raise_for_status()

    letter_json = response.json()

    return letter_json["status"], letter_json["recipient_id"], base64.b64decode(letter_json['letter_pdf'])
