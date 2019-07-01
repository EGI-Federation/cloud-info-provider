import json
from StringIO import StringIO

from cloud_info_provider.formatters import base


class CMDB(base.BaseFormatter):
    def __init__(self):
        self.template_extension = 'cmdb.json'
        self.templates = ['compute']

    def to_stdout(self, template):
        template_str = StringIO(template)
        json_data = json.load(template_str)


class CMDBv2(base.BaseFormatter):
    def __init__(self):
        self.template_extension = 'cmdbv2.json'
        self.templates = ['compute']
