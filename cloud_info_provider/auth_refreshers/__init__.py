"""
Authentication refreshers

Provides a pluggable way to dynamically refresh authentication credentials if
needed. The actual refresh mechanism depends greatly on the actual credential
type and the provider used.

The `refresh` method is invoked every time the provider needs to rescope
authentication for a new share (i.e. VO)
"""


class BaseRefresher(object):
    def __init__(self, opts):
        self.opts = opts

    def refresh(self, provider, **kwargs):
        pass

    @staticmethod
    def populate_parser(parser):
        """Populate the argparser 'parser' with the needed options."""


class OidcBaseRefresher(BaseRefresher):
    def _update_provider(self, provider, token):
        # this requires some inner knowledge on the oidc auth of OpenStack
        # and won't work for others, but I'm not sure if we can make
        # this generic
        provider.opts.os_access_token = token
