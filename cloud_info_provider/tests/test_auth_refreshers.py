import argparse

import mock
import requests

from cloud_info_provider.auth_refreshers import oidc_refresh
from cloud_info_provider.exceptions import RefresherException
from cloud_info_provider.tests import base


class OidcRefreshOptionsTest(base.TestCase):
    def test_populate_parser(self):
        parser = argparse.ArgumentParser(conflict_handler='resolve')
        refresher = oidc_refresh.OidcRefreshToken(None)
        refresher.populate_parser(parser)

        opts = parser.parse_args(['--oidc-token-endpoint',
                                  'http://example.org/oidc',
                                  '--oidc-client-id', 'foo',
                                  '--oidc-client-secret', 'bar',
                                  '--oidc-refresh-token', 'baz',
                                  '--oidc-scopes', 'foobar'])

        self.assertEqual("http://example.org/oidc", opts.oidc_token_endpoint)
        self.assertEqual('foo', opts.oidc_client_id)
        self.assertEqual('bar', opts.oidc_client_secret)
        self.assertEqual('baz', opts.oidc_refresh_token)
        self.assertEqual('foobar', opts.oidc_scopes)


class OidcRefreshTest(base.TestCase):
    def setUp(self):
        super(OidcRefreshTest, self).setUp()

        class FakeRefresher(oidc_refresh.OidcRefreshToken):
            def __init__(self):
                self.opts = mock.Mock()
                self.opts.oidc_token_endpoint = 'http://example.org/oidc'
                self.opts.oidc_client_id = 'foo'
                self.opts.oidc_client_secret = 'bar'
                self.opts.oidc_refresh_token = 'baz'
                self.opts.oidc_scopes = 'foobar'

        class FakeProvider(object):
            def __init__(self):
                self.opts = mock.Mock()

        self.refresher = FakeRefresher()
        self.provider = FakeProvider()

    @mock.patch('requests.post')
    def test_refresh_success(self, m_post):
        m_ret = mock.Mock()
        m_post.return_value = m_ret
        m_ret.status_code = 200
        m_ret.json.return_value = {"access_token": "a token"}
        self.refresher.refresh(self.provider)
        self.assertEqual("a token", self.provider.opts.oidcaccesstoken)
        m_post.assert_called_with('http://example.org/oidc',
                                  auth=('foo', 'bar'),
                                  data={"client_id": "foo",
                                        "client_secret": "bar",
                                        "grant_type": "refresh_token",
                                        "refresh_token": "baz",
                                        "scope": "foobar"})

    @mock.patch('requests.post')
    def test_refresh_bad_code(self, m_post):
        m_ret = mock.Mock()
        m_post.return_value = m_ret
        m_ret.status_code = 400
        self.assertRaises(RefresherException,
                          self.refresher.refresh,
                          self.provider)

    @mock.patch('requests.post')
    def test_refresh_request_exception(self, m_post):
        m_post.side_effect = requests.exceptions.RequestException
        self.assertRaises(RefresherException,
                          self.refresher.refresh,
                          self.provider)

    @mock.patch('requests.post')
    def test_refresh_no_json(self, m_post):
        m_ret = mock.Mock()
        m_post.return_value = m_ret
        m_ret.status_code = 200
        m_ret.json.side_effect = ValueError
        m_ret = mock.Mock()
        self.assertRaises(RefresherException,
                          self.refresher.refresh,
                          self.provider)

    @mock.patch('requests.post')
    def test_refresh_bad_json(self, m_post):
        m_ret = mock.Mock()
        m_post.return_value = m_ret
        m_ret.status_code = 200
        m_ret.json.return_value = {}
        m_ret = mock.Mock()
        self.assertRaises(RefresherException,
                          self.refresher.refresh,
                          self.provider)
