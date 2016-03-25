from django.db import models
from django.conf import settings
from django.forms import model_to_dict
from django.utils import timezone

from jsonfield import JSONField
from datetime import timedelta
from events import emit_event


class EventManager(models.Manager):
    def fetch(self, event_type, user):
        """ Fetch events of a determined type for this user
        """
        # get the list of events already consumed by this user
        consumed_events = user.consumed_events.values_list('event', flat=True)

        # get a list of all events for this user and global events
        events = self.filter(
            models.Q(user=user) | models.Q(user__isnull=True),
            event_type=event_type
        ).exclude(pk__in=consumed_events)

        # generate a list containing all event data
        return [
            {
                'event_id': e.pk,
                'event_note': e.event_note,
                'event_data': e.event_data,
            }
            for e in events
        ]

    def mark_consumed(self, user, event_ids):
        """ Marked events as consumed, so they stop showing
        """
        events = Event.objects.filter(pk__in=event_ids)

        # mark these events as consumed
        EventConsumed.objects.bulk_create([
            EventConsumed(user=user, event=e)
            for e in events
        ])

        # remove if all consumed
        for event in events:
            event.delete_if_consumed_or_expired()

    def delete_expired(self):
        """ Delete expired events
        """
        qs = self.annotate(
            expires=models.ExpressionWrapper(
                models.F('date_created') + models.F('event_expiration'),
                output_field=models.DateTimeField())
        ).filter(
            expires__lt=timezone.now()
        )

        qs.delete()


class Event(models.Model):
    """ Events must be removed as soon as they are consumed

        When ``user`` is ``None`` the event will be delivered to all users.
    """
    uid = models.CharField(max_length=64, blank=True, null=True)

    # TODO: should we make a ManyToMany relation to User, "recipients"?
    # If not, we'd want to create a fabric func that would accept a list of recipients and
    # create an Event instance for each of them
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                             related_name='events', on_delete=models.CASCADE)

    event_type = models.CharField(max_length=30)
    event_data = JSONField()
    event_expiration = models.DurationField(default=timedelta(days=1))
    event_note = models.CharField(max_length=255, blank=True, null=True)

    date_created = models.DateTimeField(auto_now_add=True)

    objects = EventManager()

    class Meta:
        ordering = ('pk',)

    def delete_if_consumed_or_expired(self):
        """ Checks whether an event was consumed by all users, if so deletes it
        """
        if self.user is not None:
            if self.consumed.filter(user=self.user).exists():
                self.delete()
        else:
            Event.objects.delete_expired()


class EventConsumed(models.Model):
    """ List of users who consumed a determined event.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                              related_name='consumed')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='consumed_events')


class EventSourceMixin(object):
    """
    Provides event API for models.
    """
    def emit(self, event_type, note=None, uid=None, user=None):
        event_user = user or getattr(self, 'user', None)

        event_data = {
            'pk': self.pk,
            'data': self.to_dict() if hasattr(self, 'to_dict') else model_to_dict(self)
        }

        emit_event(event_type, event_data, user=event_user, note=note, uid=uid)
