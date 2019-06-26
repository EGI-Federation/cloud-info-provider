import requests

from cloud_info_provider import auth_refreshers
from cloud_info_provider import exceptions


class OidcRefreshToken(auth_refreshers.BaseRefresher):
    """Refreshes OAuth 2.0 access tokens using refresh_token grant.

    OAuth2.0 token endpoint and credentials are specified in the options to
    perform token refresh request following
    https://tools.ietf.org/html/rfc6749#section-1.5
    """
    def _refresh_token(self, token_endpoint, client_id, client_secret,
                       refresh_token, scopes):
        refresh_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": scopes,
        }
        try:
            r = requests.post(token_endpoint,
                              auth=(client_id,
                                    client_secret),
                              data=refresh_data)
            if r.status_code != requests.codes.ok:
                msg = "Unable to get token, request returned %s" % r.text
                raise exceptions.RefresherException(msg)
            return r.json()["access_token"]
        except (ValueError,
                KeyError,
                requests.exceptions.RequestException) as e:
            raise exceptions.RefresherException('Unable to get token %s' % e)

    def _update_provider(self, provider, token):
        # this requires some inner knowledge on the oidc auth of OpenStack
        # and won't work for others, but I'm not sure if we can make
        # this generic
        provider.opts.oidcaccesstoken = token

    def refresh(self, provider, **kwargs):
        token = self._refresh_token(self.opts.oidc_token_endpoint,
                                    self.opts.oidc_client_id,
                                    self.opts.oidc_client_secret,
                                    self.opts.oidc_refresh_token,
                                    self.opts.oidc_scopes)
        self._update_provider(provider, token)

    @staticmethod
    def populate_parser(parser):
        parser.add_argument("--oidc-token-endpoint", metavar="<oidc endpoint>",
                            help="URL of endpoint where tokens are refreshed")

        parser.add_argument("--oidc-client-id", metavar="<oidc client id>",
                            help="OIDC Client identifier")

        parser.add_argument("--oidc-client-secret", metavar="<oidc secret>",
                            help="OIDC Client secret")

        parser.add_argument("--oidc-refresh-token", metavar="<refresh token>",
                            help="OIDC Refresh token")

        parser.add_argument("--oidc-scopes", metavar="<scopes>",
                            default="openid email profile",
                            help="OIDC scopes for token refresh")
