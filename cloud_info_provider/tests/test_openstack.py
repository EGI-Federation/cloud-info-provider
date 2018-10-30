import argparse

import mock

from cloud_info_provider.providers import ooi as ooi_provider
from cloud_info_provider.providers import openstack as os_provider
from cloud_info_provider.tests import base
from cloud_info_provider.tests import data
from cloud_info_provider.tests import utils as utils

from six.moves.urllib.parse import urljoin

FAKES = data.OS_FAKES


class OpenStackProviderOptionsTest(base.TestCase):
    def test_populate_parser(self):
        parser = argparse.ArgumentParser(conflict_handler='resolve')
        provider = os_provider.OpenStackProvider
        provider.populate_parser(parser)

        opts = parser.parse_args(['--os-username', 'foo',
                                  '--os-password', 'bar',
                                  '--os-auth-url', 'http://example.org:5000',
                                  '--os-cacert', 'foobar',
                                  '--insecure',
                                  '--all-images',
                                  '--select-flavors', 'public'])

        self.assertEqual(opts.os_username, 'foo')
        self.assertEqual(opts.os_password, 'bar')
        self.assertEqual(opts.os_auth_url, 'http://example.org:5000')
        self.assertEqual(opts.os_cacert, 'foobar')
        self.assertEqual(opts.insecure, True)
        self.assertEqual(opts.all_images, True)
        self.assertEqual(opts.select_flavors, 'public')


