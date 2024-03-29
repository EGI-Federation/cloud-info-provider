import os.path

import yaml


class Data(object):
    @property
    def site_info(self):
        return {
            "suffix": "o=glue",
            "site_name": "SITE_NAME",
            "site_is_public": False,
        }

    @property
    def storage_endpoints(self):
        return {
            "endpoints": {
                "https://storage-service01.example.org:8080": {
                    "storage_api_authn_method": "X509-VOMS",
                    "storage_api_endpoint_technology": "REST",
                    "storage_api_type": "CDMI",
                    "storage_api_version": "1.0.1",
                    "storage_production_level": "production",
                },
                "https://storage-service02.example.org:8080": {
                    "storage_api_authn_method": "X509-VOMS",
                    "storage_api_endpoint_technology": "REST",
                    "storage_api_type": "CDMI",
                    "storage_api_version": "1.0.1",
                    "storage_production_level": "testing",
                },
            },
            "storage_capabilities": ["cloud.data.upload"],
            "storage_middleware": "A Middleware",
            "storage_middleware_developer": "Middleware Developer",
            "storage_middleware_version": "v1.0",
            "storage_oidc_auth_enabled": None,
            "storage_total_storage": 0,
            "storage_service_production_level": "production",
            "storage_service_name": "example.org",
        }

    @property
    def compute_endpoints(self):
        return {
            "compute_capabilities": [
                "executionmanagement.dynamicvmdeploy",
                "security.accounting",
            ],
            "compute_hypervisor": "Foo Hypervisor",
            "compute_hypervisor_version": "0.42",
            "compute_failover": False,
            "compute_vm_backup_restore": False,
            "compute_live_migration": False,
            "compute_min_accelerators": 0,
            "compute_max_accelerators": 0,
            "compute_total_accelerators": 0,
            "compute_min_dedicated_ram": 0,
            "compute_max_dedicated_ram": 0,
            "compute_total_cores": 0,
            "compute_total_ram": 0,
            "compute_service_production_level": "production",
            "compute_service_name": "example.org",
            "endpoints": {
                "https://cloud-service01.example.org:8787": {
                    "compute_endpoint_url": "https://cloud-service01.example.org:8787",
                    "compute_api_authn_method": "X509-VOMS",
                    "compute_api_endpoint_technology": "webservice",
                    "compute_api_type": "OCCI",
                    "compute_production_level": "unknown",
                    "compute_api_version": "v2",
                    "compute_occi_api_version": "1.1",
                    "compute_occi_middleware_version": "0.3.2",
                    "compute_middleware": "OpenStack",
                    "compute_middleware_developer": "OpenStack",
                    "compute_middleware_version": "Liberty",
                },
                "https://cloud-service02.example.org:8787": {
                    "compute_endpoint_url": "https://cloud-service02.example.org:8787",
                    "compute_api_authn_method": "X509",
                    "compute_api_endpoint_technology": "webservice",
                    "compute_api_type": "OCCI",
                    "compute_production_level": "testing",
                    "compute_api_version": "v2",
                    "compute_occi_api_version": "1.1",
                    "compute_occi_middleware_version": "0.3.2",
                    "compute_middleware": "OpenStack",
                    "compute_middleware_developer": "OpenStack",
                    "compute_middleware_version": "Liberty",
                },
                "https://cloud-service03.example.org:8787": {
                    "compute_endpoint_url": "https://cloud-service03.example.org:8787",
                    "compute_api_authn_method": "User/Password",
                    "compute_api_endpoint_technology": "webservice",
                    "compute_api_type": "OCCI",
                    "compute_production_level": "unknown",
                    "compute_api_version": "v2",
                    "compute_occi_api_version": "1.1",
                    "compute_occi_middleware_version": "0.3.2",
                    "compute_middleware": "OpenStack",
                    "compute_middleware_developer": "OpenStack",
                    "compute_middleware_version": "Liberty",
                },
            },
        }

    @property
    def compute_images(self):
        return {
            "os_tpl#foobarid": {
                "image_name": "Foo Image",
                "image_version": 1.0,
                "image_marketplace_id": (
                    "http://url.to.marketplace.id.example.org/foo/bar"
                ),
                "image_os_family": "linux",
                "image_os_name": "Cirros",
                "image_os_version": 1.0,
                "image_platform": "amd64",
            },
        }

    @property
    def compute_templates(self):
        return {
            "resource_tpl#extra_large": {
                "template_cpu": 8,
                "template_memory": 16384,
                "template_network": "public",
                "template_platform": "amd64",
            },
            "resource_tpl#large": {
                "template_cpu": 4,
                "template_memory": 8196,
                "template_network": "public",
                "template_platform": "amd64",
            },
            "resource_tpl#medium": {
                "template_cpu": 2,
                "template_memory": 4096,
                "template_network": "public",
                "template_platform": "amd64",
            },
            "resource_tpl#small": {
                "template_cpu": 1,
                "template_memory": 1024,
                "template_network": "public",
                "template_platform": "amd64",
            },
        }

    @property
    def compute_shares(self):
        return {
            "fedcloud.egi.eu": {
                "sla": "https://egi.eu/sla/fedcloud",
                "auth": {"project_id": "fedcloud"},
            },
            "training.egi.eu": {
                "sla": "https://egi.eu/sla/training",
                "auth": {"project_id": "training"},
            },
        }


