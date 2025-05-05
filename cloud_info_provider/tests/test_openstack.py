import argparse

import mock
from cloud_info_provider import glue
from cloud_info_provider.providers import openstack as os_provider
from cloud_info_provider.tests import base, data
from cloud_info_provider.tests import utils as utils
from cloud_info_provider.tests.utils import compare_glue

FAKES = data.OS_FAKES


class OpenStackProviderOptionsTest(base.TestCase):
    def test_populate_parser(self):
        parser = argparse.ArgumentParser(conflict_handler="resolve")
        provider = os_provider.OpenStackProvider
        provider.populate_parser(parser)

        opts = parser.parse_args(
            [
                "--os-username",
                "foo",
                "--os-password",
                "bar",
                "--os-auth-url",
                "http://example.org:5000",
                "--insecure",
                "--all-images",
                "--select-flavors",
                "public",
                "--os-region",
                "North pole",
                "site_config",
            ]
        )

        self.assertEqual(opts.os_username, "foo")
        self.assertEqual(opts.os_password, "bar")
        self.assertEqual(opts.os_auth_url, "http://example.org:5000")
        self.assertEqual(opts.os_region, "North pole")
        self.assertEqual(opts.insecure, True)
        self.assertEqual(opts.all_images, True)
        self.assertEqual(opts.select_flavors, "public")


class OpenStackProviderAuthTest(base.TestCase):
    # Do not limit diff output on failures
    maxDiff = None

    def setUp(self):
        super(OpenStackProviderAuthTest, self).setUp()

        class FakeProvider(os_provider.OpenStackProvider):
            def __init__(self, opts):
                self.project_id = None
                self.os_region = None
                self.opts = mock.Mock()

        self.provider = FakeProvider(None)

    def test_rescope_simple(self):
        with utils.nested(
            mock.patch("keystoneauth1.loading." "load_auth_from_argparse_arguments"),
            mock.patch("keystoneauth1.loading." "load_session_from_argparse_arguments"),
        ) as (_, m_load_session):
            session = mock.Mock()
            session.get_project_id.return_value = "foo"
            m_load_session.return_value = session
            auth = {"project_id": "foo", "vo": "bar"}
            self.provider.rescope_project(auth)
            self.assertEqual("foo", self.provider.project_id)


