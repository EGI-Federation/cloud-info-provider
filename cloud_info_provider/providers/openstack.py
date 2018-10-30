import functools
import logging

from cloud_info_provider import exceptions
from cloud_info_provider import providers
from cloud_info_provider.providers import ssl_utils
from cloud_info_provider import utils

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
    from keystoneauth1.exceptions import http as http_exc
    from keystoneauth1 import loading
    from keystoneauth1.loading import base as loading_base
    from keystoneauth1.loading import session as loading_session
except ImportError:
    msg = 'Cannot import keystoneauth module.'
    raise exceptions.OpenStackProviderException(msg)

try:
    import novaclient.client
    from novaclient.exceptions import Forbidden
except ImportError:
    msg = 'Cannot import novaclient module.'
    raise exceptions.OpenStackProviderException(msg)

# Remove info log messages from output
logging.getLogger('stevedore.extension').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('novaclient').setLevel(logging.WARNING)
logging.getLogger('keystoneauth').setLevel(logging.WARNING)
logging.getLogger('keystoneclient').setLevel(logging.WARNING)


# TODO(enolfc): should this be completely inside the provider class?
def _rescope(f):
    @functools.wraps(f)
    def inner(self, project=None, project_domain_name=None, **kwargs):
        self._rescope_project(project, project_domain_name)
        return f(self, **kwargs)
    return inner


