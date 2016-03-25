from django.conf.urls import patterns, url

from integrations.salesforce.views import SalesforceOauthRedirectView


urlpatterns = patterns(
    '', url(r'^salesforce/$', SalesforceOauthRedirectView.as_view(), name='salesforce_oauth'),
)