class OpenStackProviderTest(base.TestCase):

    # Do not limit diff output on failures
    maxDiff = None

    def setUp(self):
        super(OpenStackProviderTest, self).setUp()

        class FakeProvider(os_provider.OpenStackProvider):
            def __init__(self, opts):
                self.nova = mock.Mock()
                self.glance = mock.Mock()
                self.glance.http_client.get_endpoint.return_value = (
                    "http://glance.example.org:9292/v2"
                )
                self.session = mock.Mock()
                self.session.get_project_id.return_value = 'TEST_PROJECT_ID'
                self.auth_plugin = mock.MagicMock()
                self.auth_plugin.auth_url = 'http://foo.example.org:5000/v2'
                self.static = mock.Mock()
                self.keystone_cert_issuer = "foo"
                self.keystone_trusted_cas = []
                self.insecure = False
                self.os_cacert = '/etc/ssl/cas'
                self.os_project_id = None
                self.select_flavors = 'all'
                self._rescope_project = mock.Mock()
                self.all_images = False
                self.opts = mock.Mock()
                self.opts.extra_specs_infiniband_key = 'infiniband'
                self.opts.extra_specs_infiniband_value = 'true'

        self.provider = FakeProvider(None)

    def assert_resources(self, expected, observed, template=None,
                         ignored_fields=[]):
        if template:
            fields = utils.get_variables_from_template(template,
                                                       ignored_fields)
        else:
            fields = []
        for k, v in observed.items():
            self.assertDictEqual(expected[k], v)
            for f in fields:
                self.assertIn(f, v)

    def test_get_templates_with_defaults(self):
        expected_templates = {}
        url = 'http://schemas.openstack.org/template/resource'
        for f in FAKES.flavors:
            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': '%s#%s' % (url, f.id),
                'template_native_id': "%s" % f.id,
                'template_platform': 'amd64',
                'template_network': 'private',
                'template_disk': f.disk,
                'template_ephemeral': f.ephemeral,
                'template_infiniband': False,
            }

        with utils.nested(
                mock.patch.object(self.provider.static,
                                  'get_template_defaults'),
                mock.patch.object(self.provider.nova.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {}
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            self.assertTrue(m_get_template_defaults.called)

        self.assert_resources(expected_templates,
                              templates,
                              template="compute.ldif",
                              ignored_fields=[
                                  "compute_api_type",
                                  "compute_api_version",
                                  "compute_api_endpoint_technology",
                                  "compute_capabilities",
                                  "compute_endpoint_url",
                                  "compute_hypervisor",
                                  "compute_hypervisor_version",
                                  "compute_middleware",
                                  "compute_middleware_developer",
                                  "compute_middleware_version",
                                  "compute_production_level",
                                  "compute_api_authn_method",
                                  "compute_service_name",
                                  "compute_service_production_level",
                                  "compute_total_cores",
                                  "compute_total_ram",
                                  "image_id",
                                  "image_name",
                                  "image_os_family",
                                  "image_os_name",
                                  "image_os_version",
                                  "image_platform",
                                  "image_version",
                                  "image_description",
                                  "image_marketplace_id"
                              ])

    def test_get_templates_with_defaults_from_static(self):
        expected_templates = {}
        url = 'http://schemas.openstack.org/template/resource'
        for f in FAKES.flavors:
            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': '%s#%s' % (url, f.id),
                'template_native_id': "%s" % f.id,
                'template_platform': 'i686',
                'template_network': 'private',
                'template_disk': f.disk,
                'template_ephemeral': f.ephemeral,
                'template_infiniband': False,
            }

        with utils.nested(
                mock.patch.object(self.provider.static,
                                  'get_template_defaults'),
                mock.patch.object(self.provider.nova.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {
                'template_platform': 'i686'
            }
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            self.assertTrue(m_get_template_defaults.called)

        self.assert_resources(expected_templates,
                              templates,
                              template="compute.ldif",
                              ignored_fields=[
                                  "compute_api_type",
                                  "compute_api_version",
                                  "compute_api_endpoint_technology",
                                  "compute_capabilities",
                                  "compute_endpoint_url",
                                  "compute_hypervisor",
                                  "compute_hypervisor_version",
                                  "compute_middleware",
                                  "compute_middleware_developer",
                                  "compute_middleware_version",
                                  "compute_production_level",
                                  "compute_api_authn_method",
                                  "compute_service_name",
                                  "compute_service_production_level",
                                  "compute_total_cores",
                                  "compute_total_ram",
                                  "image_id",
                                  "image_name",
                                  "image_version",
                                  "image_description",
                                  "image_marketplace_id"
                              ])

    def test_get_all_templates(self):
        """Tests that all templates/flavors are returned"""
        expected_templates = {}
        url = 'http://schemas.openstack.org/template/resource'
        for f in FAKES.flavors:
            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': '%s#%s' % (url, f.id),
                'template_native_id': "%s" % f.id,
                'template_platform': 'i686',
                'template_network': 'private',
                'template_disk': f.disk,
                'template_ephemeral': f.ephemeral,
                'template_infiniband': False,
            }

        self.provider.select_flavors = 'all'
        with utils.nested(
                mock.patch.object(self.provider.static,
                                  'get_template_defaults'),
                mock.patch.object(self.provider.nova.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {
                'template_platform': 'i686'
            }
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            self.assertTrue(m_get_template_defaults.called)

        # Extract required fields from compute.ldif template excluding fields
        # extracted that are not related to the flavors
        self.assert_resources(expected_templates,
                              templates,
                              template="compute.ldif",
                              ignored_fields=[
                                  "compute_service_name",
                                  "compute_hypervisor",
                                  "compute_api_authn_method",
                                  "compute_total_ram",
                                  "image_marketplace_id",
                                  "compute_middleware_developer",
                                  "compute_production_level",
                                  "compute_production_level",
                                  "compute_api_type",
                                  "compute_api_endpoint_technology",
                                  "compute_api_version",
                                  "compute_endpoint_url",
                                  "compute_service_production_level",
                                  "compute_capabilities",
                                  "compute_total_cores",
                                  "compute_middleware",
                                  "compute_hypervisor_version",
                                  "compute_middleware_version",
                                  "image_description",
                                  "image_id",
                                  "image_name",
                                  "image_version",
                              ])

    def test_get_public_templates(self):
        """Tests that only public templates/flavors are returned"""
        expected_templates = {}
        url = 'http://schemas.openstack.org/template/resource'
        for f in FAKES.flavors:
            if not f.is_public:
                continue

            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': '%s#%s' % (url, f.id),
                'template_native_id': "%s" % f.id,
                'template_platform': 'i686',
                'template_network': 'private',
                'template_disk': f.disk,
                'template_ephemeral': f.ephemeral,
                'template_infiniband': False,
            }

        self.provider.select_flavors = 'public'
        with utils.nested(
                mock.patch.object(self.provider.static,
                                  'get_template_defaults'),
                mock.patch.object(self.provider.nova.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {
                'template_platform': 'i686'
            }
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            self.assertTrue(m_get_template_defaults.called)

        # Extract required fields from compute.ldif template excluding fields
        # extracted that are not related to the flavors
        self.assert_resources(expected_templates,
                              templates,
                              template="compute.ldif",
                              ignored_fields=[
                                  "compute_service_name",
                                  "compute_hypervisor",
                                  "compute_api_authn_method",
                                  "compute_total_ram",
                                  "image_marketplace_id",
                                  "compute_middleware_developer",
                                  "compute_production_level",
                                  "compute_production_level",
                                  "compute_api_type",
                                  "compute_api_endpoint_technology",
                                  "compute_api_version",
                                  "compute_endpoint_url",
                                  "compute_service_production_level",
                                  "compute_capabilities",
                                  "compute_total_cores",
                                  "compute_middleware",
                                  "compute_hypervisor_version",
                                  "compute_middleware_version",
                                  "image_description",
                                  "image_id",
                                  "image_name",
                                  "image_version"
                              ])

    def test_get_private_templates(self):
        """Tests that only private templates/flavors are returned"""
        expected_templates = {}
        url = 'http://schemas.openstack.org/template/resource'
        for f in FAKES.flavors:
            if f.is_public:
                continue

            expected_templates[f.id] = {
                'template_memory': f.ram,
                'template_cpu': f.vcpus,
                'template_id': '%s#%s' % (url, f.id),
                'template_native_id': "%s" % f.id,
                'template_platform': 'i686',
                'template_network': 'private',
                'template_disk': f.disk,
                'template_ephemeral': f.ephemeral,
                'template_infiniband': False,
            }

        self.provider.select_flavors = 'private'
        with utils.nested(
                mock.patch.object(self.provider.static,
                                  'get_template_defaults'),
                mock.patch.object(self.provider.nova.flavors, 'list'),
        ) as (m_get_template_defaults, m_flavors_list):
            m_get_template_defaults.return_value = {
                'template_platform': 'i686'
            }
            m_flavors_list.return_value = FAKES.flavors
            templates = self.provider.get_templates()
            self.assertTrue(m_get_template_defaults.called)

        # Extract required fields from compute.ldif template excluding fields
        # extracted that are not related to the flavors
        self.assert_resources(expected_templates,
                              templates,
                              template="compute.ldif",
                              ignored_fields=[
                                  "compute_service_name",
                                  "compute_hypervisor",
                                  "compute_api_authn_method",
                                  "compute_total_ram",
                                  "image_marketplace_id",
                                  "compute_middleware_developer",
                                  "compute_production_level",
                                  "compute_production_level",
                                  "compute_api_type",
                                  "compute_api_endpoint_technology",
                                  "compute_api_version",
                                  "compute_endpoint_url",
                                  "compute_service_production_level",
                                  "compute_capabilities",
                                  "compute_total_cores",
                                  "compute_middleware",
                                  "compute_hypervisor_version",
                                  "compute_middleware_version",
                                  "image_description",
                                  "image_id",
                                  "image_name",
                                  "image_os_family",
                                  "image_os_name",
                                  "image_os_version",
                                  "image_platform",
                                  "image_version"
                              ])

    def test_get_images(self):
        # XXX move this to a custom class?
        # XXX add docker information
        expected_images = {
            'bar id': {
                'name': 'barimage',
                'id': 'bar id',
                'metadata': {},
                'file': 'v2/bar id/file',
                'image_description': None,
                'image_name': 'barimage',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': None,
                'image_marketplace_id': "%s" % urljoin(self.provider.glance
                                                       .http_client
                                                       .get_endpoint(),
                                                       'v2/bar id/file'),
                'image_id': 'http://schemas.openstack.org/template/os#bar_id',
                'image_native_id': 'bar id',
                'image_accel_type': None,
                'image_access_info': 'none',
                'image_minimal_cpu': None,
                'image_minimal_ram': None,
                'image_minimal_accel': None,
                'image_recommended_cpu': None,
                'image_recommended_ram': None,
                'image_recommended_accel': None,
                'image_size': None,
                'image_software': [],
                'image_traffic_in': [],
                'image_traffic_out': [],
                'image_context_format': None,
            },
            'foo.id': {
                'name': 'fooimage',
                'id': 'foo.id',
                'metadata': {},
                'marketplace': 'http://example.org/',
                'file': 'v2/foo.id/file',
                'image_description': None,
                'image_name': 'fooimage',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': None,
                'image_marketplace_id': 'http://example.org/',
                'image_id': 'http://schemas.openstack.org/template/os#foo.id',
                'image_native_id': 'foo.id',
                'image_accel_type': None,
                'image_access_info': 'none',
                'image_minimal_cpu': None,
                'image_minimal_ram': None,
                'image_minimal_accel': None,
                'image_recommended_cpu': None,
                'image_recommended_ram': None,
                'image_recommended_accel': None,
                'image_size': None,
                'image_software': [],
                'image_traffic_in': [],
                'image_traffic_out': [],
                'image_context_format': None,
            },
            'baz id': {
                'name': 'bazimage',
                'id': 'baz id',
                'file': 'v2/baz id/file',
                'image_description': None,
                'image_name': 'bazimage',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': None,
                'image_marketplace_id': "%s" % urljoin(self.provider.glance
                                                       .http_client
                                                       .get_endpoint(),
                                                       'v2/baz id/file'),
                'image_id': 'http://schemas.openstack.org/template/os#baz_id',
                'image_native_id': 'baz id',
                'docker_id': 'sha1:xxxxxxxxxxxxxxxxxxxxxxxxxx',
                'docker_tag': 'latest',
                'docker_name': 'test/image',
                'image_accel_type': None,
                'image_access_info': 'none',
                'image_minimal_cpu': None,
                'image_minimal_ram': None,
                'image_minimal_accel': None,
                'image_recommended_cpu': None,
                'image_recommended_ram': None,
                'image_recommended_accel': None,
                'image_size': None,
                'image_software': [],
                'image_traffic_in': [],
                'image_traffic_out': [],
                'image_context_format': None,
            }
        }

        with utils.nested(
                mock.patch.object(self.provider.static, 'get_image_defaults'),
                mock.patch.object(self.provider.glance.images, 'list'),
        ) as (m_get_image_defaults, m_images_list):
            m_get_image_defaults.return_value = {}
            m_images_list.return_value = FAKES.images

            images = self.provider.get_images()
            self.assertTrue(m_get_image_defaults.called)

        # Filter fields from the template that are not related to images
        self.assert_resources(expected_images,
                              images,
                              template="compute.ldif",
                              ignored_fields=["compute_service_name",
                                              "compute_api_type",
                                              "compute_api_version",
                                              ("compute_api_endpoint"
                                               "_technology"),
                                              "compute_capabilities",
                                              "compute_api_authn_method",
                                              "compute_total_ram",
                                              "compute_middleware",
                                              "compute_middleware_developer",
                                              "compute_middleware_version",
                                              "compute_endpoint_url",
                                              "compute_hypervisor",
                                              "compute_hypervisor_version",
                                              "compute_production_level",
                                              ("compute_service"
                                               "_production_level"),
                                              "compute_total_cores",
                                              "compute_total_ram",
                                              "template_platform",
                                              "template_cpu",
                                              "template_memory",
                                              "template_network",
                                              "template_disk",
                                              "template_ephemeral",
                                              "template_id",
                                              "template_infiniband"])

    def test_get_markeplace_images(self):
        expected_images = ['foo.id']

        self.provider.all_images = False
        with utils.nested(
                mock.patch.object(self.provider.static, 'get_image_defaults'),
                mock.patch.object(self.provider.glance.images, 'list'),
        ) as (m_get_image_defaults, m_images_list):
            m_get_image_defaults.return_value = {}
            m_images_list.return_value = FAKES.images

            images = self.provider.get_images()
            self.assertTrue(m_get_image_defaults.called)

        self.assertItemsEqual(images.keys(), expected_images)

    def test_get_endpoints_with_defaults_from_static(self):
        expected_endpoints = {
            'endpoints': {
                'http://foo.example.org:5000/v2': {
                    'compute_api_type': 'OpenStack',
                    # As version is extracted from the URL default is not used
                    'compute_api_version': 'v2',
                    'compute_endpoint_id': '1b7f14c87d8c42ad962f4d3a5fd13a77',
                    'compute_nova_endpoint_url':
                        'https://cloud.example.org:8774/v1.1/ce2d',
                    'compute_nova_api_version': 'v1.1',
                    'compute_endpoint_url':
                        'http://foo.example.org:5000/v2'}
            },
            'compute_middleware_developer': 'OpenStack',
            'compute_middleware': 'OpenStack Nova',
            'compute_service_name': 'http://foo.example.org:5000/v2',
        }

        with mock.patch.object(
                self.provider.static, 'get_compute_endpoint_defaults'
        ) as m_get_endpoint_defaults:
            m_get_endpoint_defaults.return_value = {
                'compute_occi_api_version': '11.11',
                'compute_compute_api_version': '99.99',
            }
            r = mock.Mock()
            r.service_catalog = FAKES.catalog
            self.provider.auth_plugin.get_access.return_value = r
            endpoints = self.provider.get_compute_endpoints()
            self.assertTrue(m_get_endpoint_defaults.called)

        for k, v in expected_endpoints['endpoints'].items():
            self.assertDictContainsSubset(v, endpoints['endpoints'].get(k, {}))

    def test_get_endpoints_with_defaults(self):
        expected_endpoints = {
            'endpoints': {
                'http://foo.example.org:5000/v2': {
                    'compute_api_type': 'OpenStack',
                    'compute_api_version': 'v2',
                    'compute_nova_endpoint_url':
                        'https://cloud.example.org:8774/v1.1/ce2d',
                    'compute_nova_api_version': 'v1.1',
                    'compute_middleware': 'OpenStack Nova',
                    'compute_middleware_version': 'UNKNOWN',
                    'compute_middleware_developer': 'OpenStack Foundation',
                    'endpoint_issuer': self.provider.keystone_cert_issuer,
                    'endpoint_trusted_cas': [],
                    'compute_endpoint_id': '1b7f14c87d8c42ad962f4d3a5fd13a77',
                    'compute_endpoint_url':
                        'http://foo.example.org:5000/v2'}
            },
            'compute_service_name': 'http://foo.example.org:5000/v2',
        }

        with mock.patch.object(
                self.provider.static, 'get_compute_endpoint_defaults'
        ) as m_get_endpoint_defaults:
            m_get_endpoint_defaults.return_value = {}
            r = mock.Mock()
            r.service_catalog = FAKES.catalog
            self.provider.auth_plugin.get_access.return_value = r
            endpoints = self.provider.get_compute_endpoints()
            self.assertTrue(m_get_endpoint_defaults.called)

        self.assertDictEqual(expected_endpoints, endpoints)

    def test_occify_terms(self):
        self.assertEqual('m1.tiny', self.provider.adapt_id('m1.tiny'))
        self.assertEqual('m1 tiny', self.provider.adapt_id('m1 tiny'))
        self.assertEqual('m1.tiny s', self.provider.adapt_id('m1.tiny s'))

    def test_service_type(self):
        self.assertEqual('compute', self.provider.service_type)


class OoiProviderTest(OpenStackProviderTest):
    def setUp(self):
        super(OoiProviderTest, self).setUp()

        class FakeProvider(ooi_provider.OoiProvider):
            def __init__(self, opts):
                self.nova = mock.Mock()
                self.glance = mock.Mock()
                self.glance.http_client.get_endpoint.return_value = (
                    "http://glance.example.org:9292/v2"
                )
                self.session = mock.Mock()
                self.session.get_project_id.return_value = 'TEST_PROJECT_ID'
                self.auth_plugin = mock.MagicMock()
                self.auth_plugin.auth_url = 'http://foo.example.org:5000/v2'
                self.static = mock.Mock()
                self.keystone_cert_issuer = "foo"
                self.keystone_trusted_cas = []
                self.insecure = False
                self.os_cacert = '/etc/ssl/cas'
                self.os_project_id = None
                self.select_flavors = 'all'
                self._rescope_project = mock.Mock()
                self.all_images = False
                self.opts = mock.Mock()
                self.opts.extra_specs_infiniband_key = 'infiniband'
                self.opts.extra_specs_infiniband_value = 'true'

        self.provider = FakeProvider(None)

    def test_occify_terms(self):
        self.assertEqual('m1-tiny', self.provider.adapt_id('m1.tiny'))
        self.assertEqual('m1_tiny', self.provider.adapt_id('m1 tiny'))
        self.assertEqual('m1-tiny_s', self.provider.adapt_id('m1.tiny s'))

    def test_service_type(self):
        self.assertEqual('occi', self.provider.service_type)

    def test_get_images(self):
        # XXX move this to a custom class?
        # XXX add docker information
        expected_images = {
            'bar id': {
                'name': 'barimage',
                'id': 'bar id',
                'metadata': {},
                'file': 'v2/bar id/file',
                'image_description': None,
                'image_name': 'barimage',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': None,
                'image_marketplace_id': "%s" % urljoin(self.provider.glance
                                                       .http_client
                                                       .get_endpoint(),
                                                       'v2/bar id/file'),
                'image_id': 'http://schemas.openstack.org/template/os#bar_id',
                'image_native_id': 'bar id',
                'image_accel_type': None,
                'image_access_info': 'none',
                'image_minimal_cpu': None,
                'image_minimal_ram': None,
                'image_minimal_accel': None,
                'image_recommended_cpu': None,
                'image_recommended_ram': None,
                'image_recommended_accel': None,
                'image_size': None,
                'image_software': [],
                'image_traffic_in': [],
                'image_traffic_out': [],
                'image_context_format': None,
            },
            'foo.id': {
                'name': 'fooimage',
                'id': 'foo.id',
                'metadata': {},
                'marketplace': 'http://example.org/',
                'file': 'v2/foo.id/file',
                'image_description': None,
                'image_name': 'fooimage',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': None,
                'image_marketplace_id': 'http://example.org/',
                'image_id': 'http://schemas.openstack.org/template/os#foo-id',
                'image_native_id': 'foo.id',
                'image_accel_type': None,
                'image_access_info': 'none',
                'image_minimal_cpu': None,
                'image_minimal_ram': None,
                'image_minimal_accel': None,
                'image_recommended_cpu': None,
                'image_recommended_ram': None,
                'image_recommended_accel': None,
                'image_size': None,
                'image_software': [],
                'image_traffic_in': [],
                'image_traffic_out': [],
                'image_context_format': None,
            },
            'baz id': {
                'name': 'bazimage',
                'id': 'baz id',
                'file': 'v2/baz id/file',
                'image_description': None,
                'image_name': 'bazimage',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': None,
                'image_marketplace_id': "%s" % urljoin(self.provider.glance
                                                       .http_client
                                                       .get_endpoint(),
                                                       'v2/baz id/file'),
                'image_id': 'http://schemas.openstack.org/template/os#baz_id',
                'image_native_id': 'baz id',
                'docker_id': 'sha1:xxxxxxxxxxxxxxxxxxxxxxxxxx',
                'docker_tag': 'latest',
                'docker_name': 'test/image',
                'image_accel_type': None,
                'image_access_info': 'none',
                'image_minimal_cpu': None,
                'image_minimal_ram': None,
                'image_minimal_accel': None,
                'image_recommended_cpu': None,
                'image_recommended_ram': None,
                'image_recommended_accel': None,
                'image_size': None,
                'image_software': [],
                'image_traffic_in': [],
                'image_traffic_out': [],
                'image_context_format': None,
            }
        }

        with utils.nested(
                mock.patch.object(self.provider.static, 'get_image_defaults'),
                mock.patch.object(self.provider.glance.images, 'list'),
        ) as (m_get_image_defaults, m_images_list):
            m_get_image_defaults.return_value = {}
            m_images_list.return_value = FAKES.images

            images = self.provider.get_images()
            self.assertTrue(m_get_image_defaults.called)

        # Filter fields from the template that are not related to images
        self.assert_resources(expected_images,
                              images,
                              template="compute.ldif",
                              ignored_fields=["compute_service_name",
                                              "compute_api_type",
                                              "compute_api_version",
                                              ("compute_api_endpoint"
                                               "_technology"),
                                              "compute_capabilities",
                                              "compute_api_authn_method",
                                              "compute_total_ram",
                                              "compute_middleware",
                                              "compute_middleware_developer",
                                              "compute_middleware_version",
                                              "compute_endpoint_url",
                                              "compute_hypervisor",
                                              "compute_hypervisor_version",
                                              "compute_production_level",
                                              ("compute_service"
                                               "_production_level"),
                                              "compute_total_cores",
                                              "compute_total_ram",
                                              "template_platform",
                                              "template_cpu",
                                              "template_memory",
                                              "template_network",
                                              "template_disk",
                                              "template_ephemeral",
                                              "template_id",
                                              "template_infiniband"])

    def test_get_endpoints_with_defaults_from_static(self):
        expected_endpoints = {
            'endpoints': {
                'https://cloud.example.org:8787/': {
                    'compute_api_type': 'OCCI',
                    'compute_api_version': '11.11',
                    'compute_endpoint_id': '03e087c8fb3b495c9a360bcba3abf914',
                    'compute_endpoint_url': 'https://cloud.example.org:8787/'},
            },
            'compute_middleware_developer': 'OpenStack',
            'compute_middleware': 'OpenStack Nova',
            'compute_service_name': 'http://foo.example.org:5000/v2',
        }

        with mock.patch.object(
                self.provider.static, 'get_compute_endpoint_defaults'
        ) as m_get_endpoint_defaults:
            m_get_endpoint_defaults.return_value = {
                'compute_occi_api_version': '11.11',
                'compute_compute_api_version': '99.99',
            }
            r = mock.Mock()
            r.service_catalog = FAKES.catalog
            self.provider.auth_plugin.get_access.return_value = r
            endpoints = self.provider.get_compute_endpoints()
            self.assertTrue(m_get_endpoint_defaults.called)

        for k, v in expected_endpoints['endpoints'].items():
            self.assertDictContainsSubset(v, endpoints['endpoints'].get(k, {}))

    def test_get_endpoints_with_defaults(self):
        expected_endpoints = {
            'endpoints': {
                'https://cloud.example.org:8787/': {
                    'compute_api_type': 'OCCI',
                    'compute_api_version': 'UNKNOWN',
                    'compute_middleware': 'ooi',
                    'compute_middleware_version': 'UNKNOWN',
                    'compute_middleware_developer': 'CSIC',
                    'endpoint_issuer': self.provider.keystone_cert_issuer,
                    'endpoint_trusted_cas': [],
                    'compute_endpoint_id': '03e087c8fb3b495c9a360bcba3abf914',
                    'compute_endpoint_url': 'https://cloud.example.org:8787/'},
            },
            'compute_service_name': 'http://foo.example.org:5000/v2',
        }

        with mock.patch.object(
                self.provider.static, 'get_compute_endpoint_defaults'
        ) as m_get_endpoint_defaults:
            m_get_endpoint_defaults.return_value = {}
            r = mock.Mock()
            r.service_catalog = FAKES.catalog
            self.provider.auth_plugin.get_access.return_value = r
            endpoints = self.provider.get_compute_endpoints()
            self.assertTrue(m_get_endpoint_defaults.called)

        self.assertDictEqual(expected_endpoints, endpoints)
