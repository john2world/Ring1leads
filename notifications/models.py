from django.db import models
from django.contrib import admin
from accounts.models import CustomUser
from events.models import EventSourceMixin


class Notification(EventSourceMixin, models.Model):
    """ A message delivered to one of our users to alert them of some change to
    a program, a change in their billing settings (inactive credit card),
    feature updates and release notifications, and anything else related to
    their use of the system. """

    created = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=256)
    text = models.TextField()
    sharedwith = models.CharField(max_length=1024, blank=True, default="::1")

    def as_json(self):
        return dict(
            id=self.id,
            subject=self.subject,
            text=self.text,
            created=str(self.created)
        )

    def is_shared(self, user):
        if (self.sharedwith == '::1') or (self.sharedwith is None):
            return True
        else:
            shared_users = self.sharedwith.split(',')
            if (str(user.id) in shared_users):
                return True
            else:
                return False

    def is_archived(self, user):
        user_notification = UserNotification.objects.filter(notification=self).filter(user=user).first()
        if user_notification:
            return user_notification.archived

        return False

    class Meta:
        ordering = ['-created']


class UserNotification(models.Model):
    user = models.ForeignKey(CustomUser, related_name="user_id")
    notification = models.ForeignKey(Notification, related_name="notification_id")
    archived = models.BooleanField(default=False)

    @classmethod
    def unread_notifications(cls, user):
        read_notifications = UserNotification.objects.filter(user=user)
        notifications = Notification.objects.all()
        unread_notifications = list()
        unreads = 0
        for notification in notifications:
            bfind = False
            for read_notification in read_notifications:
                if notification == read_notification.notification:
                    bfind = True
                    break

            if (bfind == False) and (notification.is_shared(user)):
                unread_notifications.append(notification.as_json())
                unreads += 1
        return {'unreads': unreads, 'notifications': unread_notifications}

admin.site.register(Notification)
admin.site.register(UserNotification)