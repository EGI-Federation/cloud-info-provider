import contextlib  # noqa
import itertools
import os.path
import re

import six

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


if six.PY2:
    nested = contextlib.nested
else:
    @contextlib.contextmanager
    def nested(*contexts):
        with contextlib.ExitStack() as stack:
            yield [stack.enter_context(c) for c in contexts]
