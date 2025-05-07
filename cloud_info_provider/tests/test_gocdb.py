import mock
from cloud_info_provider.providers import utils
from cloud_info_provider.tests import base

sample_goc_response = """<?xml version="1.0" encoding="UTF-8"?>
<results>
    <SERVICE_ENDPOINT PRIMARY_KEY="1234G0">
        <PRIMARY_KEY>1234G0</PRIMARY_KEY>
        <HOSTNAME>simple.example.com</HOSTNAME>
        <SERVICE_TYPE>org.openstack.nova</SERVICE_TYPE>
        <CORE></CORE>
        <IN_PRODUCTION>Y</IN_PRODUCTION>
        <NODE_MONITORED>Y</NODE_MONITORED>
        <NOTIFICATIONS>Y</NOTIFICATIONS>
        <SITENAME>FOO-BAR-SITE</SITENAME>
        <COUNTRY_NAME>Spain</COUNTRY_NAME>
        <COUNTRY_CODE>ES</COUNTRY_CODE>
        <ROC_NAME>NGI_IBERGRID</ROC_NAME>
        <URL>https://keystone.example.com:5000/v2.0/?image=18d99a06-c3e5-4157-a0e3-37ec34bdfc24&amp;resource=m1.tiny</URL>
        <ENDPOINTS/>
  </SERVICE_ENDPOINT>
</results>"""

sample_goc_ep_response = """<?xml version="1.0" encoding="UTF-8"?>
<results>
  <SERVICE_ENDPOINT PRIMARY_KEY="00000G0">
    <PRIMARY_KEY>00000G0</PRIMARY_KEY>
    <HOSTNAME>www.baz.example.com</HOSTNAME>
    <GOCDB_PORTAL_URL>https://goc.egi.eu/portal/index.php?Page_Type=Service&amp;id=14541</GOCDB_PORTAL_URL>
    <BETA>N</BETA>
    <SERVICE_TYPE>org.openstack.nova</SERVICE_TYPE>
    <CORE/>
    <IN_PRODUCTION>Y</IN_PRODUCTION>
    <NODE_MONITORED>Y</NODE_MONITORED>
    <NOTIFICATIONS>Y</NOTIFICATIONS>
    <SITENAME>BAR-FOO-SITE</SITENAME>
    <COUNTRY_NAME>Ireland</COUNTRY_NAME>
    <COUNTRY_CODE>IE</COUNTRY_CODE>
    <ROC_NAME>NGI_IE</ROC_NAME>
    <URL/>
    <ENDPOINTS>
      <ENDPOINT>
        <ID>8282</ID>
        <NAME>Name-it</NAME>
        <EXTENSIONS/>
        <URL>https://horizon.baz.example.com:5000/v3</URL>
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
            r = utils.find_in_gocdb("foo", "bar")
            m_requests.assert_called_once_with(
                "https://goc.egi.eu/gocdbpi/public/",
                params={"method": "get_service", "service_type": "bar"},
                verify=True,
                timeout=None,
            )
            assert {} == r

    def test_request_call_insecure(self):
        with mock.patch("requests.get") as m_requests:
            m_requests.return_value = mock.MagicMock()
            r = utils.find_in_gocdb("foo", "bar", insecure=True)
            m_requests.assert_called_once_with(
                "https://goc.egi.eu/gocdbpi/public/",
                params={"method": "get_service", "service_type": "bar"},
                verify=False,
                timeout=None,
            )
            assert {} == r

    def test_request_call_timeout(self):
        with mock.patch("requests.get") as m_requests:
            m_requests.return_value = mock.MagicMock()
            r = utils.find_in_gocdb("foo", "bar", timeout=1234)
            m_requests.assert_called_once_with(
                "https://goc.egi.eu/gocdbpi/public/",
                params={"method": "get_service", "service_type": "bar"},
                verify=True,
                timeout=1234,
            )
            assert {} == r

    def test_goc_non_200(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 404
            m_requests.return_value = r
            assert {} == utils.find_in_gocdb("foo", "bar")

    def test_goc_empty(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 200
            r.text = '<?xml version="1.0" encoding="UTF-8"?>' "<results/>"
            m_requests.return_value = r
            assert {} == utils.find_in_gocdb("foo", "bar")

    def test_goc_not_found(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 200
            r.text = sample_goc_response
            m_requests.return_value = r
            assert {} == utils.find_in_gocdb("foo", "bar")

    def test_goc_found_same_path(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 200
            r.text = sample_goc_response
            m_requests.return_value = r
            expected = {"gocdb_id": "1234G0", "site_name": "FOO-BAR-SITE"}
            assert expected == utils.find_in_gocdb(
                "https://keystone.example.com:5000/v2.0/", "bar"
            )

    def test_goc_found_similar_path(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 200
            r.text = sample_goc_response
            m_requests.return_value = r
            expected = {"gocdb_id": "1234G0", "site_name": "FOO-BAR-SITE"}
            assert expected == utils.find_in_gocdb(
                "https://keystone.example.com:5000/v2.0", "bar"
            )

    def test_goc_multiple_endpoints(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 200
            r.text = sample_goc_ep_response
            m_requests.return_value = r
            expected = {"gocdb_id": "00000G0", "site_name": "BAR-FOO-SITE"}
            assert expected == utils.find_in_gocdb(
                "https://horizon.baz.example.com:5000/v3", "bar"
            )
