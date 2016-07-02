import argparse
import unittest
import uuid

import mock

from cloud_bdii import exceptions
from cloud_bdii.providers import opennebula
from cloud_bdii.tests import data

FAKES = data.ONE_FAKES


class OpenNebulaBaseProviderOptionsTest(unittest.TestCase):
    def setUp(self):
        self.provider = opennebula.OpenNebulaBaseProvider

    def test_populate_parser(self):
        parser = argparse.ArgumentParser()
        self.provider.populate_parser(parser)

        opts = parser.parse_args(['--on-auth', 'foo',
                                  '--on-rpcxml-endpoint', 'bar',
                                  '--vmcatcher-images'])

        self.assertEqual(opts.on_auth, 'foo')
        self.assertEqual(opts.on_rpcxml_endpoint, 'bar')
        self.assertTrue(opts.vmcatcher_images)

    def test_options(self):
        class Opts(object):
            on_auth = 'foo'
            on_rpcxml_endpoint = 'bar'
            vmcatcher_images = False

        # Check that the required opts are there
        for opt in ('on_auth', 'on_rpcxml_endpoint'):
            o = Opts()
            setattr(o, opt, None)
            self.assertRaises(exceptions.OpenNebulaProviderException,
                              self.provider, o)


class OpenNebulaProviderOptionsTest(OpenNebulaBaseProviderOptionsTest):
    def setUp(self):
        self.provider = opennebula.OpenNebulaProvider


class OpenNebulaROCCIProviderOptionsTest(OpenNebulaBaseProviderOptionsTest):
    def setUp(self):
        self.provider = opennebula.OpenNebulaROCCIProvider


class IndigoONProviderOptionsTest(OpenNebulaBaseProviderOptionsTest):
    def setUp(self):
        self.provider = opennebula.IndigoONProvider


class OpenNebulaBaseProviderTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(OpenNebulaBaseProviderTest, self).__init__(*args, **kwargs)
        self.expected_images = {
            '80': {
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'image_version': '3.3.0-1',
                'image_platform': 'amd64',
                'image_os_version': None,
                'image_name': 'CERNVM-3.3.0-40GB@fedcloud-dukan',
                'image_id': 'os_tpl#80',
                'image_description': (
                    'This version of CERNVM has been modified by EGI with '
                    'the followign changes - default OS extended to 40GB '
                    'of disk - updated OpenNebula Cloud-Init driver to '
                    'latest version 0.7.5 - enabled all Cloud-Init data '
                    'sources'
                ),
                'image_os_name': None,
                'image_os_family': None
            },
            '86': {
                'image_marketplace_id': None,
                'image_version': None,
                'image_platform': 'amd64',
                'image_os_version': None,
                'image_name': 'Ubuntu-Server-14.04-LTS-ht-xxl@fedcloud-dukan',
                'image_id': 'os_tpl#86',
                'image_description': None,
                'image_os_name': None,
                'image_os_family': None},
        }
        self.provider_class = opennebula.OpenNebulaBaseProvider

    def setUp(self):
        class FakeProvider(self.provider_class):
            def __init__(self, opts):
                self.on_auth = None
                self.on_rpcxml_endpoint = "http://foo.bar.com/"
                self.api = mock.Mock()
                self.static = mock.Mock()
                self.static.get_image_defaults.return_value = {}
                self.opts = opts

        class Opts(object):
            on_auth = 'foo'
            on_rpcxml_endpoint = 'bar'
            vmcatcher_images = False

        self.provider = FakeProvider(Opts())

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_get_images(self, mock_open):
        resp = mock.Mock()
        resp.read.side_effect = [FAKES.templatepool, FAKES.imagepool]
        mock_open.return_value = resp
        self.assertDictEqual(self.expected_images,
                             self.provider.get_images())

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_get_filtered_images(self, mock_open):
        resp = mock.Mock()
        resp.read.side_effect = [FAKES.templatepool, FAKES.imagepool]
        mock_open.return_value = resp
        self.provider.opts.vmcatcher_images = True
        filtered_images = {k: v for (k, v) in self.expected_images.items()
                           if v.get('image_marketplace_id')}
        self.assertDictEqual(filtered_images,
                             self.provider.get_images())


class OpenNebulaProviderTest(OpenNebulaBaseProviderTest):
    def __init__(self, *args, **kwargs):
        super(OpenNebulaProviderTest, self).__init__(*args, **kwargs)
        self.provider_class = opennebula.OpenNebulaProvider
        self.maxDiff = None


