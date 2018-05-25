
from datetime import datetime, timezone
import json
from pprint import pprint

import django
from django.db import transaction

import djnexmo as n
import djnexmo.decorators as d
import djnexmo.models as models

from random import shuffle
from unittest.mock import MagicMock, call, sentinel

import pytest


@pytest.fixture(name="partial_message")
def partial_message_fixture():
    return {
        "concat": "true",
        "concat-part": "1",
        "concat-ref": "78",
        "concat-total": "9",
        "keyword": "LOREM",
        "message-timestamp": "2018-04-24 14:05:19",
        "messageId": "0B000000D0EBB58D",
        "msisdn": "447700900419",
        "nonce": "0a455d75-459e-446c-9072-698728516d7c",
        "sig": "c4bc6301949691b6093772ba246a35eb",
        "text": "Lorem Ipsum is simply dummy text of the printing and typesetting in",
        "timestamp": "1524578719",
        "to": "447700900996",
        "type": "unicode",
    }


@pytest.fixture(name="complete_message")
def complete_message_fixture():
    return {
        "keyword": "THIS",
        "message-timestamp": "2018-04-24 14:05:19",
        "messageId": "0B000000D0EBB58D",
        "msisdn": "447700900419",
        "nonce": "0a455d75-459e-446c-9072-698728516d7c",
        "sig": "266c3734d3cf9baf6f293dae148e14f5",
        "text": "This is complete!",
        "timestamp": "1524578719",
        "to": "447700900996",
        "type": "unicode",
    }


def test_parse_part(partial_message):
    """ Ensure we can parse an incoming json sms request. """
    sms = d.IncomingSMSSchema().load(partial_message)
    assert isinstance(sms, d.IncomingSMS)
    assert sms.concat == True
    assert sms.concat_part == 1
    assert sms.concat_total == 9
    assert sms.concat_ref == "78"
    assert sms.keyword == "LOREM"
    assert (
        sms.message_timestamp == datetime(2018, 4, 24, 14, 5, 19, tzinfo=timezone.utc)
    )
    assert sms.message_id == "0B000000D0EBB58D"
    assert sms.msisdn == "447700900419"
    assert sms.to == "447700900996"
    assert (
        sms.text
        == "Lorem Ipsum is simply dummy text of the printing and typesetting in"
    )
    assert sms.timestamp == datetime(2018, 4, 24, 14, 5, 19, tzinfo=timezone.utc)
    assert sms.type == "unicode"


def test_to_model(partial_message):
    """ Ensure translating from the parsed object to the django model works. """
    sms = d.IncomingSMSSchema().load(partial_message).to_model()
    assert isinstance(sms, models.SMSMessagePart)
    assert not hasattr(sms, "concat")  # Just make sure we're looking at the model.
    assert sms.concat_part == 1
    assert sms.concat_total == 9
    assert sms.concat_ref == "78"
    assert sms.keyword == "LOREM"
    assert (
        sms.message_timestamp == datetime(2018, 4, 24, 14, 5, 19, tzinfo=timezone.utc)
    )
    assert sms.message_id == "0B000000D0EBB58D"
    assert sms.msisdn == "447700900419"
    assert sms.to == "447700900996"
    assert (
        sms.text
        == "Lorem Ipsum is simply dummy text of the printing and typesetting in"
    )
    assert sms.timestamp == datetime(2018, 4, 24, 14, 5, 19, tzinfo=timezone.utc)
    assert sms.type == "unicode"


@pytest.mark.django_db
def test_duplicate_partials(partial_message):
    """ Ensure saving the same message part twice fails. """
    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 0
    ), "There should be no parts stored before the test."
    sms = d.IncomingSMSSchema().load(partial_message).to_model()
    sms.save()

    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 1
    ), "Part should be saved."

    with pytest.raises(django.db.IntegrityError), transaction.atomic():
        sms2 = d.IncomingSMSSchema().load(partial_message).to_model()
        sms2.save()

    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 1
    ), "Duplicate part should be not be saved."


