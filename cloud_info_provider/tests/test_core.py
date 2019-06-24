import os.path

from cloud_info_provider.tests import base


class FakeBDIIOpts(object):
    middleware = 'foo middleware'
    format = ''
    yaml_file = None
    template_dir = ''
    template_extension = ''


class FakeProvider(object):
    def __init__(self, *args, **kwargs):
        pass

    def method(self):
        pass


class BaseTest(base.TestCase):
    def setUp(self):
        super(BaseTest, self).setUp()

        self.providers = {
            'static': FakeProvider,
            'foo middleware': FakeProvider
        }

        self.opts = FakeBDIIOpts()
        cwd = os.path.dirname(__file__)
        template_dir = os.path.join(cwd, '..', '..', 'etc', 'templates')
        self.opts.template_dir = template_dir
