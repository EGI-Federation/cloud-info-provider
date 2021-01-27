import json
from io import StringIO

from cloud_info_provider import exceptions
from cloud_info_provider.formatters import base


class CMDB(base.BaseFormatter):
    def __init__(self):
        self.template_extension = "cmdb.json.tmpl"
        self.templates = ["compute", "storage"]
