import itertools
import os.path
import re


IGNORED_FIELDS = ["suffix", "site_name"]


def get_variables_from_template(template, ignored_fields=[]):
    """Extract all variables from the template."""
    cwd = os.path.dirname(__file__)
    template = os.path.join(cwd, "..", "..", "etc", "templates", template)
    with open(template, "r") as f:
        content = f.read()

    regexp = re.compile('%\((.+?)\)s')
    l = set(regexp.findall(content))
    for k in itertools.chain(IGNORED_FIELDS, ignored_fields):
        if k in l:
            l.remove(k)
    return list(l)
