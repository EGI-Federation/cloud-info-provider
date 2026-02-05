import cloud_info_provider.providers.base
import mock
from cloud_info_provider import glue
from cloud_info_provider.tests import base
from cloud_info_provider.tests import utils as utils
from cloud_info_provider.tests.data import DATA


class FakeBaseProvider(cloud_info_provider.providers.base.BaseProvider):
    def _load_site_config(self, site_config):
        self.site_config = DATA.site_config


class BaseProviderTest(base.TestCase):
    def setUp(self):
        class Opts(object):
            debug = None
            timeout = 1234
            site_config = None
            insecure = None

        super().setUp()
        self.provider = FakeBaseProvider(Opts())

    def test_provider_build_service(self):
        with mock.patch(
            "cloud_info_provider.providers.utils.find_in_gocdb"
        ) as m_goc_find:
            m_goc_find.return_value = {"foo": "bar"}
            service = {
                "site_name": DATA.site_name,
                "name": f"Cloud Compute service at {DATA.site_name}",
                "other_info": {"foo": "bar"},
                "associations": {"AdminDomain": [DATA.site_name]},
                "status_info": f"https://argo.egi.eu/egi/report-status/Critical/SITES/{DATA.site_name}",
                "capability": [
                    "executionmanagement.dynamicvmdeploy",
                    "security.accounting",
                ],
                "type": "org.cloud.iaas",
                "id": "service",
                "quality_level": "production",
                "service_aup": "http://go.egi.eu/aup",
            }
            assert utils.compare_glue(service, self.provider.build_service())

    def test_provider_build_manager(self):
        self.provider.add_glue(glue.CloudComputingService(id="foo", status_info="bar"))
        manager = {"id": "manager", "associations": {"CloudComputingService": ["foo"]}}
        assert utils.compare_glue(manager, self.provider.build_manager())

    def test_provider_build_endpoint(self):
        with mock.patch(
            "cloud_info_provider.providers.utils.get_endpoint_ca_information"
        ) as m_ca_get:
            m_ca_get.return_value = {"issuer": "foo_ca", "trusted_cas": ["ca1", "ca2"]}
            self.provider.add_glue(
                glue.CloudComputingService(id="foo", status_info="bar")
            )
            endpoint = {
                "id": "endpoint",
                "name": "Cloud computing endpoint for endpoint",
                "url": "https://foo.example.org:5000/v3",
                "associations": {"CloudComputingService": ["foo"]},
                "capability": [],
                "quality_level": "production",
                "serving_state": "production",
                "interface_name": "",
                "health_state": "ok",
                "health_state_info": "Endpoint functioning properly",
                "technology": "webservice",
                "downtime_info": "https://goc.egi.eu/portal/index.php?Page_Type=Downtimes_Calendar&site=SITE_NAME",
                "issuer_ca": "foo_ca",
                "trusted_cas": ["ca1", "ca2"],
            }
            assert utils.compare_glue(endpoint, self.provider.build_endpoint())

    def test_provider_build_shares(self):
        self.provider.build_shares()
        self.provider.get_objs("Share") == []

    def test_get_goc_info_no_svc(self):
        assert self.provider._get_goc_info("baz") == {}

    def test_get_goc_info(self):
        self.provider.goc_service_type = "svc"
        with mock.patch(
            "cloud_info_provider.providers.utils.find_in_gocdb"
        ) as m_goc_find:
            m_goc_find.return_value = {"foo": "bar"}
            info = self.provider._get_goc_info("baz")
            assert self.provider._goc_info == {"baz": {"foo": "bar"}}
            assert info == {"foo": "bar"}

    def test_fetch(self):
        with utils.nested(
            mock.patch("cloud_info_provider.providers.utils.find_in_gocdb"),
            mock.patch(
                "cloud_info_provider.providers.utils.get_endpoint_ca_information"
            ),
        ) as (m_goc_find, m_ca_get):
            m_goc_find.return_value = {"foo": "bar"}
            m_ca_get.return_value = {"issuer": "foo_ca", "trusted_cas": ["ca1", "ca2"]}
            self.provider.fetch()
            # just check the complexity here
            assert self.provider.service.complexity == "endpointType=1,share=0"
            assert self.provider.manager
            assert self.provider.endpoint
