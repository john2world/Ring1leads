from django.conf.urls import url

from notifications.views import NotificationsListView, unread_notifications, read_notification, archive_notification

urlpatterns = [
    url(r'^$', NotificationsListView.as_view(), name='notifications'),
    url(r'^notification_status/$', read_notification, name='notification_status'),
    url(r'^unread_notifications/$', unread_notifications, name='unread_notifications'),
    url(r'^archive_notification/$', archive_notification, name='archive_notification')
]
