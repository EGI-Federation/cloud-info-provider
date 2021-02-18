import cloud_info_provider.collectors.base
import cloud_info_provider.collectors.cloud
import cloud_info_provider.collectors.compute
import cloud_info_provider.collectors.storage
from cloud_info_provider.exceptions import CloudInfoException
import mock
from cloud_info_provider.tests import base, data, utils

DATA = data.DATA


class BaseCollectorTest(base.BaseTest):
    @mock.patch.multiple(
        cloud_info_provider.collectors.base.BaseCollector,
        __abstractmethods__=set(),
        fetch=mock.Mock(return_value={}),
    )
    def test_get_info_from_providers(self):
        cases = (
            ({}, {}, {}),
            ({"foo": "bar"}, {"bar": "bazonk"}, {"foo": "bar", "bar": "bazonk"},),
            ({"foo": "bar"}, {"foo": "bazonk"}, {"foo": "bazonk"},),
            ({}, {"foo": "bazonk"}, {"foo": "bazonk"},),
            ({"foo": "bar"}, {}, {"foo": "bar"},),
        )

        # pylint: disable=abstract-class-instantiated
        base = cloud_info_provider.collectors.base.BaseCollector(
            self.opts, self.providers, None
        )

        for s, d, e in cases:
            with utils.nested(
                mock.patch.object(base.static_provider, "method"),
                mock.patch.object(base.dynamic_provider, "method"),
            ) as (m_static, m_dynamic):
                m_static.return_value = s
                m_dynamic.return_value = d

                self.assertEqual(e, base._get_info_from_providers("method"))


class CloudCollectorTest(base.BaseTest):
    @mock.patch.object(
        cloud_info_provider.collectors.cloud.CloudCollector, "_get_info_from_providers"
    )
    def test_fetch(self, m_get_info):
        m_get_info.return_value = DATA.site_info
        cloud = cloud_info_provider.collectors.cloud.CloudCollector(
            self.opts, self.providers, None
        )
        self.assertIsNotNone(cloud.fetch())
        self.assertEqual(cloud.fetch(), DATA.site_info)


class StorageCollectorTest(base.BaseTest):
    @mock.patch.object(
        cloud_info_provider.collectors.storage.StorageCollector,
        "_get_info_from_providers",
    )
    def test_fetch(self, m_get_info):
        m_get_info.side_effect = (DATA.storage_endpoints, DATA.site_info)
        endpoints = DATA.storage_endpoints
        static_storage_info = dict(endpoints, **DATA.site_info)
        static_storage_info.pop("endpoints")

        for endpoint in endpoints["endpoints"].values():
            endpoint.update(static_storage_info)

        info = {}
        info.update({"endpoints": endpoints})
        info.update({"static_storage_info": static_storage_info})

        storage = cloud_info_provider.collectors.storage.StorageCollector(
            self.opts, self.providers, None
        )
        self.assertIsNotNone(storage.fetch())

    @mock.patch.object(
        cloud_info_provider.collectors.storage.StorageCollector,
        "_get_info_from_providers",
    )
    def test_fetch_empty(self, m_get_info):
        m_get_info.side_effect = ({}, DATA.site_info)
        storage = cloud_info_provider.collectors.storage.StorageCollector(
            self.opts, self.providers, None
        )
        self.assertEqual({}, storage.fetch())


class ComputeCollectorTest(base.BaseTest):
    @mock.patch.object(
        cloud_info_provider.collectors.compute.ComputeCollector,
        "_get_info_from_providers",
    )
    def test_fetch(self, m_get_info):
        def get_info_side_effect(what, **kwargs):
            data_mapping = {
                "get_site_info": DATA.site_info,
                "get_compute_shares": DATA.compute_shares,
                "get_compute_share": {},
                "get_compute_endpoints": DATA.compute_endpoints,
                "get_images": DATA.compute_images,
                "get_templates": DATA.compute_templates,
                "get_instances": {},
                "get_compute_quotas": {},
            }
            return data_mapping[what]

        m_get_info.side_effect = get_info_side_effect
        endpoints = DATA.compute_endpoints
        static_compute_info = dict(endpoints, **DATA.site_info)
        static_compute_info.pop("endpoints")
        templates = DATA.compute_templates
        images = DATA.compute_images
        shares = DATA.compute_shares

        for endpoint in endpoints["endpoints"].values():
            endpoint.update(static_compute_info)

        for template in templates.values():
            template.update(static_compute_info)

        for image in images.values():
            image.update(static_compute_info)

        for share in shares.values():
            share.update(
                {
                    "endpoints": endpoints,
                    "images": images,
                    "templates": templates,
                    "instances": {},
                    "quotas": {},
                }
            )

        info = {}
        info.update({"static_compute_info": static_compute_info})
        info.update({"shares": shares})

        compute = cloud_info_provider.collectors.compute.ComputeCollector(
            self.opts, self.providers, None
        )
        self.assertIsNotNone(compute.fetch())

    @mock.patch.object(
        cloud_info_provider.collectors.compute.ComputeCollector,
        "_get_info_from_providers",
    )
    def test_fetch_empty(self, m_get_info):
        m_get_info.side_effect = (
            DATA.site_info,
            DATA.compute_shares,
            {},
            DATA.site_info,
            DATA.compute_shares,
            {},
        )
        compute = cloud_info_provider.collectors.compute.ComputeCollector(
            self.opts, self.providers, None
        )
        self.assertFalse(compute.fetch())
        self.assertEqual({}, compute.fetch())

    @mock.patch.object(
        cloud_info_provider.collectors.compute.ComputeCollector,
        "_get_info_from_providers",
    )
    def test_fetch_error_ignored(self, m_get_info):
        m_get_info.side_effect = (
            DATA.site_info,
            DATA.compute_shares,
            CloudInfoException(),
            CloudInfoException(),
            DATA.site_info,
            DATA.compute_shares,
            CloudInfoException(),
            CloudInfoException(),
        )
        self.opts.ignore_share_errors = True
        compute = cloud_info_provider.collectors.compute.ComputeCollector(
            self.opts, self.providers, None
        )
        self.assertFalse(compute.fetch())
        self.assertEqual({}, compute.fetch())

    @mock.patch.object(
        cloud_info_provider.collectors.compute.ComputeCollector,
        "_get_info_from_providers",
    )
    def test_fetch_error(self, m_get_info):
        m_get_info.side_effect = (
            DATA.site_info,
            DATA.compute_shares,
            CloudInfoException(),
        )
        self.opts.ignore_share_errors = False
        compute = cloud_info_provider.collectors.compute.ComputeCollector(
            self.opts, self.providers, None
        )
        self.assertRaises(CloudInfoException, compute.fetch)
