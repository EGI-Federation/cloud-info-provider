class BaseProvider(object):
    def __init__(self, opts):
        self.opts = opts

    def get_site_info(self, **kwargs):
        return {}

    def get_images(self, **kwargs):
        return {}

    def get_templates(self, **kwargs):
        return {}

    def get_compute_shares(self, **kwargs):
        return {}

    def get_compute_endpoints(self, **kwargs):
        return {}

    def get_storage_endpoints(self, **kwargs):
        return {}

    @staticmethod
    def populate_parser(parser):
        '''Populate the argparser 'parser' with the needed options.'''