class IndigoONProviderTest(OpenNebulaBaseProviderTest):
    def __init__(self, *args, **kwargs):
        super(IndigoONProviderTest, self).__init__(*args, **kwargs)
        self.provider_class = opennebula.IndigoONProvider
        self.maxDiff = None
        self.expected_images = {
            '30': {
                'image_marketplace_id': None,
                'image_version': None,
                'image_platform': 'amd64',
                'image_os_version': None,
                'image_name': 'monitoring',
                'image_id': '30',
                'image_description': 'Monitoring image',
                'image_os_name': None,
                'image_os_family': None
            },
            '31': {
                'image_marketplace_id': None,
                'image_version': None,
                'image_platform': 'amd64',
                'image_os_version': None,
                'image_name': 'debian6',
                'image_id': '31',
                'image_description': 'Debian6 sample image',
                'image_os_name': None,
                'image_os_family': None},
            '183': {
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'image_version': '3.3.0-1',
                'image_platform': 'amd64',
                'image_os_version': None,
                'image_name': 'c0482bc2-bf41-5d49-a85f-a750174a186b',
                'image_id': '183',
                'image_description': (
                    'This version of CERNVM has been modified by EGI '
                    'with the followign changes - default OS extended to '
                    '40GB of disk - updated OpenNebula Cloud-Init driver '
                    'to latest version 0.7.5 - enabled all Cloud-Init '
                    'data sources'
                ),
                'image_os_name': None,
                'image_os_family': None},
            '186': {
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'image_version': '20140227',
                'image_platform': 'amd64',
                'image_os_version': None,
                'image_name': '800f345f-5278-5523-a1dc-8a98476006f8',
                'image_id': '186',
                'image_description': (
                    'This machine image is provided by '
                    'the Ubuntu project http//cloud-images.ubuntu.com'
                ),
                'image_os_name': None,
                'image_os_family': None},
            '187': {
                'image_description': '""',
                'image_id': '187',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'image_name': 'b25c250b-637b-5622-a6fb-b0db4f2883f2',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': '20140617'},
            '188': {
                'image_description': '""',
                'image_id': '188',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'image_name': '662b0e71-3e21-5f43-b6a1-cc2f51319fa7',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': '20140617'},
            '189': {
                'image_description': '""',
                'image_id': '189',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'image_name': 'de355bfb-5781-5b0c-9ccd-9bd3d0d2be06',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': '20140607.1'},
            '190': {
                'image_description': 'ttylinux-kvm',
                'image_id': '190',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'image_name': '93084776-1176-4849-95dc-cc7a15f2ce97',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': '0.0.93'},
            '192': {
                'image_description': '""',
                'image_id': '192',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'image_name': '2f55ff2a-abe3-52b3-ad56-aded22a63fae',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': '20140617'},
            '193': {
                'image_description': '""',
                'image_id': '193',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'image_name': 'ba4235f2-8732-5376-ad46-53bf176ea036',
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_version': '20140607.1'}
        }


class OpenNebulaROCCIProviderTest(OpenNebulaBaseProviderTest):
    def __init__(self, *args, **kwargs):
        super(OpenNebulaROCCIProviderTest, self).__init__(*args, **kwargs)
        self.provider_class = opennebula.OpenNebulaROCCIProvider
        self.expected_images['80']['image_id'] = (
            'os_tpl#uuid_cernvm_3_3_0_40gb_fedcloud_dukan_80'
        )
        self.expected_images['86']['image_id'] = (
            'os_tpl#uuid_ubuntu_server_14_04_lts_ht_xxl_fedcloud_dukan_86'
        )

    def setUp(self):
        class FakeProvider(self.provider_class):
            def __init__(self, opts):
                self.on_auth = None
                self.on_rpcxml_endpoint = "http://foo.bar.com/"
                self.api = mock.Mock()
                self.static = mock.Mock()
                self.static.get_image_defaults.return_value = {}
                self.static.get_template_defaults.return_value = {}
                self.opts = opts

        class Opts(object):
            on_auth = 'foo'
            on_rpcxml_endpoint = 'bar'
            rocci_template_dir = 'foobar'
            vmcatcher_images = False

        self.provider = FakeProvider(Opts())

    def test_templates_missing(self):
        fake_dir = uuid.uuid4().hex
        self.provider.opts.template_dir = fake_dir
        self.assertRaises(OSError, self.provider.get_templates)

    def test_load_templates(self):
        # TBD
        pass
