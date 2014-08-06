import os.path
import re


def get_variables_from_template(template):
    """Extract all variables from the template."""
    cwd = os.path.dirname(__file__)
    template = os.path.join(cwd, "..", "..", "etc", "templates", template)
    with open(template, "r") as f:
        content = f.read()

    regexp = re.compile('%\((.+?)\)s')
    l = set(regexp.findall(content))
    l.remove("suffix")
    l.remove("site_name")
    return list(l)
