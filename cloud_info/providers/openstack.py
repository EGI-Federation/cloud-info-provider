import logging
import re
import socket

import functools
import re
import socket

from cloud_info import exceptions
from cloud_info import providers
from cloud_info import utils

import keystoneauth1.exceptions.http
from six.moves.urllib.parse import urljoin
from six.moves.urllib.parse import urlparse

try:
    import requests
except ImportError:
    msg = 'Cannot import requests module.'
    raise exceptions.OpenStackProviderException(msg)

try:
    import glanceclient
except ImportError:
    msg = 'Cannot import glanceclient module.'
    raise exceptions.OpenStackProviderException(msg)

try:
    from keystoneauth1 import loading
    from keystoneauth1.loading import base as loading_base
except ImportError:
    msg = 'Cannot import keystoneauth module.'
    raise exceptions.OpenStackProviderException(msg)

try:
    import novaclient.client
except ImportError:
    msg = 'Cannot import novaclient module.'
    raise exceptions.OpenStackProviderException(msg)

try:
    from OpenSSL import SSL
except ImportError:
    msg = 'Cannot import pyOpenSSL module.'
    raise exceptions.OpenStackProviderException(msg)

# Remove info log messages from output
logging.getLogger('stevedore.extension').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('novaclient').setLevel(logging.WARNING)
logging.getLogger('keystoneauth').setLevel(logging.WARNING)
logging.getLogger('keystoneclient').setLevel(logging.WARNING)


def _rescope(f):
    @functools.wraps(f)
    def inner(self, os_project_name=None, **kwargs):
        if (not self.os_tenant_id or
                os_project_name != self.auth_plugin.project_name):
            self.auth_plugin.project_name = os_project_name
            self.auth_plugin.invalidate()
            try:
                self.os_tenant_id = self.session.get_project_id()
            except keystoneauth1.exceptions.http.Unauthorized:
                msg = ("Could not authorize user in project '%s'" %
                       os_project_name)
                raise exceptions.OpenStackProviderException(msg)
        return f(self, project_name=os_project_name, **kwargs)
    return inner


