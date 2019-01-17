"""
djnexmo.decorators - decorators that make it easier to work with Nexmo.


"""

from datetime import datetime, timezone
from functools import wraps
import json

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import attr
from marshmallow import Schema, fields, post_load, EXCLUDE
import pytz

from .models import SMSMessagePart

from . import client


TZ_LONDON = pytz.timezone('Europe/London')

@attr.s
class IncomingSMS:
    """ Object representing an incoming SMS message or part-message, parsed from JSON. """
    message_id = attr.ib(type=str)
    msisdn = attr.ib(type=str)
    to = attr.ib(type=str)
    type = attr.ib(
        type=str, validator=attr.validators.in_(["text", "unicode", "binary"])
    )
    message_timestamp = attr.ib(type=datetime)
    timestamp = attr.ib(type=datetime)

    keyword = attr.ib(type=str, default=None)
    text = attr.ib(type=str, default=None)
    # TODO: Need to do something with these:
    data = attr.ib(default=None)
    udh = attr.ib(default=None)

    concat = attr.ib(type=bool, default=False)
    concat_part = attr.ib(type=int, default=None)
    concat_ref = attr.ib(type=str, default=None)
    concat_total = attr.ib(type=int, default=None)

    def reply(self, text, type="text"):
        client.send_message(
            {"to": self.msisdn, "from": self.to, "text": text, "type": type}
        )

    def to_model(self):
        data = {a.name: getattr(self, a.name) for a in attr.fields(self.__class__)}
        del data["concat"]
        return SMSMessagePart(**data)


class Timestamp(fields.Field):
    """ Marshmallow Field to convert a UTC unix time into a UTC timezone-aware datetime. """

    def _deserialize(self, value, attr, data):
        # `value` is a UNIX timestamp in Europe/London tz, as a string 🙄
        return datetime.utcfromtimestamp(int(value)).replace(tzinfo=timezone.utc)


class IncomingSMSSchema(Schema):
    """ Marshmallow schema to map from Nexmo incoming SMS JSON to an IncomingSMS instance. """
    msisdn = fields.Str()
    to = fields.Str()
    message_id = fields.Str(data_key="messageId")
    text = fields.Str()
    type = fields.Str(data_key="type")
    keyword = fields.Str()
    message_timestamp = fields.DateTime(
        data_key="message-timestamp", format="%Y-%m-%d %H:%M:%S"
    )
    timestamp = Timestamp()

    concat = fields.Bool()
    concat_part = fields.Int(data_key="concat-part")
    concat_ref = fields.Str(data_key="concat-ref")
    concat_total = fields.Int(data_key="concat-total")

    # TODO: Need to do something with these:
    data = fields.Str()
    udh = fields.Str()

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_sms(self, data):
        d = data["message_timestamp"]
        if d.tzinfo is None:
            data["message_timestamp"] = d.replace(tzinfo=timezone.utc)
        return IncomingSMS(**data)


incoming_sms_parser = IncomingSMSSchema()


def sms_webhook(func=None, *, validate_signature=True):
    """
    A decorator for views which respond to incoming SMS messages.

    Example::

        @sms_webhook()
        def birthday_rsvp_view(request):
            # Access the `IncomingSMS` object via `request.sms`
            if request.sms.text.upper() == 'YES':
                BirthdayResponses(sender_tel=request.sms.msisdn, attending=True).save()

    Behind the scenes, a couple of things are done for you:

    * The signature is verified against your signature secret, defined in
      `settings.NEXMO_SIGNATURE_SECRET`. If you don't want the signature to be
      verified, call with `sms_webhook` with `validate_signature=False`
    * Messages sent as multiple parts are stored in the database until all
      parts are available. The underlying view is only called once all parts
      are available and have been merged into a single `IncomingSMS` instance.
    """

    def decorator(func):

        @wraps(func)
        @csrf_exempt
        @require_POST
        def inner(request, *args, **kwargs):
            if request.content_type != "application/json":
                return HttpResponse("Unsupported request content-type.", status=415)
            try:
                data = json.loads(request.body.decode("utf-8"))
            except json.JSONDecodeError:
                return HttpResponse("Invalid JSON payload provided.", status=400)
            if not validate_signature or client.check_signature(data):
                if data.get("concat") == "true":
                    return _handle_message_part(request, data, func, args, kwargs)
                else:
                    request.sms = incoming_sms_parser.load(data)
                    return func(request, *args, **kwargs)
            else:
                return HttpResponse(
                    "Invalid signature.", status=403, reason="Invalid signature."
                )

        return inner

    if func is not None:
        return decorator(func)
    else:
        return decorator


def _handle_message_part(request, data, wrapped_func, args, kwargs):
    # Put it in the database.
    try:
        with transaction.atomic():
            incoming_sms = incoming_sms_parser.load(data)
            incoming_sms.to_model().save()
    except IntegrityError:
        return HttpResponse("Partial message already stored.")

    # Then query if we have all the parts
    matching_parts = SMSMessagePart.objects.filter(concat_ref=incoming_sms.concat_ref)
    count = matching_parts.count()
    expected = incoming_sms.concat_total
    if count == expected:
        # If we have all the parts then create a FrankenSMS from the pieces,
        # and call the wrapped view function:
        text = "".join(part.text for part in matching_parts)
        request.sms = IncomingSMS(
            msisdn=incoming_sms.msisdn,
            to=incoming_sms.to,
            message_id=incoming_sms.message_id,
            text=text,
            type=incoming_sms.type,
            keyword=incoming_sms.keyword,
            message_timestamp=incoming_sms.message_timestamp,
            timestamp=incoming_sms.timestamp,
            concat=False,
            concat_ref=incoming_sms.concat_ref,
        )
        matching_parts.delete()
        return wrapped_func(request, *args, **kwargs)
    else:
        return HttpResponse("Partial message received.")
