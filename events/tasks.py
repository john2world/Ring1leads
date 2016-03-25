from time import sleep
from events.models import Event
from celery import shared_task
from django.contrib.auth import get_user_model


@shared_task
def mark_consumed_events(user_id, event_ids):
    # This delay is intended to all browser-tabs to be able to capture
    # all events before marking them as consumed
    sleep(5)

    User = get_user_model()
    Event.objects.mark_consumed(User.objects.get(pk=user_id), event_ids)
