import contextlib  # noqa
import itertools
import os.path
import re

import six

IGNORED_FIELDS = ["suffix", "site_name"]


def get_variables_from_template(template, ignored_fields=[]):
    """Extract all variables from the template."""
    cwd = os.path.dirname(__file__)
    template = os.path.join(cwd, "..", "formatters", "templates", template)
    with open(template, "r") as f:
        content = f.read()

    # Look for variables names like
    # ${static_compute_info['compute_service_production_level']}
    regexp = re.compile(r"\${[^\[]+\[\'(.+?)\'\]}")
    matches = set(regexp.findall(content))
    for k in itertools.chain(IGNORED_FIELDS, ignored_fields):
        if k in matches:
            matches.remove(k)
    return list(matches)


if six.PY2:
    # pylint: disable=no-member
    nested = contextlib.nested
else:

    @contextlib.contextmanager
    def nested(*contexts):
        with contextlib.ExitStack() as stack:
            yield [stack.enter_context(c) for c in contexts]
