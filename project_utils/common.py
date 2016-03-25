import json


def is_json(json_body):
    try:
        json.loads(json_body)
    except (TypeError, ValueError):
        return False
    return True


def import_to_python(import_str):
    mod_name, obj_name = import_str.rsplit('.', 1)
    mod = __import__(mod_name, {}, {}, [''])
    obj = getattr(mod, obj_name)
    return obj