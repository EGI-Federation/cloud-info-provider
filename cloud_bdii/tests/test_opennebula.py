import argparse
import unittest

import mock

from cloud_bdii.providers import opennebula
from cloud_bdii.providers import opennebularocci
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
            # FIXME(aloga): this should be a proper exception
            self.assertRaises(SystemExit,
                              self.provider, o)


class OpenNebulaProviderOptionsTest(OpenNebulaBaseProviderOptionsTest):
    def setUp(self):
        self.provider = opennebula.OpenNebulaProvider


class OpenNebulaROCCIProviderOptionsTest(OpenNebulaBaseProviderOptionsTest):
    def setUp(self):
        self.provider = opennebularocci.OpenNebulaROCCIProvider


class OpenNebulaBaseProviderTest(unittest.TestCase):
    def setUp(self):
        class FakeProvider(opennebula.OpenNebulaBaseProvider):
            def __init__(self, opts):
                self.on_auth = None
                self.on_rpcxml_endpoint = "http://foo.bar.com/"
                self.api = mock.Mock()
                self.static = mock.Mock()
                self.static.get_image_defaults.return_value = {}

        self.provider = FakeProvider(None)

    @mock.patch('urllib2.urlopen')
    def test_get_images(self, mock_open):
        expected_images = {
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

        resp = mock.Mock()
        resp.read.side_effect = [FAKES.templatepool, FAKES.imagepool]
        mock_open.return_value = resp
        self.assertDictEqual(expected_images,
                             self.provider.get_images())
