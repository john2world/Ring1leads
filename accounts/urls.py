from django.conf.urls import url

from accounts.views import (
    CustomUserCreateView,
    CustomUserLoginView,
    LogoutView,
    UserConnectionsView
)

urlpatterns = [
    url(r'^register/', CustomUserCreateView.as_view(), name='register'),
    url(r'^login/', CustomUserLoginView.as_view(), name='login'),
    url(r'^connections/', UserConnectionsView.as_view(), name='connections'),
    url(r'^logout/', LogoutView.as_view(), name='logout'),
]
