import os


def env(*args, **kwargs):
    '''
    returns the first environment variable set
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
