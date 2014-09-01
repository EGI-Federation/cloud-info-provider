import argparse
import unittest

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
                                  '--on-rpcxml-endpoint', 'bar'])

        self.assertEqual(opts.on_auth, 'foo')
        self.assertEqual(opts.on_rpcxml_endpoint, 'bar')

    def test_options(self):
        class Opts(object):
            on_auth = 'foo'
            on_rpcxml_endpoint = 'bar'

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


class OpenNebulaBaseProviderTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(OpenNebulaBaseProviderTest, self).__init__(*args, **kwargs)
        self.expected_images = {
            '80': {
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'image_version': None,
                'image_platform': 'amd64',
                'image_os_version': None,
                'image_name': 'CERNVM-3.3.0-40GB@fedcloud-dukan',
                'image_id': 'os_tpl#80',
                'image_description': None,
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

        self.provider = FakeProvider(None)

    @mock.patch('urllib2.urlopen')
    def test_get_images(self, mock_open):
        resp = mock.Mock()
        resp.read.side_effect = [FAKES.templatepool, FAKES.imagepool]
        mock_open.return_value = resp
        self.assertDictEqual(self.expected_images,
                             self.provider.get_images())


class OpenNebulaProviderTest(OpenNebulaBaseProviderTest):
    def __init__(self, *args, **kwargs):
        super(OpenNebulaProviderTest, self).__init__(*args, **kwargs)
        self.provider_class = opennebula.OpenNebulaProvider
        self.maxDiff = None


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
