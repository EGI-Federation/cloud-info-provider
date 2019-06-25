import requests

from cloud_info_provider import auth_refreshers
from cloud_info_provider import exceptions


class OidcRefreshToken(auth_refreshers.BaseRefresher):
    def refresh(self, provider, **kwargs):
        refresh_data = {
            "client_id": self.opts.oidc_client_id,
            "client_secret": self.opts.oidc_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.opts.oidc_refresh_token,
            "scope": self.opts.oidc_scopes,
        }
        try:
            r = requests.post(self.opts.oidc_token_endpoint,
                              auth=(self.opts.oidc_client_id,
                                    self.opts.oidc_client_secret),
                              data=refresh_data)
            if r.status_code != requests.codes.ok:
                msg = "Unable to get token, request returned %s" % r.text
                raise exceptions.RefresherException(msg)
            # this requires some inner knowledge on the oidc auth of OpenStack
            # and won't work for others, but I'm not sure if we can make
            # this generic
            provider.opts.oidcaccesstoken = r.json()["access_token"]
        except (ValueError,
                KeyError,
                requests.exceptions.RequestException) as e:
            raise exceptions.RefresherException('Unable to get token %s' % e)

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
                            help="OIDC scopes for token")
