def emit_event(event_type, event_data, user=None, note=None, uid=None):
    from events.models import Event

    defaults = {
        'user': user,
        'event_note': note,
        'event_type': event_type,
        'event_data': event_data,
    }

    if uid is None:
        Event.objects.create(**defaults)
    else:
        Event.objects.update_or_create(uid=uid, defaults=defaults)
