import itertools

from cloud_info_provider.collectors import base
from cloud_info_provider.exceptions import CloudInfoException


class ComputeCollector(base.BaseCollector):
    def __init__(self, *args):
        super(ComputeCollector, self).__init__(*args)
        self.templates = ["compute"]

    def fetch_share_info(self, site_info, share, vo):
        kwargs = share.copy()
        kwargs.update({"vo": vo})

        endpoints = self._get_info_from_providers("get_compute_endpoints", **kwargs)
        if not endpoints.get("endpoints"):
            return {}

        # Collect static information for endpoints
        static_compute_info = dict(endpoints, **site_info)
        static_compute_info.pop("endpoints")

        # Add any extra information for share
        share.update(self._get_info_from_providers("get_compute_share", **kwargs))

        # Collect dynamic information
        images = self._get_info_from_providers("get_images", **kwargs)
        templates = self._get_info_from_providers("get_templates", **kwargs)
        instances = self._get_info_from_providers("get_instances", **kwargs)
        quotas = self._get_info_from_providers("get_compute_quotas", **kwargs)

        # Add same static information to endpoints, images and templates
        for d in itertools.chain(
            endpoints["endpoints"].values(), templates.values(), images.values()
        ):
            d.update(static_compute_info)

        return {
            "images": images,
            "templates": templates,
            "instances": instances,
            "endpoints": endpoints,
            "quotas": quotas
        }

    def fetch(self):
        info = {}

        # Retrieve global site information
        # XXX Validate if really project agnostic
        # XXX Here it uses the "default" project from the CLI parameters
        site_info = self._get_info_from_providers("get_site_info")

        # Get shares / projects and related images and templates
        shares = self._get_info_from_providers("get_compute_shares")

        for vo, share in shares.items():
            try:
                share.update(self.fetch_share_info(site_info, share, vo))
            except CloudInfoException as exc:
                if not self.opts.ignore_share_errors:
                    raise exc

        # XXX Avoid creating a new list
        endpoints = {
            endpoint_id: endpoint
            for share_id, share in shares.items()
            for endpoint_id, endpoint in share["endpoints"].items()
        }

        # XXX Avoid redoing what was done in the previous shares loop
        static_compute_info = dict(endpoints, **site_info)
        static_compute_info.pop("endpoints")

        info.update({"static_compute_info": static_compute_info})
        info.update({"shares": shares})

        return info
