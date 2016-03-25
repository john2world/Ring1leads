from django.apps import AppConfig
from django.db.models.signals import post_save

from accounts.models import CustomUser


default_app_config = 'notifications.NotificationsConfig'


class NotificationsConfig(AppConfig):
    name = 'notifications'
    verbose_name = 'Notifications'

    def ready(self):
        post_save.connect(self.notification_created,
                          sender=self.get_model('Notification'))

    @staticmethod
    def notification_created(instance, created, raw, **kwargs):
        if not raw and created:
            if instance.sharedwith == '::1':
                instance.emit('notification')
            else:
                user_ids = instance.sharedwith.split(',')
                users = CustomUser.objects.filter(pk__in=user_ids)

                for user in users:
                    instance.emit('notification', user=user)
