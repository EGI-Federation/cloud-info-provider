import unittest

import cloud_bdii.providers


class BaseProviderTest(unittest.TestCase):
    def setUp(self):
        self.provider = cloud_bdii.providers.BaseProvider(None)

    def test_provider_get_site_info(self):
        self.assertEqual({}, self.provider.get_site_info())

    def test_provider_get_images(self):
        self.assertEqual([], self.provider.get_images())

    def test_provider_get_templates(self):
        self.assertEqual([], self.provider.get_templates())

    def test_provider_get_compute_endpoints(self):
        self.assertEqual([], self.provider.get_compute_endpoints())

    def test_provider_get_storage_endpoints(self):
        self.assertEqual([], self.provider.get_storage_endpoints())
