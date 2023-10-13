from cloud_info_provider import auth_refreshers


class AccessToken(auth_refreshers.OidcBaseRefresher):
    """Just uses the access token available at the auth configuration"""

    def refresh(self, provider, access_token=None, **kwargs):
        self._update_provider(provider, access_token)
