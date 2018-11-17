# DJ-Nexmo

[![PyPI version](https://badge.fury.io/py/dj-nexmo.svg)](https://badge.fury.io/py/dj-nexmo)
[![Build Status](https://api.travis-ci.org/Nexmo/dj-nexmo.svg?branch=master)](https://travis-ci.org/Nexmo/dj-nexmo)
[![Coverage Status](https://coveralls.io/repos/github/Nexmo/dj-nexmo/badge.svg?branch=master)](https://coveralls.io/github/Nexmo/dj-nexmo?branch=master)

The [Nexmo API] is _awesome_ - but there are some problems that developers using Nexmo need to solve again and again.
This Django app provides Django-specific functionality on top of the [Nexmo Client Library for Python]! Currently it contains:

* A decorator for validating and re-combining SMS message parts.
* Template filters for rendering phone numbers in international and national formats.


## How To Install It

Currently, `dj-nexmo` **only** supports Python 3.4+, and Django 2.0+. We _may_ backport to Django 1.x, but we have no intention of backporting to Python 2.

First, `pip install dj-nexmo`

Add `"djnexmo"` to `INSTALLED_APPS` in your settings.

Run `python manage.py migrate djnexmo` to create the necessary models.


## Configuration

### `NEXMO_API_KEY`

This optional setting should be set to your Nexmo API Key, which you can obtain from the dashboard.

### `NEXMO_API_SECRET`

This optional setting should be set to your Nexmo API Secret, which you can obtain from the dashboard.

### `NEXMO_SIGNATURE_SECRET`

This optional setting should be set to your Nexmo Signature Secret, which you can obtain by contacting Nexmo support.
You will need this setting if you wish to validate incoming SMS.

### `NEXMO_SIGNATURE_METHOD`

This optional setting should be set to your Nexmo signing method, which you should obtain from Nexmo support when you
obtain your Nexmo signature secret.

### `NEXMO_APPLICATION_ID`

This optional setting should be set to the ID of a Nexmo Voice application.

### `NEXMO_PRIVATE_KEY`

This optional setting should be set to your Nexmo Voice application's private key, or a path to a file containing
your private key.


## Using the Nexmo Client

`dj-nexmo` configures a Nexmo `Client` object from the settings above. You can
use it by importing it from the `djnexmo` package:

```python
from djnexmo import client

client.send_sms({
    'to': '447700900301',
    'from': '447700900414',
    'text': 'Hello from DJ Nexmo!'
})
```


## Incoming SMS

`dj-nexmo` provides a view decorator which will ensure your webhook view is only called once all the parts of an SMS are
available.

```python
# This will automatically check the signature of the incoming request.
# The view will only be called once all parts of the SMS have arrived.
@sms_webhook
def sms_registration(request):
    # Your parsed & merged SMS message will be available as `request.sms`:
    sms = request.sms

    # Don't do any long processing here - you should return a 200 response as soon as possible.
    ...

    return HttpResponse("OK")
```


## Formatting Phone Numbers

`dj-nexmo` adds a couple of template filters for formatting phone numbers, wrapping the awesome
[phonenumbers] library.

```html
{% load phonenumbers %}

International: {{ "447700900486" | international }} => +44 7700 900486
Local Format: {{ "447700900486" | national }}       => 07700 900486
```

## Coming Soon:

* A management command for clearing the database of old message parts where not all parts were received.
* A decorator to validate other webhooks from the Nexmo API.


## License

This code is open-source, released under the Apache License. This means it is free to use
for commercial or non-commercial purposes, and you can make any changes you would like or need.


## Contribute!

We :heart: contributions -- if you'd like help contributing to this project, please contact us!
If you want to do anything particularly significant, we recommend you open up an issue
to discuss it with us first. If there's something you'd like to see, please open an issue for that
too! If you find a bug, please create an issue - any help you can give providing a small code sample that
demonstrates the problem you've seen would be very useful and means we should be able to solve
your problem sooner!


[Nexmo API]: https://developer.nexmo.com/
[phonenumbers]: https://github.com/google/phonenumbers
[Nexmo Client Library for Python]: https://github.com/nexmo/nexmo-python
