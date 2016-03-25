from django.conf import settings
from django.core.mail import send_mail


class BaseNotification(object):
    STATUS_INFO = 'INFO'
    STATUS_WARNING = 'WARNING'
    STATUS_URGENT = 'URGENT'

    # Notification type can be used to highlight notification type in email subject, push notification etc.
    # So receiver can understand what part of the system sends the notification
    NOTIFICATION_TYPE = "Common"

    def __init__(self, message, status=None):
        self.message = message
        self.status = status if status else self.STATUS_INFO


class KickboxAPIInsuffinetBalanceNotification(BaseNotification):
    NOTIFICATION_TYPE = 'Kickbox'

    def __init__(self):
        super(KickboxAPIInsuffinetBalanceNotification, self).__init__(
            status=self.STATUS_URGENT,
            message="""
URGENT!
Kickbox API returned "Insufficient balance" error!
Please check Kickbox account balance: https://kickbox.io/app/billing
"""
        )


class BaseNotificationSender(object):
    def __init__(self, notification):
        self.notification = notification

    def notify(self):
        raise NotImplementedError()


class EmailAdminsNotificationSender(BaseNotificationSender):
    def notify(self):
        subject = "Data Quality Tool: %s Notification Received. Status: %s" % (
            self.notification.NOTIFICATION_TYPE,
            self.notification.status.upper(),
        )
        recipient_list = [admin[1] for admin in settings.ADMINS]
        send_mail(subject, self.notification.message, settings.SERVER_EMAIL, recipient_list=recipient_list)
