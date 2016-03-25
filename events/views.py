from django.http import JsonResponse

from events.models import Event
from events.tasks import mark_consumed_events


def events(request):
    data = {}

    if request.user.is_authenticated():
        # mark consumed events
        event_ids = request.GET.get('consumed_events', '').split(',')
        event_ids = filter(lambda i: i.isdigit(), event_ids)

        if event_ids:
            mark_consumed_events.delay(request.user.pk, event_ids)

        # consume new events
        consume_events = request.GET.get('consume_events', '').split(',')
        for event in consume_events:
            result = Event.objects.fetch(event, request.user)
            if result:
                data[event] = result

    return JsonResponse(data)
