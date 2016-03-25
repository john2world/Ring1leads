from django.conf.urls import url
from api import views

urlpatterns = [
    url(r'^program/$', views.ProgramListView.as_view(), name='list-program'),
    url(r'^program/(?P<pk>[0-9]+)/$', views.ProgramRetrieveView.as_view(), name='retrieve-program'),
]
