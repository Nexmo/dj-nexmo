from django.conf import settings
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pytest_configure():
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=["djnexmo"],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
            }
        },
        SECRET_KEY="this is n0t a seekret",
        NEXMO_SIGNATURE_SECRET="abcdefABCDEF12345",
        LANGUAGE_CODE="en-us",
        TIME_ZONE="UTC",
        USE_I18N=True,
        USE_L10N=True,
        USE_TZ=True,
    )
