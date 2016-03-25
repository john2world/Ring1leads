from django.conf.urls import url
from integrations.salesforce import views


urlpatterns = [
    url(r'^delete/$', views.DeleteSalesforceConnectionView.as_view(), name='delete_salesforce'),
]
