import json
import os


def env(*args, **kwargs):
    """Returns the first environment variable set.

    if none are non-empty, defaults to '' or keyword arg default
    """
    for arg in args:
        value = os.environ.get(arg, None)
        if value:
            return value
    return kwargs.get("default", "")


def pythonize_network_info(network_info):
    """Pythonize Ruby dict-like network_info string. Do nothing otherwise."""
    try:
        return json.loads(network_info.replace(':"', '"').replace("=>", ":"))
    except AttributeError:
        return network_info
