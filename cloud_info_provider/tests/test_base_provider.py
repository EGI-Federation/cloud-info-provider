import cloud_info_provider.providers.base
import mock
from cloud_info_provider.tests import base


class BaseProviderTest(base.TestCase):
    def setUp(self):
        class Opts(object):
            debug = None
        super(BaseProviderTest, self).setUp()
        self.provider = cloud_info_provider.providers.base.BaseProvider(Opts())

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

    def test_provider_get_instances(self):
        self.assertEqual({}, self.provider.get_instances())

    def test_provider_get_compute_shares(self):
        self.assertEqual({}, self.provider.get_compute_shares())

    def test_provider_get_compute_quotas(self):
        self.assertEqual({}, self.provider.get_compute_quotas())

    def test_get_goc_info_no_svc(self):
        self.assertEqual({}, self.provider.get_goc_info('baz'))

    def test_get_goc_info(self):
        self.provider.goc_service_type = 'svc'
        with mock.patch(
            'cloud_info_provider.providers.gocdb.find_in_gocdb'
        ) as m_goc_find:
            m_goc_find.return_value = {'foo': 'bar'}
            self.provider.get_goc_info('baz')
            info = self.provider.get_goc_info('baz')
            self.assertEqual({'baz': {'foo': 'bar'}}, self.provider._goc_info)
            self.assertEqual({'foo': 'bar'}, info)
            self.assertEqual('baz', self.provider._last_goc_url)
            info = self.provider.get_goc_info()
            m_goc_find.assert_called_once_with(
                'baz', 'svc', False)
            self.assertEqual({'foo': 'bar'}, info)
