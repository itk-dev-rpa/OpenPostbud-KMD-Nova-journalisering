"""This module contains configuration constants used across the framework"""

from itk_dev_shared_components.kmd_nova.nova_objects import Caseworker

# The number of times the robot retries on an error before terminating.
MAX_RETRY_COUNT = 3

# Whether the robot should be marked as failed if MAX_RETRY_COUNT is reached.
FAIL_ROBOT_ON_TOO_MANY_ERRORS = True

# Error screenshot config
SMTP_SERVER = "smtp.adm.aarhuskommune.dk"
SMTP_PORT = 25
SCREENSHOT_SENDER = "robot@friend.dk"

# Constant/Credential names
ERROR_EMAIL = "Error Email"

OPENPOSTBUD_KEY = "OpenPostbud Key"
OPENPOSTBUD_DOMAIN = "OpenPostbud Domain"

NOVA_API = "Nova API"
GRAPH_API = "Graph API"

QUEUE_NAME = "OpenPostbud KMD Nova Journalisering"
MAX_TASK_COUNT = 500

# Config options
MAIL_SOURCE_FOLDER = "Indbakke/OpenPostbud Nova journalisering"
MAIL_INBOX_SUBJECT = "RPA - OpenPostbud journalisering i Nova (fra Selvbetjening.aarhuskommune.dk)"
STATUS_SENDER = "itk-rpa@ba.aarhus.dk"


# KMD Constants
KMD_DEPARTMENTS = {
    "4BFOLKEREG": {"name": "Folkeregister og Sygesikring", "id": "70403"},
    "4BBORGER": {"name": "Borgerservice", "id": "818485"},
    "4BFRONT": {"name": "Frontbetjening", "id": "1061417"},
    "4BFRONTTEL": {"name": "Kontaktcentret", "id": "1061418"},
    "4BKONTROL": {"name": "Kontrolteamet", "id": "70363"},
    "4BOPKRÆV": {"name": "Opkrævningen", "id": "70391"},
}

KMD_DEPARTMENT_SECURITY_PAIRS = {
    "4BFOLKEREG": "4BBORGER",
    "4BBORGER": "4BBORGER",
    "4BFRONT": "4BBORGER",
    "4BFRONTTEL": "4BBORGER",
    "4BKONTROL": "4BKONTROL",
    "4BOPKRÆV": "4BOPKRÆV",
}

KMD_SENSITIVITY = {
    "Fortrolige oplysninger": "Fortrolige",
    "Ikke fortrolige oplysninger": "IkkeFortrolige",
    "Særligt følsomme oplysninger": "SærligFølsomme",
    "Følsomme oplysninger": "Følsomme"
}

CASEWORKER = Caseworker(
    uuid="3eb31cbb-d6dc-4b01-9eec-0b415f5b89cb",
    name="Rpabruger Rpa15 - MÅ IKKE SLETTES RITM0055928",
    ident="AZRPA15"
)
