from cloud_info_provider import core
from cloud_info_provider.formatters import base


class CMDB(base.BaseFormatter):
    def __init__(self):
        self.template_extension = 'cmdb.json'
        self.templates = ['compute']
        self.cls = [core.ComputeFetcher]
