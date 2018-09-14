import cloud_info_provider.providers
from cloud_info_provider.tests import base


class BaseProviderTest(base.TestCase):
    def setUp(self):
        super(BaseProviderTest, self).setUp()
        self.provider = cloud_info_provider.providers.BaseProvider(None)

    def test_provider_get_site_info(self):
        self.assertEqual({}, self.provider.get_site_info())

    def test_provider_get_images(self):
        self.assertEqual({}, self.provider.get_images())

    def test_provider_get_templates(self):
        self.assertEqual({}, self.provider.get_templates())

    def test_provider_get_compute_endpoints(self):
        self.assertEqual({}, self.provider.get_compute_endpoints())

    def test_provider_get_storage_endpoints(self):
        self.assertEqual({}, self.provider.get_storage_endpoints())
