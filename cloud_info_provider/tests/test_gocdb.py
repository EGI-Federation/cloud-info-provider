import mock
from cloud_info_provider.providers import gocdb
from cloud_info_provider.tests import base

sample_goc_response = """<?xml version="1.0" encoding="UTF-8"?>
<results>
    <SERVICE_ENDPOINT PRIMARY_KEY="7513G0">
        <PRIMARY_KEY>7513G0</PRIMARY_KEY>
        <HOSTNAME>nova.cloud.ifca.es</HOSTNAME>
        <SERVICE_TYPE>org.openstack.nova</SERVICE_TYPE>
        <CORE></CORE>
        <IN_PRODUCTION>Y</IN_PRODUCTION>
        <NODE_MONITORED>Y</NODE_MONITORED>
        <NOTIFICATIONS>Y</NOTIFICATIONS>
        <SITENAME>IFCA-LCG2</SITENAME>
        <COUNTRY_NAME>Spain</COUNTRY_NAME>
        <COUNTRY_CODE>ES</COUNTRY_CODE>
        <ROC_NAME>NGI_IBERGRID</ROC_NAME>
        <URL>https://keystone.ifca.es:5000/v2.0/?image=18d99a06-c3e5-4157-a0e3-37ec34bdfc24&amp;resource=m1.tiny</URL>
        <ENDPOINTS/>
  </SERVICE_ENDPOINT>
</results>"""

sample_goc_ep_response = """<?xml version="1.0" encoding="UTF-8"?>
<results>
  <SERVICE_ENDPOINT PRIMARY_KEY="14541G0">
    <PRIMARY_KEY>14541G0</PRIMARY_KEY>
    <HOSTNAME>www.waltoncloud.eu</HOSTNAME>
    <GOCDB_PORTAL_URL>https://goc.egi.eu/portal/index.php?Page_Type=Service&amp;id=14541</GOCDB_PORTAL_URL>
    <BETA>N</BETA>
    <SERVICE_TYPE>org.openstack.nova</SERVICE_TYPE>
    <CORE/>
    <IN_PRODUCTION>Y</IN_PRODUCTION>
    <NODE_MONITORED>Y</NODE_MONITORED>
    <NOTIFICATIONS>Y</NOTIFICATIONS>
    <SITENAME>WALTON-CLOUD</SITENAME>
    <COUNTRY_NAME>Ireland</COUNTRY_NAME>
    <COUNTRY_CODE>IE</COUNTRY_CODE>
    <ROC_NAME>NGI_IE</ROC_NAME>
    <URL/>
    <ENDPOINTS>
      <ENDPOINT>
        <ID>8282</ID>
        <NAME>WaltonDiscovery</NAME>
        <EXTENSIONS/>
        <URL>https://horizon.waltoncloud.eu:5000/v3</URL>
        <INTERFACENAME>org.openstack.nova</INTERFACENAME>
        <ENDPOINT_MONITORED>Y</ENDPOINT_MONITORED>
      </ENDPOINT>
    </ENDPOINTS>
    <SCOPES>
      <SCOPE>EGI</SCOPE>
    </SCOPES>
    <EXTENSIONS/>
  </SERVICE_ENDPOINT>
</results>"""


class GOCDBTest(base.TestCase):
    def test_request_call(self):
        with mock.patch("requests.get") as m_requests:
            m_requests.return_value = mock.MagicMock()
            r = gocdb.find_in_gocdb("foo", "bar")
            m_requests.assert_called_once_with(
                "https://goc.egi.eu/gocdbpi/public/",
                params={"method": "get_service", "service_type": "bar"},
                verify=True,
                timeout=None,
            )
            self.assertEqual({}, r)

    def test_request_call_insecure(self):
        with mock.patch("requests.get") as m_requests:
            m_requests.return_value = mock.MagicMock()
            r = gocdb.find_in_gocdb("foo", "bar", insecure=True)
            m_requests.assert_called_once_with(
                "https://goc.egi.eu/gocdbpi/public/",
                params={"method": "get_service", "service_type": "bar"},
                verify=False,
                timeout=None,
            )
            self.assertEqual({}, r)

    def test_request_call_timeout(self):
        with mock.patch("requests.get") as m_requests:
            m_requests.return_value = mock.MagicMock()
            r = gocdb.find_in_gocdb("foo", "bar", timeout=1234)
            m_requests.assert_called_once_with(
                "https://goc.egi.eu/gocdbpi/public/",
                params={"method": "get_service", "service_type": "bar"},
                verify=True,
                timeout=1234,
            )
            self.assertEqual({}, r)

    def test_goc_non_200(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 404
            m_requests.return_value = r
            self.assertEqual({}, gocdb.find_in_gocdb("foo", "bar"))

    def test_goc_empty(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 200
            r.text = '<?xml version="1.0" encoding="UTF-8"?>' "<results/>"
            m_requests.return_value = r
            self.assertEqual({}, gocdb.find_in_gocdb("foo", "bar"))

    def test_goc_not_found(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 200
            r.text = sample_goc_response
            m_requests.return_value = r
            self.assertEqual({}, gocdb.find_in_gocdb("foo", "bar"))

    def test_goc_found_same_path(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 200
            r.text = sample_goc_response
            m_requests.return_value = r
            expected = {"gocdb_id": "7513G0", "site_name": "IFCA-LCG2"}
            self.assertEqual(
                expected,
                gocdb.find_in_gocdb("https://keystone.ifca.es:5000/v2.0/", "bar"),
            )

    def test_goc_found_similar_path(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 200
            r.text = sample_goc_response
            m_requests.return_value = r
            expected = {"gocdb_id": "7513G0", "site_name": "IFCA-LCG2"}
            self.assertEqual(
                expected,
                gocdb.find_in_gocdb("https://keystone.ifca.es:5000/v2.0", "bar"),
            )

    def test_goc_multiple_endpoints(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 200
            r.text = sample_goc_ep_response
            m_requests.return_value = r
            expected = {"gocdb_id": "14541G0", "site_name": "WALTON-CLOUD"}
            self.assertEqual(
                expected,
                gocdb.find_in_gocdb("https://horizon.waltoncloud.eu:5000/v3", "bar"),
            )
