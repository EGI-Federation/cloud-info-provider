from cloud_info_provider.formatters import base


class GLUE(base.BaseFormatter):
    def __init__(self):
        self.template_extension = 'ldif'
        self.templates = [
            'headers',
            'clouddomain',
            'compute',
            'storage',
        ]
