import re

from cloud_info_provider import exceptions
from cloud_info_provider.providers.openstack import OpenStackProvider

try:
    import requests
except ImportError:
    msg = 'Cannot import requests module.'
    raise exceptions.OpenStackProviderException(msg)


class OoiProvider(OpenStackProvider):
    service_type = 'occi'
    goc_service_type = 'eu.egi.cloud.vm-management.occi'
    service_data = {
        'compute_api_type': 'OCCI',
        'compute_middleware': 'ooi',
        'compute_middleware_developer': 'CSIC',
    }

    def __init__(self, opts):
        super(OoiProvider, self).__init__(opts)

    def _get_endpoint_versions(self, endpoint_url):
        '''Return the API and middleware versions of a compute endpoint.'''
        e_middleware_version = None
        e_version = None

        if self.insecure:
            verify = False
        else:
            verify = self.os_cacert

        request_url = "%s/-/" % endpoint_url
        try:
            r = self.session.get(request_url,
                                 authenticated=True,
                                 verify=verify)
            if r.status_code == requests.codes.ok:
                header_server = r.headers['Server']
                e_middleware_version = re.search(r'ooi/([0-9.]+)',
                                                 header_server).group(1)
                e_version = re.search(r'OCCI/([0-9.]+)',
                                      header_server).group(1)
        except IndexError:
            pass
        except requests.exceptions.RequestException:
            pass

        return {
            'compute_middleware_version': e_middleware_version,
            'compute_api_version': e_version,
        }

    def _get_endpoint_id_url(self, e_url):
        return e_url

    def _get_extra_endpoint_info(self, e_url):
        return {}

    @staticmethod
    def adapt_id(term_name):
        '''Occifies a term_name so that it is compliant with GFD 185.'''
        term = term_name.strip().replace(' ', '_').replace('.', '-').lower()
        return term
