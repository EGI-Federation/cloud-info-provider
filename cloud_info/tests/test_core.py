import os.path
import unittest

import mock

import cloud_info.core
from cloud_info.tests import data
from cloud_info.tests import utils

DATA = data.DATA


class ModuleTest(unittest.TestCase):
    def test_main(self):
        with contextlib.nested(
            mock.patch.object(cloud_info.core, 'parse_opts'),
            mock.patch('cloud_info.core.CloudBDII'),
            mock.patch('cloud_info.core.IndigoComputeBDII'),
            mock.patch('cloud_info.core.ComputeBDII'),
            mock.patch('cloud_info.core.StorageBDII')
        ) as (m0, m1, m2, m3, m4):
            m0.return_value = None
            for i in (m1, m2, m3, m4):
                i = i.return_value
                i.render.return_value = 'foo'

            self.assertIsNone(cloud_info.core.main())

            # XXX only IndigoComputeBDII is used
            for i in (m0, m2):
                assert i.called


class FakeBDIIOpts(object):
    full_bdii_ldif = False
    middleware = 'foo middleware'
    yaml_file = None
    template_dir = ''
    template_extension = ''


class BaseTest(unittest.TestCase):
    def setUp(self):
        cloud_info.core.SUPPORTED_MIDDLEWARE = {
            'static': mock.MagicMock(),
            'foo middleware': mock.MagicMock(),
        }

        self.opts = FakeBDIIOpts()
        cwd = os.path.dirname(__file__)
        template_dir = os.path.join(cwd, '..', '..', 'etc', 'templates')
        self.opts.template_dir = template_dir


class BaseBDIITest(BaseTest):
    def test_get_info_from_providers(self):
        cases = (
            (
                {},
                {},
                {}
            ),
            (
                {'foo': 'bar'},
                {'bar': 'bazonk'},
                {'foo': 'bar', 'bar': 'bazonk'},
            ),
            (
                {'foo': 'bar'},
                {'foo': 'bazonk'},
                {'foo': 'bazonk'},
            ),
            (
                {},
                {'foo': 'bazonk'},
                {'foo': 'bazonk'},
            ),
            (
                {'foo': 'bar'},
                {},
                {'foo': 'bar'},
            ),
        )

        bdii = cloud_info.core.BaseBDII(self.opts)

        for s, d, e in cases:
            with utils.nested(
                mock.patch.object(bdii.static_provider, 'foomethod'),
                mock.patch.object(bdii.dynamic_provider, 'foomethod')
            ) as (m_static, m_dynamic):
                m_static.return_value = s
                m_dynamic.return_value = d

                self.assertEqual(e, bdii._get_info_from_providers('foomethod'))

    def test_load_templates(self):
        self.opts.template_dir = 'foobar'
        tpls = ['foo', 'bar']
        tpl_contents = 'foo ${attributes["fobble"]}'
        info = {'fobble': 'burble', 'brongle': 'farbla'}
        expected_tpls = {
            'foo': 'foobar/foo.%s' % self.opts.template_extension,
            'bar': 'foobar/bar.%s' % self.opts.template_extension
        }
        expected = 'foo burble'

        bdii = cloud_info.core.BaseBDII(self.opts)
        with utils.nested(
            mock.patch.object(bdii, 'templates', tpls),
            mock.patch('mako.util.open',
                       mock.mock_open(read_data=tpl_contents), create=True)
        ):
            bdii.load_templates()
            templates_files = bdii.__dict__['templates_files']
            self.assertEqual(templates_files, expected_tpls)
            self.assertEqual(expected, bdii._format_template('foo', info))



class CloudBDIITest(BaseTest):
    @mock.patch.object(cloud_bdii.core.CloudBDII, '_get_info_from_providers')
    def test_render(self, m_get_info):
        m_get_info.return_value = DATA.site_info
        bdii = cloud_bdii.core.CloudBDII(self.opts)
        self.assertIsNotNone(bdii.render())

    @mock.patch.object(cloud_bdii.core.CloudBDII, '_get_info_from_providers')
    def test_render_full(self, m_get_info):
        self.opts.full_bdii_ldif = True
        m_get_info.return_value = DATA.site_info_full
        bdii = cloud_bdii.core.CloudBDII(self.opts)
        self.assertNotEqual('', bdii.render())


class StorageBDIITEst(BaseTest):
    @mock.patch.object(cloud_bdii.core.StorageBDII, '_get_info_from_providers')
    def test_render(self, m_get_info):
        m_get_info.side_effect = (
            DATA.storage_endpoints,
            DATA.site_info
        )
        bdii = cloud_bdii.core.StorageBDII(self.opts)
        self.assertNotEqual('', bdii.render())

    @mock.patch.object(cloud_bdii.core.StorageBDII, '_get_info_from_providers')
    def test_render_empty(self, m_get_info):
        m_get_info.side_effect = (
            {},
            DATA.site_info
        )
        bdii = cloud_bdii.core.StorageBDII(self.opts)
        self.assertEqual('', bdii.render())


class ComputeBDIITest(BaseTest):
    @mock.patch.object(cloud_bdii.core.ComputeBDII, '_get_info_from_providers')
    def test_render(self, m_get_info):
        m_get_info.side_effect = (
            DATA.compute_endpoints,
            DATA.site_info,
            DATA.compute_templates,
            DATA.compute_images,
        )
        bdii = cloud_bdii.core.ComputeBDII(self.opts)
        self.assertNotEqual('', bdii.render())

    @mock.patch.object(cloud_bdii.core.ComputeBDII, '_get_info_from_providers')
    def test_render_empty(self, m_get_info):
        m_get_info.side_effect = (
            {},
            DATA.site_info,
            DATA.compute_templates,
            DATA.compute_images,
        )
        bdii = cloud_bdii.core.ComputeBDII(self.opts)
        self.assertEqual('', bdii.render())


class IndigoComputeBDIITest(BaseTest):
    @mock.patch.object(cloud_info.core.IndigoComputeBDII,
                       '_get_info_from_providers')
    def test_render(self, m_get_info):
        m_get_info.side_effect = (
            DATA.compute_endpoints,
            DATA.site_info,
            DATA.compute_templates,
            DATA.compute_images,
        )
        bdii = cloud_info.core.IndigoComputeBDII(self.opts)
        self.assertNotEqual('', bdii.render())

    @mock.patch.object(cloud_info.core.IndigoComputeBDII,
                       '_get_info_from_providers')
    def test_render_empty(self, m_get_info):
        m_get_info.side_effect = (
            {},
            DATA.site_info,
            DATA.compute_templates,
            DATA.compute_images,
        )
        bdii = cloud_info.core.IndigoComputeBDII(self.opts)
        self.assertEqual('', bdii.render())
