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
