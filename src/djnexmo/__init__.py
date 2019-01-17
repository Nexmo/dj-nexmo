from django.conf import settings

import nexmo

__version__ = '0.0.4'

default_app_config = "djnexmo.apps.NexmoConfig"

client = nexmo.Client(
    key=getattr(settings, "NEXMO_API_KEY", None),
    secret=getattr(settings, "NEXMO_API_SECRET", None),
    signature_secret=getattr(settings, "NEXMO_SIGNATURE_SECRET", None),
    signature_method=getattr(settings, "NEXMO_SIGNATURE_METHOD", None),
    application_id=getattr(settings, "NEXMO_APPLICATION_ID", None),
    private_key=getattr(settings, "NEXMO_PRIVATE_KEY", None),
)