class OpenStackProviderTest(base.TestCase):
    # Do not limit diff output on failures
    maxDiff = None

    def setUp(self):
        super(OpenStackProviderTest, self).setUp()

        class FakeProvider(os_provider.OpenStackProvider):
            def rescope_project(self, auth):
                self.project_id = auth["project_id"]

            def __init__(self, opts):
                self.nova = mock.Mock()
                self.glance = mock.Mock()
                self.glance.http_client.get_endpoint.return_value = (
                    "http://glance.example.org:9292/v2"
                )
                self.session = mock.Mock()
                self.project_id = None
                self.session.get_project_id.return_value = "TEST_PROJECT_ID"
                self.auth_plugin = mock.MagicMock()
                self.auth_plugin.auth_url = data.DATA.endpoint_url
                self.insecure = False
                self.os_region = None
                self.select_flavors = "all"
                self.all_images = False
                self.flavor_properties = {
                    "infiniband": {"key": "infiniband", "value": "true"},
                    "flavor_gpu_number": {"key": "gpu_number", "value": None},
                }
                self.image_properties = {
                    "image_gpu_driver": {"key": "gpu_driver", "value": "true"},
                    "image_gpu_cuda": {"key": "gpu_cuda", "value": "true"},
                }
                self.site_config = data.DATA.site_config
                self.service = glue.CloudComputingService(id="foo", status_info="ok")
                self.endpoint = glue.CloudComputingEndpoint(
                    id="bar",
                    interface_name="iface",
                    url="url",
                )
                self.manager = glue.CloudComputingManager(id="baz")
                self._goc_info = {data.DATA.endpoint_url: {"foo": "bar"}}
                self._ca_info = {data.DATA.endpoint_url: {"foo": "bar"}}

        self.provider = FakeProvider(None)

    def test_get_service(self):
        service = {
            "site_name": data.DATA.site_name,
            "name": f"Cloud Compute service at {data.DATA.site_name}",
            "other_info": {"foo": "bar"},
            "associations": {"AdminDomain": [data.DATA.site_name]},
            "status_info": f"https://argo.egi.eu/egi/report-status/Critical/SITES/{data.DATA.site_name}",
            "capability": [
                "executionmanagement.dynamicvmdeploy",
                "security.accounting",
            ],
            "type": "org.cloud.iaas",
            "id": "https://foo.example.org:5000/v3_cloud.compute",
            "quality_level": "production",
            "service_aup": "http://go.egi.eu/aup",
        }
        assert compare_glue(service, self.provider.get_service())

    def test_provider_get_endpoint(self):
        class Version:
            version = "vy.x"

        self.provider.nova.versions.get_current.return_value = Version()
        self.provider.nova.api_version.get_string.return_value = "vx.y"
        endpoint = {
            "id": "https://foo.example.org:5000/v3_OpenStack_v3_oidc",
            "url": "https://foo.example.org:5000/v3",
            "name": "Cloud computing endpoint for https://foo.example.org:5000/v3_OpenStack_v3_oidc",
            "associations": {"CloudComputingService": ["foo"]},
            "capability": [],
            "quality_level": "production",
            "serving_state": "production",
            "interface_name": "org.openstack.nova",
            "interface_version": "vx.y",
            "implementor": "OpenStack Foundation",
            "implementation_name": "OpenStack Nova",
            "implementation_version": "vy.x",
            "semantics": "https://developer.openstack.org/api-ref/compute",
            "health_state": "ok",
            "health_state_info": "Endpoint funtioning properly",
            "technology": "webservice",
            "authentication": "oidc",
            "downtime_info": "https://goc.egi.eu/portal/index.php?Page_Type=Downtimes_Calendar&site=SITE_NAME",
        }
        assert compare_glue(endpoint, self.provider.get_endpoint())

    def test_build_image(self):
        share = glue.Share(id="share")
        objs = self.provider.build_image(FAKES.images[0], share)
        assert len(objs) == 1
        assert compare_glue(
            {
                "id": "foo.id",
                "name": "fooimage",
                "other_info": {"base_mpuri": "foobar"},
                "associations": {
                    "Share": ["share"],
                    "CloudComputingEndpoint": ["bar"],
                    "CloudComputingManager": ["baz"],
                },
                "marketplace_url": "http://example.org/",
                "osPlatform": "UNKNOWN",
                "osName": "UNKNOWN",
                "osVersion": "UNKNOWN",
                "description": "UNKNOWN",
                "access_info": "none",
            },
            objs[0],
        )

    def test_get_images(self):
        self.provider.all_images = True
        self.provider.glance.images.list.return_value = FAKES.images
        share = glue.Share(id="share")
        images = self.provider.get_share_images(share)
        expected_images = {"bar id", "foo.id", "baz id"}
        assert expected_images == {i.id for i in images}
        self.provider.all_images = False
        images = self.provider.get_share_images(share)
        expected_images = {"foo.id"}
        assert expected_images == {i.id for i in images}

    def test_build_instance_type(self):
        share = glue.Share(id="share")
        objs = self.provider.build_instance_type(FAKES.flavors[0], share)
        assert len(objs) == 1
        assert compare_glue(
            {
                "id": "1",
                "name": "m1.foo",
                "associations": {
                    "Share": ["share"],
                    "CloudComputingEndpoint": ["bar"],
                    "CloudComputingManager": ["baz"],
                },
                "platform": "amd64",
                "cpu": 20,
                "ram": 10,
                "disk": 0,
                "network_in": "UNKNOWN",
                "network_out": True,
            },
            objs[0],
        )

    def test_build_instance_type_gpu(self):
        share = glue.Share(id="share")
        objs = self.provider.build_instance_type(FAKES.flavors[1], share)
        assert len(objs) == 2
        for o in objs:
            if isinstance(o, glue.CloudComputingInstanceType):
                assert compare_glue(
                    {
                        "id": "2",
                        "name": "m1 bar",
                        "associations": {
                            "Share": ["share"],
                            "CloudComputingEndpoint": ["bar"],
                            "CloudComputingManager": ["baz"],
                            "CloudComputingVirtualAccelerator": ["2_gpu"],
                        },
                        "platform": "amd64",
                        "cpu": 30,
                        "ram": 20,
                        "disk": 10,
                        "network_in": "UNKNOWN",
                        "network_out": True,
                    },
                    o,
                )
            elif isinstance(o, glue.CloudComputingVirtualAccelerator):
                assert compare_glue(
                    {
                        "id": "2_gpu",
                        "name": "m1 bar_gpu",
                        "associations": {"CloudComputingInstanceType": ["2"]},
                        "compute_capability": [],
                        "type": "GPU",
                        "number": 23,
                        "vendor": "UNKNOWN",
                        "model": "UNKNOWN",
                    },
                    o,
                )

    def test_get_instances(self):
        # all
        self.provider.select_flavors = "all"
        self.provider.nova.flavors.list.return_value = FAKES.flavors
        share = glue.Share(id="share")
        itypes = self.provider.get_share_instance_types(share)
        expected_types = {"1", "2", "3", "2_gpu"}
        assert expected_types == {i.id for i in itypes}
        assert share.instance_max_ram == 20
        assert share.instance_min_ram == 2
        assert share.instance_max_cpu == 30
        assert share.instance_min_cpu == 3
        # public
        self.provider.select_flavors = "public"
        itypes = self.provider.get_share_instance_types(share)
        expected_types = {"1", "3"}
        assert expected_types == {i.id for i in itypes}
        assert share.instance_max_ram == 10
        assert share.instance_min_ram == 2
        assert share.instance_max_cpu == 20
        assert share.instance_min_cpu == 3
        # private
        self.provider.select_flavors = "private"
        itypes = self.provider.get_share_instance_types(share)
        expected_types = {"2", "2_gpu"}
        assert expected_types == {i.id for i in itypes}
        assert share.instance_max_ram == 20
        assert share.instance_min_ram == 20
        assert share.instance_max_cpu == 30
        assert share.instance_min_cpu == 30

    def test_get_quotas(self):
        self.provider.nova.servers.list.return_value = FAKES.servers
        self.provider.nova.quotas.get.return_value = FAKES.quotas
        share = glue.Share(id="share")
        instance_types = [glue.CloudComputingInstanceType(id="foo", cpu=1, ram=4)]
        self.provider.get_share_quotas(share, instance_types)
        assert share.running_vm == 3
        assert share.halted_vm == 1
        assert share.suspended_vm == 4
        assert share.total_vm == 8
        assert share.max_vm == 4
        assert share.other_info["quotas"] == FAKES.quotas.get_dict()

    def test_get_shares(self):
        self.provider.glance.images.list.return_value = FAKES.images
        self.provider.nova.flavors.list.return_value = FAKES.flavors
        self.provider.nova.servers.list.return_value = FAKES.servers
        self.provider.nova.quotas.get.return_value = FAKES.quotas
        self.provider.auth_plugin.get_access.return_value = FAKES.access
        objs = self.provider.get_shares()
        # 2 shares and a global policy
        # For each share:
        # 1 image, 1 mapping policy, 3 flavors, 1 virtual accelerator
        assert len(objs) == 15
        shares = [s for s in objs if isinstance(s, glue.Share)]
        assert {
            "https://foo.example.org:5000/v3_OpenStack_v3_oidc_share_foo1_bar",
            "https://foo.example.org:5000/v3_OpenStack_v3_oidc_share_foo2_baz",
        } == {s.id for s in shares}

        bar_shares = [s for s in shares if s.project_id == "bar"][0]
        assert compare_glue(
            {
                "id": "https://foo.example.org:5000/v3_OpenStack_v3_oidc_share_foo1_bar",
                "name": "Share in service https://foo.example.org:5000/v3_OpenStack_v3_oidc for VO foo1 (Project bar)",
                "other_info": {
                    "project_name": "project",
                    "project_domain_name": "default",
                    "quotas": {
                        "instances": 4,
                        "cores": 5,
                        "ram": 7,
                        "floating_ips": 1,
                        "fixed_ips": 0,
                        "metadata_items": 4,
                        "injected_files": 7,
                        "injected_file_content_bytes": 8,
                        "injected_file_path_bytes": 9,
                        "key_pairs": 10,
                        "security_groups": 1,
                        "security_group_rules": 2,
                        "server_groups": 4,
                        "server_group_members": 5,
                    },
                },
                "associations": {
                    "CloudComputingService": ["foo"],
                    "CloudComputingEndpoint": ["bar"],
                },
                "instance_max_cpu": 30,
                "instance_max_ram": 20,
                "instance_min_cpu": 3,
                "instance_min_ram": 2,
                "total_vm": 8,
                "running_vm": 3,
                "suspended_vm": 4,
                "halted_vm": 1,
                "max_vm": 4,
                "project_id": "bar",
            },
            bar_shares,
        )

        # check policies, assume everything else is ok
        for o in objs:
            if o.id == "bar_policy":
                assert compare_glue(
                    {
                        "id": "bar_policy",
                        "associations": {"CloudComputingEndpoint": ["bar"]},
                        "scheme": "org.glite.standard",
                        "rule": ["VO:foo1", "VO:foo2"],
                    },
                    o,
                )
            # foo1 policy
            elif (
                o.id
                == "https://foo.example.org:5000/v3_OpenStack_v3_oidc_share_foo1_bar_Policy"
            ):
                assert compare_glue(
                    {
                        "id": "https://foo.example.org:5000/v3_OpenStack_v3_oidc_share_foo1_bar_Policy",
                        "associations": {
                            "Share": [
                                "https://foo.example.org:5000/v3_OpenStack_v3_oidc_share_foo1_bar"
                            ],
                            "PolicyUserDomain": ["VO:foo1"],
                        },
                        "scheme": "org.glite.standard",
                        "rule": ["VO:foo1"],
                    },
                    o,
                )
            elif (
                o.id
                == "https://foo.example.org:5000/v3_OpenStack_v3_oidc_share_foo2_baz_Policy"
            ):
                assert compare_glue(
                    {
                        "id": "https://foo.example.org:5000/v3_OpenStack_v3_oidc_share_foo2_baz_Policy",
                        "associations": {
                            "Share": [
                                "https://foo.example.org:5000/v3_OpenStack_v3_oidc_share_foo2_baz"
                            ],
                            "PolicyUserDomain": ["VO:foo2"],
                        },
                        "scheme": "org.glite.standard",
                        "rule": ["VO:foo2"],
                    },
                    o,
                )
