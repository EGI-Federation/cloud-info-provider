"""
Tests for the auth refreshers
"""

import argparse

import mock
import requests
from cloud_info_provider.auth_refreshers import (
    access_token,
    oidc_refresh,
    oidc_vo_refresh,
)
from cloud_info_provider.exceptions import RefresherException
from cloud_info_provider.tests import base


class AccessTokenTest(base.TestCase):
    def test_refresh(self):
        class FakeProvider(object):
            def __init__(self):
                self.opts = mock.Mock()

        provider = FakeProvider()
        refresher = access_token.AccessToken(None)
        token = "this token"
        refresher.refresh(provider, access_token=token, ignore=True)
        self.assertEqual("this token", provider.opts.os_access_token)


class OidcRefreshOptionsTest(base.TestCase):
    def test_populate_parser(self):
        """Tests that the right options are added to the argument parser"""

        parser = argparse.ArgumentParser(conflict_handler="resolve")
        refresher = oidc_refresh.OidcRefreshToken(None)
        refresher.populate_parser(parser)

        opts = parser.parse_args(
            [
                "--oidc-token-endpoint",
                "http://example.org/oidc",
                "--oidc-client-id",
                "foo",
                "--oidc-client-secret",
                "bar",
                "--oidc-refresh-token",
                "baz",
                "--oidc-scopes",
                "foobar",
            ]
        )

        self.assertEqual("http://example.org/oidc", opts.oidc_token_endpoint)
        self.assertEqual("foo", opts.oidc_client_id)
        self.assertEqual("bar", opts.oidc_client_secret)
        self.assertEqual("baz", opts.oidc_refresh_token)
        self.assertEqual("foobar", opts.oidc_scopes)


class OidcRefreshTest(base.TestCase):
    def setUp(self):
        super(OidcRefreshTest, self).setUp()

        class FakeRefresher(oidc_refresh.OidcRefreshToken):
            def __init__(self):
                self.opts = mock.Mock()
                self.opts.oidc_token_endpoint = "http://example.org/oidc"
                self.opts.oidc_client_id = "foo"
                self.opts.oidc_client_secret = "bar"
                self.opts.oidc_refresh_token = "baz"
                self.opts.oidc_scopes = "foobar"

        class FakeProvider(object):
            def __init__(self):
                self.opts = mock.Mock()

        self.refresher = FakeRefresher()
        self.provider = FakeProvider()

    @mock.patch("requests.post")
    def test_refresh_success(self, m_post):
        """Tests a successful invocation of the refresher.

        Checks that the token endpoint is called with the right parameters
        and that the provider gets its access_token updated with the value
        returned bt the endpoint
        """
        m_ret = mock.Mock()
        m_post.return_value = m_ret
        m_ret.status_code = 200
        m_ret.json.return_value = {"access_token": "a token"}
        self.refresher.refresh(self.provider)
        self.assertEqual("a token", self.provider.opts.os_access_token)
        m_post.assert_called_with(
            "http://example.org/oidc",
            auth=("foo", "bar"),
            data={
                "client_id": "foo",
                "client_secret": "bar",
                "grant_type": "refresh_token",
                "refresh_token": "baz",
                "scope": "foobar",
            },
            timeout=self.refresher.opts.timeout,
        )

    @mock.patch("requests.post")
    def test_refresh_bad_code(self, m_post):
        """Ensures exception is raised on HTTP status code != 200"""
        m_ret = mock.Mock()
        m_post.return_value = m_ret
        m_ret.status_code = 400
        self.assertRaises(RefresherException, self.refresher.refresh, self.provider)

    @mock.patch("requests.post")
    def test_refresh_request_exception(self, m_post):
        """Ensures exception is raised on requests errors"""
        m_post.side_effect = requests.exceptions.RequestException
        self.assertRaises(RefresherException, self.refresher.refresh, self.provider)

    @mock.patch("requests.post")
    def test_refresh_no_json(self, m_post):
        """Ensures exception is raised when bad json is returned"""
        m_ret = mock.Mock()
        m_post.return_value = m_ret
        m_ret.status_code = 200
        m_ret.json.side_effect = ValueError
        m_ret = mock.Mock()
        self.assertRaises(RefresherException, self.refresher.refresh, self.provider)

    @mock.patch("requests.post")
    def test_refresh_bad_json(self, m_post):
        """Ensures exception is raised json does not contain access_token"""
        m_ret = mock.Mock()
        m_post.return_value = m_ret
        m_ret.status_code = 200
        m_ret.json.return_value = {}
        m_ret = mock.Mock()
        self.assertRaises(RefresherException, self.refresher.refresh, self.provider)


class OidcRefreshVOOptionsTest(base.TestCase):
    def test_populate_parser(self):
        """Tests that the right options are added to the argument parser"""

        parser = argparse.ArgumentParser(conflict_handler="resolve")
        refresher = oidc_vo_refresh.OidcVORefreshToken(None)
        refresher.populate_parser(parser)

        opts = parser.parse_args(
            [
                "--oidc-token-endpoint",
                "http://example.org/oidc",
                "--oidc-credentials-path",
                "/foo",
                "--oidc-scopes",
                "foobar",
            ]
        )

        self.assertEqual("http://example.org/oidc", opts.oidc_token_endpoint)
        self.assertEqual("/foo", opts.oidc_credentials_path)
        self.assertEqual("foobar", opts.oidc_scopes)


class OidcRefreshVOTest(base.TestCase):
    def setUp(self):
        super(OidcRefreshVOTest, self).setUp()

        class FakeRefresher(oidc_vo_refresh.OidcVORefreshToken):
            def __init__(self):
                self.opts = mock.Mock()
                self.opts.oidc_token_endpoint = "http://example.org/oidc"
                self.opts.oidc_credentials_path = "/abc"
                self.opts.oidc_scopes = "foobar"

        class FakeProvider(object):
            def __init__(self):
                self.opts = mock.Mock()

        self.refresher = FakeRefresher()
        self.provider = FakeProvider()

    @mock.patch("requests.post")
    def test_refresh_success(self, m_post):
        """Test the successful renewal of tokens for a vo.foo.bar VO.

        Checks that the files with the credentials are read and
        that the token endpoint is contacted with the right parameters
        """
        m_open = mock.mock_open(read_data="foo")
        m_open.side_effect = [
            m_open.return_value,
            mock.mock_open(read_data="bar").return_value,
            mock.mock_open(read_data="baz").return_value,
        ]
        m_ret = mock.Mock()
        m_post.return_value = m_ret
        m_ret.status_code = 200
        m_ret.json.return_value = {"access_token": "a token"}
        with mock.patch(
            "cloud_info_provider.auth_refreshers.oidc_vo_refresh." "open", m_open
        ):
            self.refresher.refresh(self.provider, vo="vo.foo.bar")
        self.assertEqual("a token", self.provider.opts.os_access_token)
        m_post.assert_called_with(
            "http://example.org/oidc",
            auth=("foo", "bar"),
            data={
                "client_id": "foo",
                "client_secret": "bar",
                "grant_type": "refresh_token",
                "refresh_token": "baz",
                "scope": "foobar",
            },
            timeout=self.refresher.opts.timeout,
        )
