from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.decorators import login_required

from events.views import events

from integrations.salesforce.settings import (
    SALESFORCE_PROD_AUTH_URL,
    SALESFORCE_SANDBOX_AUTH_URL
    )


urlpatterns = [
    url(r'^', include('program_manager.urls'), name='programs'),

    url(r'^events\.json$', events),

    url(r'^analytics/', include('qscore.urls'), name='analytics'),
    url(r'^accounts/', include('accounts.urls', namespace='accounts')),
    url(r'^notifications/', include('notifications.urls'),
        name='notifications'),
    url(r'^payments/', include('payments.urls'), name='payments'),
    url(r'^reports/', include('reports.urls'), name='reports'),
    url(r'^api/', include('api.urls'), name='api'),
    url(r'^field_mapper/', include('field_mapper.urls',
        namespace='field_mapper')),
    url(r'^salesforce/', include('integrations.salesforce.urls', namespace='salesforce')),
    url(r'^welcome/$',
        login_required(TemplateView.as_view(template_name='welcome.html')),
        name='welcome'),

    # Incoming Oauth Redirects
    url(r'^oauth/', include('integrations.oauth'), name='oauth'),

    # Outgoing Oauth Redirects
    url(
        r'^salesforce_auth/$',
        RedirectView.as_view(url=SALESFORCE_PROD_AUTH_URL, permanent=False),
        name='salesforce_auth_request'
        ),
    url(
        r'^salesforce_sandbox/$',
        RedirectView.as_view(url=SALESFORCE_SANDBOX_AUTH_URL, permanent=False),
        name='salesforce_sandbox_auth_request'
        ),


    url(r'^admin/', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^djangojs/', include('djangojs.urls')),
]