class OpenStackProvider(providers.BaseProvider):
    def __init__(self, opts):
        super(OpenStackProvider, self).__init__(opts)

        # NOTE(aloga): we do not want a project to be passed from the CLI,
        # as we will iterate over it for each configured VO and project.  We
        # have not added these arguments to the parser, but, since the plugin
        # is expecting them when parsing the arguments we need to set them to
        # None before calling the load_auth_from_argparse_arguments. However,
        # we may receive this in the "opts" namespace, therefore we do not set
        # it this is passed.
        if "os_project_name" not in opts:
            opts.os_project_name = None
            opts.os_tenant_name = None
        if "os_project_id" not in opts:
            opts.os_project_id = None
            opts.os_tenant_id = None

        self.auth_plugin = loading.load_auth_from_argparse_arguments(opts)

        self.session = loading.load_session_from_argparse_arguments(
            opts, auth=self.auth_plugin
        )

        self.os_tenant_id = None

        # Hide urllib3 warnings when allowing unverified connection
        if opts.insecure:
            requests.packages.urllib3.disable_warnings()

        self.nova = novaclient.client.Client(2, session=self.session)
        self.glance = glanceclient.Client('2', session=self.session)

        self.static = providers.static.StaticProvider(opts)
        self.legacy_occi_os = opts.legacy_occi_os
        self.insecure = opts.insecure

        # Retieve information about Keystone endpoint SSL configuration
        e_cert_info = self._get_endpoint_ca_information(opts.os_auth_url,
                                                        opts.insecure,
                                                        opts.os_cacert)
        self.keystone_cert_issuer = e_cert_info['issuer']
        self.keystone_trusted_cas = e_cert_info['trusted_cas']
        self.os_cacert = opts.os_cacert
        # Select 'public', 'private' or 'all' (default) templates.
        self.select_flavors = opts.select_flavors

    def _get_endpoint_versions(self, endpoint_url, endpoint_type):
        '''Return the API and middleware versions of a compute endpoint.'''
        ret = {
            'compute_middleware_version': None,
            'compute_api_version': None,
        }

        defaults = self.static.get_compute_endpoint_defaults(prefix=True)

        mw_version_key = 'compute_%s_middleware_version' % endpoint_type
        api_version_key = 'compute_%s_api_version' % endpoint_type

        e_middleware_version = defaults.get(mw_version_key, 'UNKNOWN')
        e_version = defaults.get(api_version_key, 'UNKNOWN')

        if endpoint_type == 'occi':
            try:
                if self.insecure:
                    verify = False
                else:
                    verify = self.os_cacert

                request_url = "%s/-/" % endpoint_url

                r = self.session.get(request_url,
                                     authenticated=True,
                                     verify=verify)

                if r.status_code == requests.codes.ok:
                    header_server = r.headers['Server']
                    e_middleware_version = re.search(r'ooi/([0-9.]+)',
                                                     header_server).group(1)
                    e_version = re.search(r'OCCI/([0-9.]+)',
                                          header_server).group(1)
            except requests.exceptions.RequestException:
                pass
            except IndexError:
                pass
        elif endpoint_type == 'compute':
            try:
                # TODO(gwarf) Retrieve using API programatically
                e_version = urlparse(endpoint_url).path.split('/')[1]
            except Exception:
                pass

        ret.update({
            'compute_middleware_version': e_middleware_version,
            'compute_api_version': e_version,
        })

        return ret

    def _get_endpoint_ca_information(self, endpoint_url, insecure, cacert):
        '''Return the cer issuer and trusted CAs list of an HTTPS endpoint.'''
        ca_info = {'issuer': 'UNKNOWN', 'trusted_cas': ['UNKNOWN']}

        if insecure:
            verify = SSL.VERIFY_NONE
        else:
            verify = SSL.VERIFY_PEER

        try:
            scheme = urlparse(endpoint_url).scheme
            host = urlparse(endpoint_url).hostname
            port = urlparse(endpoint_url).port

            if scheme == 'https':
                ctx = SSL.Context(SSL.SSLv23_METHOD)
                ctx.set_options(SSL.OP_NO_SSLv2)
                ctx.set_options(SSL.OP_NO_SSLv3)
                ctx.set_verify(verify, lambda conn, cert, errno, depth, ok: ok)
                if not insecure:
                    ctx.load_verify_locations(cacert)

                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((host, port))

                client_ssl = SSL.Connection(ctx, client)
                client_ssl.set_connect_state()
                client_ssl.set_tlsext_host_name(host)
                client_ssl.do_handshake()

                cert = client_ssl.get_peer_certificate()
                issuer = self._get_dn(cert.get_issuer())

                client_ca_list = client_ssl.get_client_ca_list()
                trusted_cas = [self._get_dn(ca) for ca in client_ca_list]

                client_ssl.shutdown()
                client_ssl.close()

                ca_info['issuer'] = issuer
                ca_info['trusted_cas'] = trusted_cas
        except SSL.Error:
            pass

        return ca_info

    def _get_dn(self, x509name):
        '''Return the DN of an X509Name object.'''
        # XXX shortest/easiest way to get the DN of the X509Name
        # str(X509Name): <X509Name object 'DN'>
        # return str(x509name)[18:-2]
        obj_name = str(x509name)
        start = obj_name.find("'") + 1
        end = obj_name.rfind("'")

        return obj_name[start:end]

        # Retrieve a keystone authentication token
        # XXX to be used as main authentication mean
        self.keystone = ksclient.Client(auth_url=os_auth_url,
                                        username=os_username,
                                        password=os_password,
                                        tenant_name=os_tenant_name,
                                        insecure=insecure)
        self.auth_token = self.keystone.auth_token
        self.os_tenant_id = self.keystone.get_project_id(os_tenant_name)

        # Retieve information about Keystone endpoint SSL configuration
        e_cert_info = self._get_endpoint_ca_information(opts.os_auth_url,
                                                        opts.insecure,
                                                        opts.os_cacert)
        self.keystone_cert_issuer = e_cert_info['issuer']
        self.keystone_trusted_cas = e_cert_info['trusted_cas']
        self.os_cacert = opts.os_cacert

    def _get_endpoint_versions(self, endpoint_url, endpoint_type):
        '''Return the API and middleware versions of a compute endpoint.'''
        ret = {
            'compute_middleware_version': None,
            'compute_api_version': None,
        }

        defaults = self.static.get_compute_endpoint_defaults(prefix=True)

        mw_version_key = 'compute_%s_middleware_version' % endpoint_type
        api_version_key = 'compute_%s_api_version' % endpoint_type

        e_middleware_version = defaults.get(mw_version_key, 'UNKNOWN')
        e_version = defaults.get(api_version_key, 'UNKNOWN')

        if endpoint_type == 'occi':
            try:
                if self.insecure:
                    verify = False
                else:
                    verify = self.os_cacert

                request_url = "%s/-/" % endpoint_url

                r = self.session.get(request_url,
                                     authenticated=True,
                                     verify=verify)

                if r.status_code == requests.codes.ok:
                    header_server = r.headers['Server']
                    e_middleware_version = re.search(r'ooi/([0-9.]+)',
                                                     header_server).group(1)
                    e_version = re.search(r'OCCI/([0-9.]+)',
                                          header_server).group(1)
            except requests.exceptions.RequestException:
                pass
            except IndexError:
                pass
        elif endpoint_type == 'compute':
            try:
                # TODO(gwarf) Retrieve using API programatically
                e_version = urlparse(endpoint_url).path.split('/')[1]
            except Exception:
                pass

        ret.update({
            'compute_middleware_version': e_middleware_version,
            'compute_api_version': e_version,
        })

        return ret

    def _get_endpoint_ca_information(self, endpoint_url, insecure, cacert):
        '''Return the cer issuer and trusted CAs list of an HTTPS endpoint.'''
        ca_info = {'issuer': 'UNKNOWN', 'trusted_cas': ['UNKNOWN']}

        if insecure:
            verify = SSL.VERIFY_NONE
        else:
            verify = SSL.VERIFY_PEER

        try:
            scheme = urlparse(endpoint_url).scheme
            host = urlparse(endpoint_url).hostname
            port = urlparse(endpoint_url).port

            if scheme == 'https':
                ctx = SSL.Context(SSL.SSLv23_METHOD)
                ctx.set_options(SSL.OP_NO_SSLv2)
                ctx.set_options(SSL.OP_NO_SSLv3)
                ctx.set_verify(verify, lambda conn, cert, errno, depth, ok: ok)
                if not insecure:
                    ctx.load_verify_locations(cacert)

                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((host, port))

                client_ssl = SSL.Connection(ctx, client)
                client_ssl.set_connect_state()
                client_ssl.set_tlsext_host_name(host)
                client_ssl.do_handshake()

                cert = client_ssl.get_peer_certificate()
                issuer = self._get_dn(cert.get_issuer())

                client_ca_list = client_ssl.get_client_ca_list()
                trusted_cas = [self._get_dn(ca) for ca in client_ca_list]

                client_ssl.shutdown()
                client_ssl.close()

                ca_info['issuer'] = issuer
                ca_info['trusted_cas'] = trusted_cas
        except SSL.Error:
            pass

        return ca_info

    def _get_dn(self, x509name):
        '''Return the DN of an X509Name object.'''
        # XXX shortest/easiest way to get the DN of the X509Name
        # str(X509Name): <X509Name object 'DN'>
        # return str(x509name)[18:-2]
        obj_name = str(x509name)
        start = obj_name.find("'") + 1
        end = obj_name.rfind("'")

        return obj_name[start:end]

    @_rescope
    def get_compute_endpoints(self, os_project_name=None, **kwargs):
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
            'compute_service_name': self.auth_plugin.auth_url
        }

        defaults = self.static.get_compute_endpoint_defaults(prefix=True)
        catalog = self.auth_plugin.get_access(self.session).service_catalog
        for e_type, e_data in supported_endpoints.items():
            epts = catalog.get_endpoints(service_type=e_type,
                                         interface="public")
            if not epts:
                continue
            for ept in epts[e_type]:
                e_id = ept['id']
                e_url = ept['url']
                # Use keystone SSL information
                e_issuer = self.keystone_cert_issuer
                e_cas = self.keystone_trusted_cas
                e_versions = self._get_endpoint_versions(e_url, e_type)
                e_mw_version = e_versions['compute_middleware_version']
                e_api_version = e_versions['compute_api_version']

                e = defaults.copy()
                e.update(e_data)
                e.update({
                    'compute_endpoint_url': e_url,
                    'endpoint_issuer': e_issuer,
                    'endpoint_trusted_cas': e_cas,
                    'compute_middleware_version': e_mw_version,
                    'compute_api_version': e_api_version,
                })

                ret['endpoints'][e_id] = e
        return ret

    @_rescope
    def get_templates(self, os_project_name=None, **kwargs):
        """Return templates/flavors selected accroding to --select-flavors"""
        flavors = {}

        defaults = {'template_platform': 'amd64',
                    'template_network': 'private'}
        defaults.update(self.static.get_template_defaults(prefix=True))
        tpl_sch = defaults.get('template_schema', 'resource')
        flavor_id_attr = 'name' if self.legacy_occi_os else 'id'
        URI = 'http://schemas.openstack.org/template/'
        for flavor in self.nova.flavors.list(detailed=True):
            add_all = self.select_flavors == 'all'
            add_pub = self.select_flavors == 'public' and flavor.is_public
            add_priv = (self.select_flavors == 'private' and not
                        flavor.is_public)
            if add_all or add_pub or add_priv:
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

    @_rescope
    def get_images(self, os_project_name=None, **kwargs):
        images = {}

        # image_native_id: middleware image ID
        # image_id: OCCI image ID
        template = {
            'image_name': None,
            'image_id': None,
            'image_native_id': None,
            'image_description': None,
            'image_version': None,
            'image_marketplace_id': None,
            'image_platform': 'amd64',
            'image_os_family': None,
            'image_os_name': None,
            'image_os_version': None,
            'image_minimal_cpu': None,
            'image_recommended_cpu': None,
            'image_minimal_ram': None,
            'image_recommended_ram': None,
            'image_minimal_accel': None,
            'image_recommended_accel': None,
            'image_accel_type': None,
            'image_size': None,
            'image_traffic_in': [],
            'image_traffic_out': [],
            'image_access_info': 'none',
            'image_context_format': None,
            'image_software': [],
        }
        defaults = self.static.get_image_defaults(prefix=True)
        img_sch = defaults.get('image_schema', 'os')
        URI = 'http://schemas.openstack.org/template/'

        for image in self.glance.images.list(detailed=True):
            aux_img = template.copy()
            aux_img.update(defaults)

            # XXX Create an entry for each metatdata attribute, no filtering
            for name, value in image.items():
                aux_img[name] = value

            img_name = image.get("name")
            img_id = image.get("id")
            aux_img.update({
                'image_name': img_name,
                'image_native_id': img_id,
                'image_id': '%s%s#%s' % (URI, img_sch,
                                         OpenStackProvider.occify(img_id))
            })

            image_descr = (image.get('vmcatcher_event_dc_description') or
                           image.get('vmcatcher_event_dc_title'))

            marketplace_id = (image.get('vmcatcher_event_ad_mpuri') or
                              image.get('marketplace'))

            if marketplace_id is None:
                if not defaults.get('image_require_marketplace_id'):
                    link = urljoin(self.glance.http_client.get_endpoint(),
                                   image.get("file"))
                    marketplace_id = link
                else:
                    continue

            distro = image.get('os_distro')
            distro_version = image.get('os_version')
            image_version = image.get('image_version')

            if marketplace_id:
                aux_img['image_marketplace_id'] = marketplace_id
            if image_descr:
                aux_img['image_description'] = image_descr
            if distro:
                aux_img['image_os_name'] = distro
            if distro_version:
                aux_img['image_os_version'] = distro_version
            if image_version:
                aux_img['image_version'] = image_version

            images[img_id] = aux_img
        return images

    @_rescope
    def get_instances(self, os_project_name=None, **kwargs):
        instance_template = {
            'instance_name': None,
            'instance_image_id': None,
            'instance_template_id': None,
            'instance_status': None,
        }

        instances = {}

        for instance in self.nova.servers.list():
            ret = instance_template.copy()
            ret.update({
                'instance_name': instance.name,
                'instance_image_id': instance.image['id'],
                'instance_template_id': instance.flavor['id'],
                'instance_status': instance.status,
            })
            instances[instance.id] = ret

        return instances

    @_rescope
    def get_compute_quotas(self, os_project_name=None, **kwargs):
        '''Return the quotas set for the current project.'''

        quota_resources = ['instances', 'cores', 'ram',
                           'floating_ips', 'fixed_ips', 'metadata_items',
                           'injected_files', 'injected_file_content_bytes',
                           'injected_file_path_bytes', 'key_pairs',
                           'security_groups', 'security_group_rules',
                           'server_groups', 'server_group_members']

        defaults = self.static.get_compute_quotas_defaults(prefix=False)
        quotas = defaults.copy()

        try:
            project_quotas = self.nova.quotas.get(self.os_tenant_id)
            for resource in quota_resources:
                try:
                    quotas[resource] = getattr(project_quotas, resource)
                except AttributeError:
                    pass
        except Forbidden:
            # Should we raise an error and make this mandatory?
            pass

        return quotas

    @staticmethod
    def occify(term_name):
        '''Occifies a term_name so that it is compliant with GFD 185.'''

        term = term_name.strip().replace(' ', '_').replace('.', '-').lower()
        return term

    @staticmethod
    def populate_parser(parser):
        default_auth = "v3password"
        parser.add_argument('--os-auth-type',
                            '--os-auth-plugin',
                            metavar='<name>',
                            default=default_auth,
                            help='Authentication type to use')

        plugin = loading_base.get_plugin_loader(default_auth)

        for opt in plugin.get_options():
            # NOTE(aloga): we do not want a project to be passed from the CLI,
            # as we will iterate over it for each configured VO and project.
            # However, as the plugin is expecting them when parsing the
            # arguments we need to set them to None before calling the
            # load_auth_from_argparse_arguments method in the __init__ method
            # of this class.
            if opt.name in ("project-name", "project-id"):
                continue
            parser.add_argument(*opt.argparse_args,
                                default=opt.argparse_default,
                                metavar=opt.metavar,
                                help=opt.help,
                                dest='os_%s' % opt.dest)

        parser.add_argument(
            '--insecure',
            default=utils.env('NOVACLIENT_INSECURE', default=False),
            action='store_true',
            help="Explicitly allow novaclient to perform 'insecure' "
                 "SSL (https) requests. The server's certificate will "
                 'not be verified against any certificate authorities. '
                 'This option should be used with caution.')

        parser.add_argument(
            '--os-cacert',
            metavar='<ca-certificate>',
            default=utils.env('OS_CACERT', default=requests.certs.where()),
            help='Specify a CA bundle file to use in '
            'verifying a TLS (https) server certificate. '
            'Defaults to env[OS_CACERT].')

        parser.add_argument(
            '--os-cert',
            metavar='<certificate>',
            default=utils.env('OS_CERT', default=None),
            help='Defaults to env[OS_CERT].')

        parser.add_argument(
            '--os-key',
            metavar='<key>',
            default=utils.env('OS_KEY', default=None),
            help='Defaults to env[OS_KEY].')

        parser.add_argument(
            '--timeout',
            default=600,
            metavar='<seconds>',
            help='Set request timeout (in seconds).')

        parser.add_argument(
            '--legacy-occi-os',
            default=False,
            action='store_true',
            help="Generate information and ids compatible with OCCI-OS, "
                 "e.g. using the flavor name instead of the flavor id.")

        parser.add_argument(
            '--select-flavors',
            default='all',
            choices=['all', 'public', 'private'],
            help='Select all (default), public or private flavors/templates.')