@pytest.mark.django_db
def test_decorator_partials(rf, partial_message):
    """ Ensure partial sms messages are handled corrrectly. """
    request = rf.post(
        "/sms/incoming",
        content_type="application/json",
        data=json.dumps(partial_message),
    )
    view = MagicMock()
    decorated = d.sms_webhook()(view)

    # Before doing anything, make sure we don't already have any parts saved:
    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 0
    ), "There should be no parts stored before the test."

    response = decorated(request)

    assert response.status_code == 200, "Request should be successful"
    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 1
    ), "Part should be saved."

    # Ensure a duplicate part doesn't also get saved:
    response = decorated(request)

    assert response.status_code == 200, "Request should be successful"
    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 1
    ), "No duplicate part should be saved."
    assert view.mock_calls == [], "Wrapped view should not be called."


@pytest.mark.django_db
def test_decorator_complete(rf, complete_message):
    request = rf.post(
        "/sms/incoming",
        content_type="application/json",
        data=json.dumps(complete_message),
    )

    view = MagicMock(return_value=sentinel.response)

    decorated = d.sms_webhook()(view)
    response = decorated(request)
    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 0
    ), "Message should not be saved."
    assert view.mock_calls == [call(request)], "Underlying view should be called."
    assert (
        response == sentinel.response
    ), "Result should be response from the underlying view."


@pytest.mark.django_db
def test_decorator_complete_bad_sig(rf, complete_message):
    complete_message["sig"] = "not-valid"
    request = rf.post(
        "/sms/incoming",
        content_type="application/json",
        data=json.dumps(complete_message),
    )
    view = MagicMock(return_value=sentinel.response)

    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 0
    ), "There should be no parts stored before the test."

    validating = d.sms_webhook(validate_signature=True)(view)
    response = validating(request)

    assert view.mock_calls == [], "Wrapped view should not be called."
    assert (
        response.status_code == 403
    ), "Decorator should return 403, permission denied."
    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 0
    ), "No part should be saved."

    nonvalidating = d.sms_webhook(validate_signature=False)(view)
    response = nonvalidating(request)

    assert (
        response == sentinel.response
    ), "Result should be response from the underlying view."
    assert view.mock_calls == [call(request)], "Underlying view should be called."
    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 0
    ), "No part should be saved."


@pytest.mark.django_db
def test_decorator_partial__bad_sig(rf, partial_message):
    partial_message["sig"] = "not-valid"
    request = rf.post(
        "/sms/incoming",
        content_type="application/json",
        data=json.dumps(partial_message),
    )

    view = MagicMock(return_value=sentinel.response)

    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 0
    ), "There should be no parts stored before the test."

    validating = d.sms_webhook(validate_signature=True)(view)
    response = validating(request)

    assert view.mock_calls == [], "Wrapped view should not be called."
    assert (
        response.status_code == 403
    ), "Decorator should return 403, permission denied."
    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 0
    ), "No part should be saved."

    nonvalidating = d.sms_webhook(validate_signature=False)(view)
    response = nonvalidating(request)

    assert (
        response.status_code == 200
    ), "OK response should be returned by the decorator."
    assert view.mock_calls == [], "Wrapped view should not be called."
    assert (
        len(models.SMSMessagePart.objects.filter(concat_ref="78")) == 1
    ), "Part should be saved."


@pytest.mark.django_db
def test_decorator_multipart(rf):
    parts = ["This", " is", " a ", "multipart", " message"]

    view = MagicMock(return_value=sentinel.response)
    webhook = d.sms_webhook(validate_signature=False)(view)
    
    requests = [
        rf.post(
            "/sms/incoming",
            content_type="application/json",
            data=json.dumps({
                "concat": "true",
                "concat-part": f"{index + 1}",
                "concat-ref": "78",
                "concat-total": f"{len(parts)}",
                "keyword": "LOREM",
                "message-timestamp": "2018-04-24 14:05:19",
                "messageId": f"0B000000D0EBB58{index}",
                "msisdn": "447700900419",
                "text": part,
                "timestamp": "1524578719",
                "to": "447700900996",
                "type": "unicode",
            }),
        )
        for index, part in enumerate(parts)
    ]
    shuffle(requests)

    for request in requests[:-1]:
        response = webhook(request)
        assert response.status_code == 200

    response = webhook(requests[-1])
    assert response is sentinel.response

    assert len(view.mock_calls) == 1
    name, args, kwargs = view.mock_calls[0]
    assert args[0].sms.text == 'This is a multipart message'