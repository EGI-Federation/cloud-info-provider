import logging
import re

from cloud_info import exceptions
from cloud_info import providers
from cloud_info import utils

from six.moves.urllib.parse import urlparse

try:
    import novaclient.client
except ImportError:
    msg = 'Cannot import novaclient module.'
    raise exceptions.OpenStackProviderException(msg)

try:
    import requests
except ImportError:
    msg = 'Cannot import requests module.'
    raise exceptions.OpenStackProviderException(msg)

# Remove info log messages from output
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('novaclient.client').setLevel(logging.WARNING)
logging.getLogger('keystoneclient').setLevel(logging.WARNING)


class OpenStackProvider(providers.BaseProvider):
    def __init__(self, opts):
        super(OpenStackProvider, self).__init__(opts)

        (os_username, os_password, os_tenant_name, os_auth_url,
         cacert, insecure, legacy_occi_os) = (opts.os_username,
                                              opts.os_password,
                                              opts.os_tenant_name,
                                              opts.os_auth_url,
                                              opts.os_cacert,
                                              opts.insecure,
                                              opts.legacy_occi_os)

        if not os_username:
            msg = ('ERROR, You must provide a username '
                   'via either --os-username or env[OS_USERNAME]')
            raise exceptions.OpenStackProviderException(msg)

        if not os_password:
            msg = ('ERROR, You must provide a password '
                   'via either --os-password or env[OS_PASSWORD]')
            raise exceptions.OpenStackProviderException(msg)

        if not os_tenant_name:
            msg = ('You must provide a tenant name '
                   'via either --os-tenant-name or env[OS_TENANT_NAME]')
            raise exceptions.OpenStackProviderException(msg)

        if not os_auth_url:
            msg = ('You must provide an auth url '
                   'via either --os-auth-url or env[OS_AUTH_URL] ')
            raise exceptions.OpenStackProviderException(msg)

        client_cls = novaclient.client.Client
        if insecure:
            self.api = client_cls(2,
                                  os_username,
                                  os_password,
                                  os_tenant_name,
                                  auth_url=os_auth_url,
                                  insecure=insecure)
        else:
            self.api = client_cls(2,
                                  os_username,
                                  os_password,
                                  os_tenant_name,
                                  auth_url=os_auth_url,
                                  insecure=insecure,
                                  cacert=cacert)

        self.api.authenticate()
        self.static = providers.static.StaticProvider(opts)
        self.legacy_occi_os = legacy_occi_os

    def get_compute_endpoints(self):
        # Hard-coded defaults for supported endpoints types
        supported_endpoints = {
            'occi': {
                'compute_api_type': 'OCCI',
                'compute_middleware': 'ooi',
                'compute_middleware_developer': 'CSIC',
            },
            'compute': {
                'compute_api_type': 'OpenStack',
                'compute_middleware': 'OpenStack Nova',
                'compute_middleware_developer': 'OpenStack Foundation',
            }
        }

        ret = {
            'endpoints': {},
            'compute_middleware_developer': 'OpenStack',
            'compute_middleware': 'OpenStack Nova',
            'compute_service_name': self.api.client.auth_url,
        }

        defaults = self.static.get_compute_endpoint_defaults(prefix=True)
        catalog = self.api.client.service_catalog.catalog

        endpoints = catalog['access']['serviceCatalog']
        for endpoint in endpoints:
            e_type = endpoint['type']
            if e_type in supported_endpoints:
                for ept in endpoint['endpoints']:
                    e_id = ept['id']
                    e_url = ept['publicURL']
                    if e_type == 'occi':
                        e_middleware_version = defaults.get(
                            'compute_occi_middleware_version', '0.3.2')
                        e_version = defaults.get('endpoint_occi_api_version',
                                                 '1.1')
                        try:
                            headers = {'X-Auth-token': self.auth_token}
                            request_url = "%s/-/" % e_url
                            r = requests.get(request_url, headers=headers)
                            if r.status_code == requests.codes.ok:
                                header_server = r.headers['Server']
                                e_middleware_version = re.search(
                                    r'ooi/([0-9.]+)', header_server).group(1)
                                e_version = re.search(
                                    r'OCCI/([0-9.]+)',
                                    header_server
                                ).group(1)
                        except requests.exceptions.RequestException as e:
                            pass
                        except IndexError as e:
                            pass
                    else:
                        e_middleware_version = defaults.get(
                            'compute_middleware_version', 'Mitaka')
                        e_version = defaults.get(
                            'endpoint_openstack_api_version',
                            'v2'
                        )
                        try:
                            # TODO(gwarf) Retrieve using API programatically
                            e_version = urlparse(e_url).path.split('/')[1]
                        except Exception as e:
                            pass

                    e = defaults.copy()
                    e.update(supported_endpoints[e_type])
                    e.update({
                        'compute_endpoint_url': e_url,
                        'compute_middleware_version': e_middleware_version,
                        'compute_api_version': e_version
                    })

                    ret['endpoints'][e_id] = e

        return ret

    def get_templates(self):
        flavors = {}

        defaults = {'template_platform': 'amd64',
                    'template_network': 'private'}
        defaults.update(self.static.get_template_defaults(prefix=True))
        tpl_sch = defaults.get('template_schema', 'resource')
        flavor_id_attr = 'name' if self.legacy_occi_os else 'id'
        URI = 'http://schemas.openstack.org/template/'
        for flavor in self.api.flavors.list(detailed=True):
            if not flavor.is_public:
                continue

            aux = defaults.copy()
            flavor_id = str(getattr(flavor, flavor_id_attr))
            template_id = '%s%s#%s' % (URI, tpl_sch,
                                       OpenStackProvider.occify(flavor_id))
            aux.update({'template_id': template_id,
                        'template_memory': flavor.ram,
                        'template_cpu': flavor.vcpus,
                        'template_disk': flavor.disk})
            flavors[flavor.id] = aux
        return flavors

    def get_images(self):
        images = {}

        template = {
            'image_name': None,
            'image_description': None,
            'image_version': None,
            'image_marketplace_id': None,
            'image_id': None,
            'image_os_family': None,
            'image_os_name': None,
            'image_os_version': None,
            'image_platform': 'amd64',
        }
        defaults = self.static.get_image_defaults(prefix=True)
        img_sch = defaults.get('image_schema', 'os')
        URI = 'http://schemas.openstack.org/template/'

        for image in self.api.images.list(detailed=True):
            aux_img = template.copy()
            aux_img.update(defaults)
            link = None
            for link in image.links:
                # TODO(aloga): Check if this is the needed parameter
                if link.get('type',
                            None) == 'application/vnd.openstack.image':
                    link = link['href']
                    break

            # XXX Create an entry for each metatdata attribute, no filtering
            for name, value in image.metadata.items():
                aux_img[name] = value

            aux_img.update({
                'image_name': image.name,
                'image_id': '%s%s#%s' % (URI, img_sch,
                                         OpenStackProvider.occify(image.id))
            })

            image_descr = None
            if image.metadata.get('vmcatcher_event_dc_description',
                                  None) is not None:
                image_descr = image.metadata['vmcatcher_event_dc_description']
            elif 'vmcatcher_event_dc_title' in image.metadata:
                image_descr = image.metadata['vmcatcher_event_dc_title']

            marketplace_id = None
            if image.metadata.get('vmcatcher_event_ad_mpuri',
                                  None) is not None:
                marketplace_id = image.metadata['vmcatcher_event_ad_mpuri']
            elif 'marketplace' in image.metadata:
                marketplace_id = image.metadata['marketplace']
            elif not defaults.get('image_require_marketplace_id', False):
                marketplace_id = link
            else:
                continue

            distro = None
            if image.metadata.get('os_distro', None) is not None:
                distro = image.metadata['os_distro']

            distro_version = None
            if image.metadata.get('os_version', None) is not None:
                distro_version = image.metadata['os_version']

            if marketplace_id:
                aux_img['image_marketplace_id'] = marketplace_id
            if image_descr:
                aux_img['image_description'] = image_descr
            if distro:
                aux_img['image_os_name'] = distro
            if distro_version:
                aux_img['image_os_version'] = distro_version
            if image.metadata.get('image_version', None) is not None:
                image_version = image.metadata['image_version']
            elif image.metadata.get('vmcatcher_event_hv_version', None) \
                    is not None:
                image_version = image.metadata['vmcatcher_event_hv_version']
            else:
                if (image.metadata.get('distro', None) is not None) and (
                        image.metadata.get(distro_version) is not None):
                    image_version = str(distro) + ' ' + str(distro_version)
                else:
                    image_version = None
            if image_version:
                aux_img['image_version'] = image_version

            images[image.id] = aux_img
        return images

    @staticmethod
    def occify(term_name):
        '''Occifies a term_name so that it is compliant with GFD 185.'''

        term = term_name.strip().replace(' ', '_').replace('.', '-').lower()
        return term

    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            '--os-username',
            metavar='<auth-user-name>',
            default=utils.env('OS_USERNAME', 'NOVA_USERNAME'),
            help='Defaults to env[OS_USERNAME].')

        parser.add_argument(
            '--os-password',
            metavar='<auth-password>',
            default=utils.env('OS_PASSWORD', 'NOVA_PASSWORD'),
            help='Defaults to env[OS_PASSWORD].')

        parser.add_argument(
            '--os-tenant-name',
            metavar='<auth-tenant-name>',
            default=utils.env('OS_TENANT_NAME', 'NOVA_PROJECT_ID'),
            help='Defaults to env[OS_TENANT_NAME].')

        parser.add_argument(
            '--os-auth-url',
            metavar='<auth-url>',
            default=utils.env('OS_AUTH_URL', 'NOVA_URL'),
            help='Defaults to env[OS_AUTH_URL].')

        parser.add_argument(
            '--os-cacert',
            metavar='<ca-certificate>',
            default=utils.env('OS_CACERT', default=None),
            help='Specify a CA bundle file to use in '
                 'verifying a TLS (https) server certificate. '
                 'Defaults to env[OS_CACERT]')

        parser.add_argument(
            '--insecure',
            default=utils.env('NOVACLIENT_INSECURE', default=False),
            action='store_true',
            help="Explicitly allow novaclient to perform 'insecure' "
                 "SSL (https) requests. The server's certificate will "
                 'not be verified against any certificate authorities. '
                 'This option should be used with caution.')

        parser.add_argument(
            '--legacy-occi-os',
            default=False,
            action='store_true',
            help="Generate information and ids compatible with OCCI-OS, "
                 "e.g. using the flavor name instead of the flavor id.")
