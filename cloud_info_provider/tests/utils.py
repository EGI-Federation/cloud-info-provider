import contextlib  # noqa

from cloud_info_provider import glue


def compare_glue(obj, glue_obj):
    for f in ("associations", "other_info"):
        if f not in obj:
            obj[f] = {}
    for field in glue_obj.__class__.model_fields:
        if field in ("creation_time", "validity"):
            continue
        v = getattr(glue_obj, field)
        if v is None:
            continue
        if isinstance(v, glue.BoolEnum):
            v = v.value
        if v != obj.get(field, None):
            print(f"Not matching {field} in object {obj} and {glue_obj.model_dump()}")
            return False
    # any extra fields??
    return True


@contextlib.contextmanager
def nested(*contexts):
    with contextlib.ExitStack() as stack:
        yield [stack.enter_context(c) for c in contexts]
