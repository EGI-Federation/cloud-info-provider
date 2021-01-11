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
  </SERVICE_ENDPOINT>'
</results>"""


class GOCDBTest(base.TestCase):
    def test_request_call(self):
        with mock.patch("requests.get") as m_requests:
            m_requests.return_value = mock.MagicMock()
            r = gocdb.get_from_gocdb(method="get_service", service_type="bar")
            m_requests.assert_called_once_with(
                "https://goc.egi.eu/gocdbpi/public/",
                params={"method": "get_service", "service_type": "bar"},
                verify=True,
            )
            self.assertEqual({}, r)

    def test_request_call_insecure(self):
        with mock.patch("requests.get") as m_requests:
            m_requests.return_value = mock.MagicMock()
            r = gocdb.get_from_gocdb(
                method="get_service",
                service_type="bar",
                insecure=True)
            m_requests.assert_called_once_with(
                "https://goc.egi.eu/gocdbpi/public/",
                params={"method": "get_service", "service_type": "bar"},
                verify=False,
            )
            self.assertEqual({}, r)

    def test_goc_non_200(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 404
            m_requests.return_value = r
            self.assertEqual({}, gocdb.get_from_gocdb(method="get_service",
                                                      service_type="bar"))

    def test_goc_empty(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 200
            r.text = '<?xml version="1.0" encoding="UTF-8"?>' "<results/>"
            m_requests.return_value = r
            self.assertEqual(('<?xml version="1.0" encoding="UTF-8"?>'
                              '<results/>'),
                             gocdb.get_from_gocdb(method="get_service",
                                                  service_type="bar"))

    def test_goc_not_found(self):
        with mock.patch("requests.get") as m_requests:
            r = mock.MagicMock()
            r.status_code = 200
            r.text = sample_goc_response
            m_requests.return_value = r
            self.assertEqual(sample_goc_response,
                             gocdb.get_from_gocdb(method="get_service",
                                                  service_type="bar"))

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
