from cloud_info_provider import auth_refreshers


class AccessTokenRefresh(auth_refreshers.OidcBaseRefresher):
    """Just uses the access token available at the auth configuration"""

    def _update_provider(self, provider, token):
        # this requires some inner knowledge on the oidc auth of OpenStack
        # and won't work for others, but I'm not sure if we can make
        # this generic
        provider.opts.os_access_token = token

    def refresh(self, provider, access_token=None, **kwargs):
        self._update_provider(provider, access_token)
