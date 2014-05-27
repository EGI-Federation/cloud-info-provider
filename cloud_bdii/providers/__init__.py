class BaseProvider(object):
    def __init__(self, opts):
        self.opts = opts

    def get_site_info(self):
        return {}

    def get_images(self):
        return []

    def get_templates(self):
        return []

    def get_compute_endpoints(self):
        return []

    def get_storage_endpoints(self):
        return []

    @staticmethod
    def populate_parser(parser):
        '''Populate the argparser 'parser' with the needed options.'''
