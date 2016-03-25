from django.db import models
from django.contrib import admin
from django.contrib import messages
from django.forms import TextInput, Textarea
from django.utils.translation import ugettext as _
from simple_salesforce import SalesforceExpiredSession

from integrations.salesforce.models import OauthToken, SalesforceTable, SalesforceField, PicklistValue


class SalesforceFieldInlineAdmin(admin.TabularInline):
    model = SalesforceField
    # TODO: limit number of fields
    formfield_overrides = {
            models.CharField: {'widget': TextInput(attrs={'size': '10'})},
            models.TextField: {'widget': TextInput(attrs={'size': 10})}
    }


class OauthTokenAdmin(admin.ModelAdmin):
    pass


class SalesforceTableAdmin(admin.ModelAdmin):
    inlines = [SalesforceFieldInlineAdmin]


admin.site.register(OauthToken, OauthTokenAdmin)
admin.site.register(SalesforceTable, SalesforceTableAdmin)
