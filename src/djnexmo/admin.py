from django.contrib import admin

from .models import SMSMessagePart

@admin.register(SMSMessagePart)
class SMSMessagePartAdmin(admin.ModelAdmin):
    list_display = ('msisdn', 'to', '__str__',)
    list_display_links = ('__str__',)
    search_fields = ('msisdn',)
    view_on_site = False