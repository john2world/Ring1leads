from django.conf.urls import url

from field_mapper.views import MapFieldsView


urlpatterns = [
    url(r'^map_fields/(?P<pk>[^/]+)/', MapFieldsView.as_view(),
        name='map_fields'),
]
