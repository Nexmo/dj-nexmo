from django import template
from django.template.defaultfilters import stringfilter

import phonenumbers

register = template.Library()


@register.filter(name="international")
@stringfilter
def international(value):
    value = value.strip()
    if not value.startswith("+"):
        value = "+" + value
    phonenumbers.parse(value)
    return phonenumbers.format_number(
        phonenumbers.parse(value), phonenumbers.PhoneNumberFormat.INTERNATIONAL
    )


@register.filter(name="national")
@stringfilter
def national(value):
    value = value.strip()
    if not value.startswith("+"):
        value = "+" + value
    phonenumbers.parse(value)
    return phonenumbers.format_number(
        phonenumbers.parse(value), phonenumbers.PhoneNumberFormat.NATIONAL
    )
