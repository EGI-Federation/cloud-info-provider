import abc

import six


@six.add_metaclass(abc.ABCMeta)
class BaseCollector(object):
    def __init__(self, opts, providers, auth_refresher):
        self.opts = opts
        self.providers = providers

        if opts.middleware != "static" and opts.middleware in self.providers:
            self.dynamic_provider = self.providers[opts.middleware](
                opts, auth_refresher=auth_refresher
            )
        else:
            self.dynamic_provider = None

        self.static_provider = self.providers["static"](opts)

    def _get_info_from_providers(self, method, **provider_kwargs):
        info = {}
        for i in (self.static_provider, self.dynamic_provider):
            if not i:
                continue
            result = getattr(i, method)(**provider_kwargs)
            info.update(result)
        return info

    @abc.abstractmethod
    def fetch(self):
        """Fetch information from the resource type."""
