import json
from StringIO import StringIO

from cloud_info_provider import exceptions
from cloud_info_provider.formatters import base


class CMDB(base.BaseFormatter):
    def __init__(self):
        self.template_extension = 'cmdb.json'
        self.templates = ['compute', 'storage']

    def to_stdout(self, template):
        template_str = StringIO(template.replace("'", "\""))
        try:
            json_data = json.load(template_str)
        except ValueError as e:
            raise exceptions.CMDBFormatterException(e.message)
        print(json.dumps(json_data, indent=4, sort_keys=True))


class CMDBv2(base.BaseFormatter):
    def __init__(self):
        self.template_extension = 'cmdbv2.json'
        self.templates = ['compute']
