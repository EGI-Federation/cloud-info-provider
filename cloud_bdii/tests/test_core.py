import contextlib
import os.path
import unittest

import mock

import cloud_bdii.core
from cloud_bdii.tests import data

DATA = data.DATA


class ModuleTest(unittest.TestCase):
    def test_main(self):
        with contextlib.nested(
            mock.patch.object(cloud_bdii.core, 'parse_opts'),
            mock.patch('cloud_bdii.core.CloudBDII'),
            mock.patch('cloud_bdii.core.ComputeBDII'),
            mock.patch('cloud_bdii.core.StorageBDII')
        ) as (m0, m1, m2, m3):
            m0.return_value = None
            for i in (m1, m2, m3):
                i = i.return_value
                i.render.return_value = 'foo'
                i.assert_called()

            self.assertIsNone(cloud_bdii.core.main())


class FakeBDIIOpts(object):
    full_bdii_ldif = False
    middleware = 'foo middleware'
    yaml_file = None
    template_dir = ''


class BaseTest(unittest.TestCase):
    def setUp(self):
        cloud_bdii.core.SUPPORTED_MIDDLEWARE = {
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

        bdii = cloud_bdii.core.BaseBDII(self.opts)

        for s, d, e in cases:
            with contextlib.nested(
                mock.patch.object(bdii.static_provider, 'foomethod'),
                mock.patch.object(bdii.dynamic_provider, 'foomethod')
            ) as (m_static, m_dynamic):
                m_static.return_value = s
                m_dynamic.return_value = d

                self.assertEqual(e, bdii._get_info_from_providers('foomethod'))

    def test_load_templates(self):
        self.opts.template_dir = 'foobar'
        tpls = ('foo', 'bar')
        tpl_contents = 'foo %(fobble)s'
        info = {'fobble': 'burble', 'brongle': 'farbla'}
        expected = tpl_contents % info

        with contextlib.nested(
            mock.patch.object(cloud_bdii.core.BaseBDII, 'templates', tpls),
            mock.patch('cloud_bdii.core.open',
                       mock.mock_open(read_data=tpl_contents), create=True)
        ) as (m_templates, m_open):
            bdii = cloud_bdii.core.BaseBDII(self.opts)
            for tpl in tpls:
                m_open.assert_any_call(
                    os.path.join(self.opts.template_dir, '%s.ldif' % tpl),
                    'r'
                )
                self.assertEqual(expected,
                                 bdii._format_template('foo', info))


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
