import os.path

from cloud_info_provider.auth_refreshers import oidc_refresh


class OidcVORefreshToken(oidc_refresh.OidcRefreshToken):
    """Refreshes OAuth 2.0 access tokens using different credentials per VO.

    Expects that the credentials are available on files named as
    follows:
      - /base_path/<name of the vo>/client_id with the OIDC client id
      - /base_path/<name of the vo>/client_secret with the OIDC client secret
      - /base_path/<name of the vo>/refresh_token with the refresh token

    The refresher will read the files and perform a token refresh request
    following https://tools.ietf.org/html/rfc6749#section-1.5
    """

    def refresh(self, provider, vo=None, **kwargs):
        base = os.path.join(self.opts.oidc_credentials_path, vo)
        args = {}
        for secret in ["client_id", "client_secret", "refresh_token"]:
            with open(os.path.join(base, secret), "r") as f:
                args[secret] = f.read()
        token = self._refresh_token(
            self.opts.oidc_token_endpoint,
            args["client_id"],
            args["client_secret"],
            args["refresh_token"],
            self.opts.oidc_scopes,
        )
        self._update_provider(provider, token)

    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            "--oidc-token-endpoint",
            metavar="<oidc endpoint>",
            help="URL of endpoint where tokens are refreshed",
        )

        parser.add_argument(
            "--oidc-credentials-path",
            metavar="<oidc credentials path>",
            help=(
                "Path where to find the OIDC client "
                "credentials for each VO. The refresher "
                "will look for <path>/<vo>/client_id, "
                "<path>/<vo>/client_secret and "
                "<path>/<vo>/refresh_token files that "
                "should contain the id, secret and refresh "
                "token to use for a given VO"
            ),
        )

        parser.add_argument(
            "--oidc-scopes",
            metavar="<scopes>",
            default="openid email profile",
            help="OIDC scopes for token",
        )