DATA = Data()


class OpenStackFakes(object):
    def __init__(self):
        class Flavor(object):
            def __init__(
                self,
                id,
                name,
                ram,
                vcpus,
                is_public,
                disk,
                ephemeral,
                infiniband=None,
                gpu_number=None,
            ):
                self.id = id
                self.name = name
                self.ram = ram
                self.vcpus = vcpus
                self.is_public = is_public
                self.disk = disk
                self.ephemeral = ephemeral
                self.infiniband = infiniband
                self.gpu_number = gpu_number

            def get_keys(self):
                return vars(self)

        flavors = (
            {
                "id": 1,
                "name": "m1.foo",
                "ram": 10,
                "vcpus": 20,
                "is_public": True,
                "disk": 0,
                "ephemeral": 10,
                "infiniband": "true",
            },
            {
                "id": 2,
                "name": "m1 bar",
                "ram": 20,
                "vcpus": 30,
                "is_public": False,
                "disk": 10,
                "ephemeral": 10,
                "gpu_number": 23,
            },
            {
                "id": 3,
                "name": "m1.baz",
                "ram": 2,
                "vcpus": 3,
                "is_public": True,
                "disk": 5,
                "ephemeral": 10,
            },
        )

        self.flavors = [Flavor(**f) for f in flavors]

        # XXX add docker information
        # XXX some fake images should include more information from AppDB
        self.images = (
            {
                "name": "fooimage",
                "id": "foo.id",
                "metadata": {},
                "file": "v2/foo.id/file",
                "marketplace": "http://example.org/",
                "APPLIANCE_ATTRIBUTES": '{"ad:base_mpuri": "foobar"}',
                "gpu_driver": "driver-x",
                "gpu_cuda": "CUDA_x.y",
            },
            {
                "name": "barimage",
                "id": "bar id",
                "metadata": {},
                "file": "v2/bar id/file",
            },
            {
                "name": "bazimage",
                "id": "baz id",
                "docker_id": "sha1:xxxxxxxxxxxxxxxxxxxxxxxxxx",
                "docker_tag": "latest",
                "docker_name": "test/image",
                "file": "v2/baz id/file",
            },
        )

        class Catalog(object):
            @staticmethod
            def _format_catalog_entry(name, type_, id_, url, interface):
                service = {
                    type_: [
                        {
                            "url": url,
                            "interface": interface,
                            "region": "RegionOne",
                            "region_id": "RegionOne",
                            "id": id_,
                        }
                    ]
                }
                return service

            def get_endpoints(
                self, service_type=None, interface=None, region_name=None
            ):
                if service_type == "occi":
                    return self._format_catalog_entry(
                        "occi",
                        "occi",
                        "03e087c8fb3b495c9a360bcba3abf914",
                        "https://cloud.example.org:8787/",
                        interface,
                    )
                elif service_type == "compute":
                    return self._format_catalog_entry(
                        "nova",
                        "compute",
                        "1b7f14c87d8c42ad962f4d3a5fd13a77",
                        "https://cloud.example.org:8774/v1.1/ce2d",
                        interface,
                    )

        self.catalog = Catalog()


OS_FAKES = OpenStackFakes()


class OpenNebulaFakes(object):
    def __init__(self):
        cwd = os.path.dirname(__file__)
        self.rocci_dir = os.path.join(cwd, "rocci_samples", "resource_tpl")
        sdir = os.path.join(cwd, "one_samples")

        with open(os.path.join(sdir, "one.imagepool.xml"), "r") as f:
            self.imagepool = f.read()

        with open(os.path.join(sdir, "one.templatepool.xml"), "r") as f:
            self.templatepool = f.read()

        with open(os.path.join(sdir, "one.documentpool.xml"), "r") as f:
            self.documentpool = f.read()

        self.opennebula_base_provider_expected_images = {}
        self.opennebula_rocci_provider_expected_images = {}
        self.opennebula_rocci_provider_expected_templates = {}
        self.opennebula_rocci_provider_expected_templates_remote = {}
        self.indigo_on_provider_expected_images = {}
        self.indigo_on_provider_expected_templates = {}

        files_attrs = [
            (
                "opennebula_base_provider_images.json",
                "opennebula_base_provider_expected_images",
            ),
            (
                "opennebula_rocci_provider_images.json",
                "opennebula_rocci_provider_expected_images",
            ),
            (
                "opennebula_rocci_provider_templates.json",
                "opennebula_rocci_provider_expected_templates",
            ),
            (
                "opennebula_rocci_provider_templates_remote.json",
                "opennebula_rocci_provider_expected_templates_remote",
            ),
            ("indigo_on_provider_images.json", "indigo_on_provider_expected_images"),
            (
                "indigo_on_provider_templates.json",
                "indigo_on_provider_expected_templates",
            ),
        ]

        for fname, attr_name in files_attrs:
            with open(os.path.join(sdir, fname), "r") as f:
                data = yaml.safe_load(f)
                setattr(self, attr_name, data)


ONE_FAKES = OpenNebulaFakes()
