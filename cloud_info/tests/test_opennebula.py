import argparse
import unittest
import uuid

import mock

from cloud_info import exceptions
from cloud_info.providers import opennebula
from cloud_info.tests import data

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
                'image_os_family': None,
                'image_os_name': None,
                'image_os_version': None,
                'image_platform': 'amd64',
                'image_name': 'CERNVM-3.3.0-40GB@fedcloud-dukan',
                'image_id': 'os_tpl#80',
                'image_description': (
                    'This version of CERNVM has been modified by EGI with '
                    'the followign changes - default OS extended to 40GB '
                    'of disk - updated OpenNebula Cloud-Init driver to '
                    'latest version 0.7.5 - enabled all Cloud-Init data '
                    'sources'
                )
            },
            '86': {
                'image_platform': 'amd64',
                'image_name': 'Ubuntu-Server-14.04-LTS-ht-xxl@fedcloud-dukan',
                'image_id': 'os_tpl#86',
                'image_version': None,
                'image_description': None,
                'image_marketplace_id': None,
                'image_os_family': None,
                'image_os_name': None,
                'image_platform': 'amd64',
                'image_os_version': None
            }
        }
        self.provider_class = opennebula.OpenNebulaBaseProvider
        self.maxDiff = None

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
                'dev_prefix': 'xvd',
                'bus': 'ide',
                'image_name': 'monitoring',
                'image_id': '30',
                'description': 'Monitoring image',
                'image_description': 'Monitoring image',
                'name': 'monitoring',
                'path': '/home/xparak/openwrt-x86-xen_domu-combined-ext4.img',
                'type': 'OS'
            },
            '31': {
                'name': 'debian6',
                'path': '/home/xparak/debian-opennebula.img',
                'image_marketplace_id': None,
                'image_name': 'debian6',
                'image_id': '31',
                'bus': 'ide',
                'description': 'Debian6 sample image',
                'image_description': 'Debian6 sample image',
                'dev_prefix': 'xvd',
                'type': 'OS'
            },
            '183': {
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'dev_prefix': 'xvd',
                'image_name': 'c0482bc2-bf41-5d49-a85f-a750174a186b',
                'image_id': '183',
                'image_description': (
                    'This version of CERNVM has been modified by EGI '
                    'with the followign changes - default OS extended to '
                    '40GB of disk - updated OpenNebula Cloud-Init driver '
                    'to latest version 0.7.5 - enabled all Cloud-Init '
                    'data sources'
                ),
                'description': (
                    'This version of CERNVM has been modified by EGI '
                    'with the followign changes - default OS extended to '
                    '40GB of disk - updated OpenNebula Cloud-Init driver '
                    'to latest version 0.7.5 - enabled all Cloud-Init '
                    'data sources'
                ),
                'vmcatcher_event_ad_mpuri': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_dc_description': (
                    'This version of CERNVM has been modified by EGI '
                    'with the followign changes - default OS extended to '
                    '40GB of disk - updated OpenNebula Cloud-Init driver '
                    'to latest version 0.7.5 - enabled all Cloud-Init '
                    'data sources'
                ),
                'vmcatcher_event_dc_identifier': (
                    'c0482bc2-bf41-5d49-'
                    'a85f-a750174a186b'
                ),
                'vmcatcher_event_dc_title': (
                    'Image for CernVM [Scientific Linux/6.0/KVM]'
                ),
                'vmcatcher_event_filename': (
                    'c0482bc2-bf41-5d49-a85f-a750174a186b'
                ),
                'vmcatcher_event_hv_format': 'OVA',
                'vmcatcher_event_hv_hypervisor': 'KVM',
                'vmcatcher_event_hv_size': '121243136',
                'vmcatcher_event_hv_uri': (
                    'http://appliance-repo.egi.eu/images/base/'
                    'CERNVM/3.3.0/CERNVM-3.3.0-40GB.ova'
                ),
                'vmcatcher_event_hv_version': '3.3.0-1',
                'vmcatcher_event_il_dc_identifier': (
                    '76fdee70-8119-5d33-9f40-3c57e1c60df1'
                ),
                'vmcatcher_event_sl_arch': 'x86_64',
                'vmcatcher_event_sl_checksum_sha512': (
                    '5c548a09467df6ff6ee77659a8cfe15115ef36'
                    '6b94baa30c47e079b744309652a17c8f947ab4'
                    '37e70c799480b4b5dc3d68a3b22581b3318db35dd3364e83dab0'
                ),
                'vmcatcher_event_sl_comments': '""',
                'vmcatcher_event_sl_os': 'Linux',
                'vmcatcher_event_sl_osversion': '6.0',
                'vmcatcher_event_type': 'AvailablePostfix'
            },
            '186': {
                'dev_prefix': 'xvd',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_ad_mpuri': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_dc_description': (
                    'This machine image is provided by '
                    'the Ubuntu project http//cloud-images.ubuntu.com'
                ),
                'vmcatcher_event_dc_identifier': (
                    '800f345f-5278-5523-a1dc-8a98476006f8'
                ),
                'vmcatcher_event_dc_title': (
                    'Basic Ubuntu Server 12.04 LTS OS Disk Image'
                ),
                'vmcatcher_event_filename': (
                    '800f345f-5278-5523-a1dc-8a98476006f8'
                ),
                'vmcatcher_event_hv_format': 'OVA',
                'vmcatcher_event_hv_hypervisor': 'QEMU-KVM',
                'vmcatcher_event_hv_size': '343963136',
                'vmcatcher_event_hv_uri': (
                    'http://appliance-repo.egi.eu/images/base/'
                    'UbuntuServer-12.04-x86_64-base/1.0/'
                    'UbuntuServer-12.04-x86_64-base.ova'
                ),
                'vmcatcher_event_hv_version': '20140227',
                'vmcatcher_event_il_dc_identifier': (
                    '76fdee70-8119-5d33-9f40-3c57e1c60df1'
                ),
                'vmcatcher_event_sl_arch': 'x86_64',
                'vmcatcher_event_sl_checksum_sha512': (
                    '6e93e48d6fcfc0d9bdb435d723eb0dad19e7c5f931'
                    '375dea9efc48a43c920edd57ae7001e0d5f2264e49'
                    'f2a9747fe721501185a3eacec87882de849464d1cc43'
                ),
                'vmcatcher_event_sl_comments': '""',
                'vmcatcher_event_sl_os': 'Linux',
                'vmcatcher_event_sl_osversion': 'Ubuntu 12.04',
                'vmcatcher_event_type': 'AvailablePostfix',
                'image_name': '800f345f-5278-5523-a1dc-8a98476006f8',
                'image_id': '186',
                'description': (
                    'This machine image is provided by '
                    'the Ubuntu project http//cloud-images.ubuntu.com'
                ),
                'image_description': (
                    'This machine image is provided by '
                    'the Ubuntu project http//cloud-images.ubuntu.com'
                )
            },
            '187': {
                'image_description': '""',
                'description': '""',
                'image_id': '187',
                'dev_prefix': 'xvd',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_ad_mpuri': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_dc_description': '""',
                'vmcatcher_event_dc_identifier': (
                    'b25c250b-637b-5622-a6fb-b0db4f2883f2'
                ),
                'vmcatcher_event_dc_title': 'OS Disk Image',
                'vmcatcher_event_filename': (
                    'b25c250b-637b-5622-a6fb-b0db4f2883f2'
                ),
                'vmcatcher_event_hv_format': 'OVA',
                'vmcatcher_event_hv_hypervisor': 'QEMU-KVM',
                'vmcatcher_event_hv_size': '313900544',
                'vmcatcher_event_hv_uri': (
                    'http://appliance-repo.egi.eu/images/base/'
                    'SL-6.5-x86_64-minimal/20140617/'
                    'ScientificLinux-65-minimal.ova'
                ),
                'vmcatcher_event_hv_version': '20140617',
                'vmcatcher_event_il_dc_identifier': (
                    '76fdee70-8119-5d33-9f40-3c57e1c60df1'
                ),
                'vmcatcher_event_sl_arch': 'x86_64',
                'vmcatcher_event_sl_checksum_sha512': (
                    '2507a3b41de50b2394e87d8d35e099f34baafe24dab'
                    'd61bc48a4783582a6d82ea17560458c1aa057aa3fd8'
                    '5a97bbda3240388f4453eed59ae700a1a2014865a6'
                ),
                'vmcatcher_event_sl_comments': '""',
                'vmcatcher_event_sl_os': 'Linux',
                'vmcatcher_event_sl_osversion': 'Scientific Linux 6.5',
                'vmcatcher_event_type': 'AvailablePostfix',
                'image_name': 'b25c250b-637b-5622-a6fb-b0db4f2883f2'
            },
            '188': {
                'image_description': '""',
                'description': '""',
                'dev_prefix': 'xvd',
                'image_id': '188',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_ad_mpuri': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_dc_description': '""',
                'vmcatcher_event_dc_identifier': (
                    '662b0e71-3e21-5f43-b6a1-cc2f51319fa7'
                ),
                'vmcatcher_event_dc_title': (
                    'Image for CentOS 6 minimal [CentOS/6.5/KVM]'
                ),
                'vmcatcher_event_filename': (
                    '662b0e71-3e21-5f43-b6a1-cc2f51319fa7'
                ),
                'vmcatcher_event_hv_format': 'OVA',
                'vmcatcher_event_hv_hypervisor': 'KVM',
                'vmcatcher_event_hv_size': '290307584',
                'vmcatcher_event_hv_uri': (
                    'http://appliance-repo.egi.eu/images/base/'
                    'CentOS-6.5-x86_64-minimal/20140617/CentOS-65-minimal.ova'
                ),
                'vmcatcher_event_hv_version': '20140617',
                'vmcatcher_event_il_dc_identifier': (
                    '76fdee70-8119-5d33-9f40-3c57e1c60df1'
                ),
                'vmcatcher_event_sl_arch': 'x86_64',
                'vmcatcher_event_sl_checksum_sha512': (
                    'f62a6b51a6cc991c6406c6f3ffe3c73728fb6f89348dde'
                    'c260fb2805aee53afe6cb67092c0a344db9c078618af7a'
                    '029ab87f9c0cf7c937f11d43401c25e23069'
                ),
                'vmcatcher_event_sl_comments': '""',
                'vmcatcher_event_sl_os': 'Linux',
                'vmcatcher_event_sl_osversion': '6.5',
                'vmcatcher_event_type': 'AvailablePostfix',
                'image_name': '662b0e71-3e21-5f43-b6a1-cc2f51319fa7'
            },
            '189': {
                'image_description': '""',
                'description': '""',
                'image_id': '189',
                'dev_prefix': 'xvd',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_ad_mpuri': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_dc_description': '""',
                'vmcatcher_event_dc_identifier': (
                    'de355bfb-5781-5b0c-9ccd-9bd3d0d2be06'
                ),
                'vmcatcher_event_dc_title': (
                    'Image for Ubuntu Server 14.04 LTS [Ubuntu/14.04 LTS/KVM]'
                ),
                'vmcatcher_event_filename': (
                    'de355bfb-5781-5b0c-9ccd-9bd3d0d2be06'
                ),
                'vmcatcher_event_hv_format': 'OVA',
                'vmcatcher_event_hv_hypervisor': 'KVM',
                'vmcatcher_event_hv_size': '242341376',
                'vmcatcher_event_hv_uri': (
                    'http://appliance-repo.egi.eu/images/base/'
                    'UbuntuServer-14.04-x86_64-base/20140607.1/'
                    'ubuntu-14.04-server-cloudimg-amd64.ova'
                ),
                'vmcatcher_event_hv_version': '20140607.1',
                'vmcatcher_event_il_dc_identifier': (
                    '76fdee70-8119-5d33-9f40-3c57e1c60df1'
                ),
                'vmcatcher_event_sl_arch': 'x86_64',
                'vmcatcher_event_sl_checksum_sha512': (
                    '44b1d93eb4bf6903724f67130d39e43a31826b512ea'
                    '7047989cef3aca3c9f8e3c848581643d616aea40caa'
                    'd2f31a9b887929f0217dd5495a6e121d4cf4506af4'
                ),
                'vmcatcher_event_sl_comments': '""',
                'vmcatcher_event_sl_os': 'Linux',
                'vmcatcher_event_sl_osversion': '14.04 LTS',
                'vmcatcher_event_type': 'AvailablePostfix',
                'image_name': 'de355bfb-5781-5b0c-9ccd-9bd3d0d2be06'
            },
            '190': {
                'image_description': 'ttylinux-kvm',
                'description': 'ttylinux-kvm',
                'dev_prefix': 'xvd',
                'image_id': '190',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_ad_mpuri': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_dc_description': 'ttylinux-kvm',
                'vmcatcher_event_dc_identifier': (
                    '93084776-1176-4849-95dc-cc7a15f2ce97'
                ),
                'vmcatcher_event_dc_title': 'ttylinux-kvm',
                'vmcatcher_event_filename': (
                    '93084776-1176-4849-95dc-cc7a15f2ce97'
                ),
                'vmcatcher_event_hv_format': 'RAW',
                'vmcatcher_event_hv_hypervisor': 'QEMU,KVM',
                'vmcatcher_event_hv_size': '41943040',
                'vmcatcher_event_hv_uri': (
                    'http://cloud.cesga.es/images/'
                    '93084776-1176-4849-95dc-cc7a15f2ce97'
                    '_2014-06-19_09-15-34.RAW'
                ),
                'vmcatcher_event_hv_version': '0.0.93',
                'vmcatcher_event_il_dc_identifier': (
                    '2204eed5-f37e-45b9-82c6-85697356109c'
                ),
                'vmcatcher_event_sl_arch': 'x86_64',
                'vmcatcher_event_sl_checksum_sha512': (
                    '4aa7c7665e6af4daabf3981516e61b0fab54f'
                    'eedb70399933dc7694df68645949c193a99f9'
                    '443b62c5d3689a263184d95268bee56bb76818e25385058d3ba891'
                ),
                'vmcatcher_event_sl_comments': (
                    'This is a very small image that works '
                    "with OpenNebula. It's already contextualized. "
                    'login:root pass:password'
                ),
                'vmcatcher_event_sl_os': 'Linux',
                'vmcatcher_event_sl_osversion': '1',
                'vmcatcher_event_type': 'AvailablePostfix',
                'image_name': '93084776-1176-4849-95dc-cc7a15f2ce97',
            },
            '192': {
                'image_description': '""',
                'description': '""',
                'image_id': '192',
                'dev_prefix': 'xvd',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'image_name': '2f55ff2a-abe3-52b3-ad56-aded22a63fae',
                'vmcatcher_event_ad_mpuri': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_dc_description': '""',
                'vmcatcher_event_dc_identifier': (
                    '2f55ff2a-abe3-52b3-ad56-aded22a63fae'
                ),
                'vmcatcher_event_dc_title': 'OS Disk Image',
                'vmcatcher_event_filename': (
                    '2f55ff2a-abe3-52b3-ad56-aded22a63fae'
                ),
                'vmcatcher_event_hv_format': 'OVA',
                'vmcatcher_event_hv_hypervisor': 'QEMU-KVM',
                'vmcatcher_event_hv_size': '313900544',
                'vmcatcher_event_hv_uri': (
                    'http://appliance-repo.egi.eu/images/base/'
                    'SL-6.5-x86_64-minimal/20140617/'
                    'ScientificLinux-65-minimal.ova'
                ),
                'vmcatcher_event_hv_version': '20140617',
                'vmcatcher_event_il_dc_identifier': (
                    '38590342-11d6-5066-bcc2-f1437b1d3b69'
                ),
                'vmcatcher_event_sl_arch': 'x86_64',
                'vmcatcher_event_sl_checksum_sha512': (
                    '2507a3b41de50b2394e87d8d35e099f34baafe2'
                    '4dabd61bc48a4783582a6d82ea17560458c1aa0'
                    '57aa3fd85a97bbda3240388f4453eed59ae700a1a2014865a6'
                ),
                'vmcatcher_event_sl_comments': '""',
                'vmcatcher_event_sl_os': 'Linux',
                'vmcatcher_event_sl_osversion': 'Scientific Linux 6.5',
                'vmcatcher_event_type': 'AvailablePostfix'
            },
            '193': {
                'dev_prefix': 'xvd',
                'image_description': '""',
                'description': '""',
                'image_id': '193',
                'image_marketplace_id': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_ad_mpuri': (
                    'https://appdb.egi.eu/store/vm/image/'
                    'c0482bc2-bf41-5d49-a85f-a750174a186b:642/'
                ),
                'vmcatcher_event_dc_description': '""',
                'vmcatcher_event_dc_identifier': (
                    'ba4235f2-8732-5376-ad46-53bf176ea036'
                ),
                'vmcatcher_event_dc_title': (
                    'Image for Ubuntu Server 14.04 LTS [Ubuntu/14.04 LTS/KVM]'
                ),
                'vmcatcher_event_filename': (
                    'ba4235f2-8732-5376-ad46-53bf176ea036'
                ),
                'vmcatcher_event_hv_format': 'OVA',
                'vmcatcher_event_hv_hypervisor': 'KVM',
                'vmcatcher_event_hv_size': '242341376',
                'vmcatcher_event_hv_uri': (
                    'http://appliance-repo.egi.eu/images/base/'
                    'UbuntuServer-14.04-x86_64-base/20140607.1/'
                    'ubuntu-14.04-server-cloudimg-amd64.ova'
                ),
                'vmcatcher_event_hv_version': '20140607.1',
                'vmcatcher_event_il_dc_identifier': (
                    'ebdb532d-d419-53cb-8a9c-3bd066059428'
                ),
                'vmcatcher_event_sl_arch': 'x86_64',
                'vmcatcher_event_sl_checksum_sha512': (
                    '44b1d93eb4bf6903724f67130d39e43a31'
                    '826b512ea7047989cef3aca3c9f8e3c848'
                    '581643d616aea40caad2f31a9b887929f0'
                    '217dd5495a6e121d4cf4506af4'
                ),
                'vmcatcher_event_sl_comments': '""',
                'vmcatcher_event_sl_os': 'Linux',
                'vmcatcher_event_sl_osversion': '14.04 LTS',
                'vmcatcher_event_type': 'AvailablePostfix',
                'image_name': 'ba4235f2-8732-5376-ad46-53bf176ea036',
            },
            '194': {
                'docker_name': 'indigodataclouddevel/mesos-slave',
                'docker_tag': 'latest',
                'docker_id': (
                    'sha256:e751041cceaf609983ec34f3e5ef6f'
                    '1e08f02c99eeede80347a5d5f2ec0a3fc2'
                ),
                'image_marketplace_id': None,
                'description': 'Docker image',
                'image_description': 'Docker image',
                'dev_prefix': 'hd',
                'image_id': '194',
                'image_name': 'indigodataclouddevel_mesos-slave'
            }
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
