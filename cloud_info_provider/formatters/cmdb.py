from cloud_info_provider.formatters import base


class CMDB(base.BaseFormatter):
    def __init__(self):
        self.template_extension = 'cmdb.json'
        self.templates = ['compute']


class CMDBv2(base.BaseFormatter):
    def __init__(self):
        self.template_extension = 'cmdbv2.json'
        self.templates = ['compute']