class OpenStackProvider(providers.BaseProvider):
    service_type = "compute"
    service_data = {
        'compute_api_type': 'OpenStack',
        'compute_middleware': 'OpenStack Nova',
        'compute_middleware_developer': 'OpenStack Foundation',
    }

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

        # need to keep this to be able to rescope
        self.opts = opts
        self.auth_plugin = loading.load_auth_from_argparse_arguments(opts)

        self.session = loading.load_session_from_argparse_arguments(
            opts, auth=self.auth_plugin
        )

        # Hide urllib3 warnings when allowing unverified connection
        if opts.insecure:
            requests.packages.urllib3.disable_warnings()

        self.nova = novaclient.client.Client(2, session=self.session)
        self.glance = glanceclient.Client('2', session=self.session)

        try:
            self.project_id = self.session.get_project_id()
            self.project = self.session.auth.project_name
        except http_exc.Unauthorized:
            msg = "Could not authorize user"
            raise exceptions.OpenStackProviderException(msg)

        self.static = providers.static.StaticProvider(opts)
        self.insecure = opts.insecure
        self.all_images = opts.all_images

        # Retieve information about Keystone endpoint SSL configuration
        e_cert_info = ssl_utils.get_endpoint_ca_information(opts.os_auth_url,
                                                            opts.insecure,
                                                            opts.os_cacert)
        self.keystone_cert_issuer = e_cert_info['issuer']
        self.keystone_trusted_cas = e_cert_info['trusted_cas']
        self.os_cacert = opts.os_cacert
        # Select 'public', 'private' or 'all' (default) templates.
        self.select_flavors = opts.select_flavors

    def _rescope_project(self, project, project_domain_name):
        '''Switch to new OS project whenever there is a change.

           It updates every OpenStack client used in case of new project.
        '''
        if (not self.project or project != self.project):
            self.opts.os_project_name = project
            self.opts.os_project_domain_name = project_domain_name
            # make sure that it also works for v2voms
            self.opts.os_tenant_name = project
            self.auth_plugin = loading.load_auth_from_argparse_arguments(
                self.opts
            )
            self.session = loading.load_session_from_argparse_arguments(
                self.opts, auth=self.auth_plugin
            )
            self.auth_plugin.invalidate()
            try:
                self.project_id = self.session.get_project_id()
                self.project = project
            except http_exc.Unauthorized:
                msg = "Could not authorize user in project '%s'" % project
                raise exceptions.OpenStackProviderException(msg)
            # make sure the clients know about the change
            self.nova = novaclient.client.Client(2, session=self.session)
            self.glance = glanceclient.Client('2', session=self.session)

    @staticmethod
    def _get_endpoint_versions(endpoint_url):
        '''Return the API and middleware versions of a compute endpoint.'''
        e_middleware_version = None
        e_version = None
        try:
            # TODO(gwarf) Retrieve using API programatically
            e_version = urlparse(endpoint_url).path.split('/')[1]
        except IndexError:
            pass

        return {
            'compute_middleware_version': e_middleware_version,
            'compute_api_version': e_version,
        }

    def _get_endpoint_id_url(self, e_url):
        return self.auth_plugin.auth_url

    def _get_extra_endpoint_info(self, e_url):
        nova_versions = self._get_endpoint_versions(e_url)
        nova_api_version = nova_versions['compute_api_version']
        return {
            'compute_nova_endpoint_url': e_url,
            'compute_nova_api_version': nova_api_version,
        }

    @_rescope
    def get_compute_endpoints(self, **kwargs):
        ret = {
            'endpoints': {},
            'compute_service_name': self.auth_plugin.auth_url
        }

        defaults = self.static.get_compute_endpoint_defaults(prefix=True)
        catalog = self.auth_plugin.get_access(self.session).service_catalog
        epts = catalog.get_endpoints(service_type=self.service_type,
                                     interface="public")
        for ept in epts.get(self.service_type, []):
            e_id = ept['id']
            # URL is in different places depending of Keystone version
            e_url = ept.get('url', ept.get('publicURL'))
            # the URL used as id is different if OCCI or nova
            e_id_url = self._get_endpoint_id_url(e_url)
            # Use keystone SSL information
            e_issuer = self.keystone_cert_issuer
            e_cas = self.keystone_trusted_cas
            e_versions = self._get_endpoint_versions(e_id_url)
            e_mw_version = e_versions['compute_middleware_version']
            e_api_version = e_versions['compute_api_version']
            # Fallback on defaults if nothing was found
            e_mw_version = self._default_if_none(e_mw_version,
                                                 self.service_type,
                                                 defaults,
                                                 'middleware_version')
            e_api_version = self._default_if_none(e_api_version,
                                                  self.service_type,
                                                  defaults,
                                                  'api_version')

            e = defaults.copy()
            e.update(self.service_data)
            e.update({
                'compute_endpoint_url': e_id_url,
                'compute_endpoint_id': e_id,
                'endpoint_issuer': e_issuer,
                'endpoint_trusted_cas': e_cas,
                'compute_middleware_version': e_mw_version,
                'compute_api_type': self.service_data['compute_api_type'],
                'compute_api_version': e_api_version,
            })
            e.update(self._get_extra_endpoint_info(e_url))
            ret['endpoints'][e_id_url] = e
        return ret

    @_rescope
    def get_templates(self, **kwargs):
        """Return templates/flavors selected accroding to --select-flavors"""
        flavors = {}
        defaults = {'template_platform': 'amd64',
                    'template_network': 'private'}
        defaults.update(self.static.get_template_defaults(prefix=True))
        tpl_sch = defaults.get('template_schema', 'resource')
        URI = 'http://schemas.openstack.org/template/'
        add_all = self.select_flavors == 'all'
        opts_infiniband_k = self.opts.extra_specs_infiniband_key
        opts_infiniband_v = self.opts.extra_specs_infiniband_value
        flavor_infiniband_k = ':'.join([
            'aggregate_instance_extra_specs',
            opts_infiniband_k])
        for flavor in self.nova.flavors.list(detailed=True):
            print(">>> FLAVOR: ", flavor)
            add_pub = self.select_flavors == 'public' and flavor.is_public
            add_priv = (self.select_flavors == 'private' and not
                        flavor.is_public)
            if not (add_all or add_pub or add_priv):
                continue
            aux = defaults.copy()
            flavor_id = str(getattr(flavor, 'id'))
            template_id = '%s%s#%s' % (URI, tpl_sch, self.adapt_id(flavor_id))
            flavor_infiniband_v = flavor.get_keys().get(
                flavor_infiniband_k, False)
            has_infiniband = flavor_infiniband_v == opts_infiniband_v
            aux.update({'template_id': template_id,
                        'template_native_id': flavor_id,
                        'template_memory': flavor.ram,
                        'template_ephemeral': flavor.ephemeral,
                        'template_disk': flavor.disk,
                        'template_cpu': flavor.vcpus,
                        'template_infiniband': has_infiniband})
            flavors[flavor.id] = aux
        return flavors

    @_rescope
    def get_images(self, **kwargs):
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
            aux_img.update(image)

            img_id = image.get("id")
            image_descr = image.get('vmcatcher_event_dc_description',
                                    image.get('vmcatcher_event_dc_title'))
            marketplace_id = image.get('vmcatcher_event_ad_mpuri',
                                       image.get('marketplace'))

            if not marketplace_id:
                if self.all_images:
                    link = urljoin(self.glance.http_client.get_endpoint(),
                                   image.get("file"))
                    marketplace_id = link
                else:
                    continue

            aux_img.update({
                'image_native_id': img_id,
                'image_id': '%s%s#%s' % (URI, img_sch, self.adapt_id(img_id)),
                'image_name': image.get('name'),
                'image_os_name': image.get('os_distro'),
                'image_os_version': image.get('os_version'),
                'image_version': image.get('image_version'),
                'image_description': image_descr,
                'image_marketplace_id': marketplace_id,
            })
            images[img_id] = aux_img
        return images

    @_rescope
    def get_instances(self, **kwargs):
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
    def get_compute_quotas(self, **kwargs):
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
            project_quotas = self.nova.quotas.get(self.project_id)
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
    def _default_if_none(key_value, endpoint_type, defaults, key_suffix):
        """Get default value if None

        Build key from endpoint_type and return value from default
        """
        if key_value is not None:
            field_value = key_value
        else:
            field_name = 'compute_%s_%s' % (endpoint_type, key_suffix)
            field_value = defaults.get(field_name, 'UNKNOWN')
        return field_value

    @staticmethod
    def adapt_id(term_name):
        '''No changes for the ids in default OpenStack.'''
        return term_name

    @staticmethod
    def populate_parser(parser):
        plugins = loading_base.get_available_plugin_names()
        default_auth = "v3password"

        parser.add_argument('--os-auth-type',
                            '--os-auth-plugin',
                            metavar='<name>',
                            default=utils.env('OS_AUTH_TYPE',
                                              default=default_auth),
                            choices=plugins,
                            help='Authentication type to use, available '
                                 'types are: %s' % ", ".join(plugins))

        # arguments come from session and plugins
        loading_session.register_argparse_arguments(parser)
        for plugin_name in plugins:
            plugin = loading_base.get_plugin_loader(plugin_name)
            # NOTE(aloga): we do not want a project to be passed from the
            # CLI, as we will iterate over it for each configured VO and
            # project. However, as the plugin is expecting them when
            # parsing the arguments we need to set them to None before
            # calling the load_auth_from_argparse_arguments method in the
            # __init__ method of this class.
            for opt in filter(lambda x: x.name not in ("project-name",
                                                       "project-id"),
                              plugin.get_options()):
                parser.add_argument(*opt.argparse_args,
                                    default=opt.argparse_default,
                                    metavar='<auth-%s>' % opt.name,
                                    help=opt.help,
                                    dest='os_%s' % opt.dest.replace("-", "_"))

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
            '--select-flavors',
            default='all',
            choices=['all', 'public', 'private'],
            help='Select all (default), public or private flavors/templates.')

        parser.add_argument(
            '--all-images',
            action='store_true',
            default=False,
            help=('If set, include information about all images (including '
                  'snapshots), otherwise only publish images with cloudkeeper '
                  'metadata, ignoring the others.'))
        parser.add_argument(
            '--extra-specs-infiniband-key',
            metavar='EXTRA_SPECS_KEY',
            default='infiniband',
            help=('When Infiniband is supported, this option specifies the '
                  'key id in the flavor\'s extra-specs field'))
        parser.add_argument(
            '--extra-specs-infiniband-value',
            metavar='EXTRA_SPECS_VALUE',
            default='true',
            help=('When Infiniband is supported, this option specifies the '
                  'value to search for/match in the flavor\'s extra-specs '
                  'field'))
