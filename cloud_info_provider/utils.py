import json
import os
import string

import six


if six.PY2:
    maketrans = string.maketrans
    translate = string.translate
else:
    maketrans = str.maketrans
    translate = str.translate


def env(*args, **kwargs):
    '''Returns the first environment variable set.

    if none are non-empty, defaults to '' or keyword arg default
    '''
    for arg in args:
        value = os.environ.get(arg, None)
        if value:
            return value
    return kwargs.get('default', '')


def get_tag_value(xml, tag):
    if xml.getElementsByTagName(tag):
        return xml.getElementsByTagName(tag)[0].firstChild.nodeValue
    else:
        return None


def pythonize_network_info(network_info):
    '''Pythonize Ruby dict-like network_info string. Do nothing otherwise.'''
    try:
        return json.loads(network_info.replace(':"', '"').replace("=>", ":"))
    except AttributeError:
        return network_info


def get_defined_values(d, ignore_empty_string=False):
    '''Return a dict with only the items whose value is not None'''
    if ignore_empty_string:
        return {k: v for (k, v) in d.items() if v not in [None, '']}
    return {k: v for (k, v) in d.items() if v is not None}
