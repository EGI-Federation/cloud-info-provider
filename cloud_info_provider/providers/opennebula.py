import base64
import copy
import json
import os

from cloud_info_provider import exceptions
from cloud_info_provider import providers
from cloud_info_provider.providers import ssl_utils
from cloud_info_provider import utils

try:
    import defusedxml.ElementTree
    from defusedxml import xmlrpc
    from six.moves import xmlrpc_client as xmlrpclib  # nosec
    # Protect the XMLRPC parser from various XML-based threats
    xmlrpc.monkey_patch()
except ImportError:
    msg = 'Cannot import defusedxml ElementTree and/or xmlrpc.'
    raise exceptions.OpenNebulaProviderException(msg)


class OpenNebulaBaseProvider(providers.BaseProvider):
    def __init__(self, opts):
        super(OpenNebulaBaseProvider, self).__init__(opts)

        self.opts = opts
        self.on_auth = opts.on_auth
        self.on_rpcxml_endpoint = opts.on_rpcxml_endpoint
        self.all_images = opts.all_images

        if not self.on_auth:
            msg = ('ERROR, You must provide a on_auth '
                   'via either --on-auth or env[ON_AUTH]')
            raise exceptions.OpenNebulaProviderException(msg)

        if not self.on_rpcxml_endpoint:
            msg = ('You must provide an OpenNebula RPC-XML '
                   'endpoint via either --on-rpcxml-endpoint or'
                   ' env[ON_RPCXML_ENDPOINT]')
            raise exceptions.OpenNebulaProviderException(msg)

        self.static = providers.static.StaticProvider(opts)
        self.xml_parser = defusedxml.ElementTree
        self.server_proxy = xmlrpclib.ServerProxy(self.on_rpcxml_endpoint)

    def get_compute_shares(self, **kwargs):
        shares = self.static.get_compute_shares(prefix=True)
        for vo, share in shares.items():
            auth = share.get('auth', dict())
            # default group name == vo name
            if 'group' not in auth:
                auth['group'] = vo
            share['auth'] = auth
            share['project'] = auth['group']
        return shares

    def _handle_response(self, response):
        if not response:
            msg = 'Invalid response from OpenNebula\'s XML RPC endpoint'
            raise exceptions.OpenNebulaProviderException(msg)
        if not response[0]:
            raise exceptions.OpenNebulaProviderException(response[1])

        doc = self.xml_parser.fromstring(response[1].encode('utf-8'))
        if doc is None:
            msg = 'Invalid XML in response from OpenNebula\'s XML RPC endpoint'
            raise exceptions.OpenNebulaProviderException(msg)

        objects = {}
        for obj in doc.getchildren():
            objects[self._get_xml_string(obj, 'ID')] = \
                self._recurse_dict(obj)[1]
        return objects

    def _get_one_templates(self):
        response = self.server_proxy.one.templatepool.info(
            self.on_auth, -3, -1, -1)
        return self._handle_response(response)

    def _get_one_images(self):
        response = self.server_proxy.one.imagepool.info(
            self.on_auth, -3, -1, -1)
        return self._handle_response(response)

    def _get_one_documents(self, document_type):
        response = self.server_proxy.one.documentpool.info(
            self.on_auth, -3, -1, -1, document_type)
        return self._handle_response(response)

    def get_images(self, **kwargs):
        img_fields = {
            'image_name': None,
            'image_description': None,
            'image_version': None,
            'image_marketplace_id': None,
            'image_id': None,
            'image_os_family': None,
            'image_os_name': None,
            'image_os_version': None,
            'image_platform': 'amd64',
            'other_info': [],
        }
        defaults = self.static.get_image_defaults(prefix=True)
        img_schema = defaults.get('image_schema', 'template')
        group_name = kwargs.get('auth', {}).get('group', None)

        templates = {}
        for tpl_id, tpl in self._get_one_templates().items():
            if group_name and group_name != tpl.get('gname'):
                continue
            aux_tpl = copy.deepcopy(img_fields)
            aux_tpl.update(defaults)

            aux_tpl['image_name'] = tpl['name']
            aux_tpl['image_id'] = '%s#%s' % (img_schema, tpl_id)

            template = tpl.get('template', {})
            aux_tpl.update({
                'image_marketplace_id': template.get(
                    'cloudkeeper_appliance_mpuri'),
                'image_description': template.get(
                    'cloudkeeper_appliance_description'),
                'image_version': template.get(
                    'cloudkeeper_appliance_version'),
                'image_platform': template.get(
                    'cloudkeeper_appliance_architecture'),
            })

            base_mpuri = None
            if template.get('cloudkeeper_appliance_base_mpuri'):
                # cloudkeeper 2.x
                base_mpuri = template['cloudkeeper_appliance_base_mpuri']
            elif template.get('cloudkeeper_appliance_attributes'):
                # cloudkeeper 1.x
                encoded_attrs = template['cloudkeeper_appliance_attributes']
                ck_attrs = json.loads(
                    base64.b64decode(encoded_attrs).decode('utf-8'))
                base_mpuri = ck_attrs.get('ad:base_mpuri')

            if base_mpuri:
                aux_tpl['other_info'].append('base_mpuri=%s' % base_mpuri)

            if not (self.all_images or aux_tpl['image_marketplace_id']):
                continue

            templates[tpl_id] = aux_tpl
        return templates

    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            '--on-auth',
            metavar='<auth>',
            default=utils.env('ON_AUTH') or 'oneadmin:opennebula',
            help=('Specify authorization information. For core drivers, '
                  'it should be <username>:<password>. '
                  'Defaults to env[ON_USERNAME] or oneadmin:opennebula.'))

        parser.add_argument(
            '--on-rpcxml-endpoint',
            metavar='<auth-url>',
            default=utils.env('ON_RPCXML_ENDPOINT')
                    or 'http://localhost:2633/RPC2',
            help=('Specify OpenNebula XML RPC endpoint. '
                  'Defaults to env[ON_RPCXML_ENDPOINT]'
                  ' or http://localhost:2633/RPC2.'))

        parser.add_argument(
            '--all-images',
            action='store_true',
            default=False,
            help=('If set, include information about all images (including '
                  'snapshots), otherwise only publish images with cloudkeeper '
                  'metadata, ignoring the others.'))

    @staticmethod
    def _recurse_dict(element):
        return (element.tag.lower(),
                dict(map(OpenNebulaProvider._recurse_dict, element))
                or element.text)

    @staticmethod
    def _get_xml_string(xml, tag):
        result = xml.find(tag)
        return result.text if result is not None else None

    @staticmethod
    def _traverse(tree, *keys):
        tc = tree
        for key in keys:
            if tc is None:
                return None
            tc = tc.get(key)
        return tc


class OpenNebulaProvider(OpenNebulaBaseProvider):
    def __init__(self, opts):
        super(OpenNebulaProvider, self).__init__(opts)


class OpenNebulaROCCIProvider(OpenNebulaBaseProvider):
    def __init__(self, opts):
        self.rocci_template_dir = opts.rocci_template_dir
        self.rocci_remote_templates = opts.rocci_remote_templates
        if not self.rocci_template_dir and not self.rocci_remote_templates:
            msg = ('ERROR, You must provide a rocci_template_dir '
                   'via --rocci-template-dir')
            raise exceptions.OpenNebulaProviderException(msg)
        self.ca_info = {}
        super(OpenNebulaROCCIProvider, self).__init__(opts)

    def _get_endpoint_ca_information(self, url, **kwargs):
        if url not in self.ca_info:
            ca_info = ssl_utils.get_endpoint_ca_information(url, **kwargs)
            self.ca_info[url] = ca_info
        return self.ca_info[url]

    def get_compute_endpoints(self, **kwargs):
        epts = dict()
        static_epts = self.static.get_compute_endpoints(**kwargs)
        for url, static_ept in static_epts['endpoints'].items():
            ept = static_ept.copy()
            ca_info = self._get_endpoint_ca_information(url)
            ept.update({
                'endpoint_trusted_cas': ca_info['trusted_cas'],
                'endpoint_issuer': ca_info['issuer'],
            })
            epts[url] = ept
        return {'endpoints': epts}

    def get_templates(self, **kwargs):
        """Get flavors from rOCCI-server configuration."""
        template = {
            'template_id': None,
            'template_cpu': None,
            'template_memory': None,
            'template_description': None,
            'template_disk': None,
            'template_platform': 'amd64',
            'template_network': 'private',
        }
        template.update(self.static.get_template_defaults(prefix=True))

        if self.rocci_remote_templates:
            group_name = kwargs.get('auth', {}).get('group', None)
            templates = self.remote_templates(template, group_name)
        else:
            templates = self.local_templates(template)

        return templates

    def local_templates(self, template):
        templates = {}
        for mxn_file in self._absolute_file_paths(self.rocci_template_dir):
            mxn = self._read_mixin(mxn_file)

            occi_attrs = self._traverse(mxn, 'attributes', 'occi', 'compute')
            if not occi_attrs:
                msg = 'Failed to get compute attributes' \
                    ' for mixin in %s' % (mxn_file)
                raise exceptions.OpenNebulaProviderException(msg)

            flid = '%s#%s' % (mxn['scheme'].rstrip('#'), mxn['term'])
            cores = self._traverse(occi_attrs, 'cores', 'Default') or 0
            memory = self._traverse(occi_attrs, 'memory', 'Default') or 0
            disk = self._traverse(
                occi_attrs, 'ephemeral_storage', 'size', 'Default') or 0

            aux = template.copy()
            aux.update({
                'template_id': flid,
                'template_cpu': cores,
                'template_memory': int(memory * 1024),
                'template_description': mxn['title'],
                'template_disk': disk,
            })

            templates[aux['template_id']] = aux

        return templates

    def remote_templates(self, template, group_name):
        document_type = 999  # TODO(bparak): configurable?

        templates = {}
        # TODO(enolfc): cache info from ONE?
        for doc in self._get_one_documents(document_type).values():
            document = json.loads(doc['template']['body'])
            if group_name and group_name != doc.get('gname'):
                continue

            aux = template.copy()
            aux.update({
                'template_id': document['identifier'],
                'template_cpu': document['occi.compute.cores'],
                'template_memory': int(document['occi.compute.memory'] * 1024),
                'template_description': document['title'],
                'template_disk':
                    document['occi.compute.ephemeral_storage.size'],
            })

            templates[aux['template_id']] = aux

        return templates

    @staticmethod
    def _absolute_file_paths(directory):
        for dirpath, _, filenames in os.walk(directory):
            for f in filenames:
                yield os.path.abspath(os.path.join(dirpath, f))

    @staticmethod
    def _read_mixin(json_file):
        with open(json_file, 'r') as fd:
            jd = json.load(fd)

        first = jd.get('mixins', [])[0]
        if not first:
            msg = 'Failed to find a mixin in %s' % (json_file)
            raise exceptions.OpenNebulaProviderException(msg)
        return first

    @staticmethod
    def populate_parser(parser):
        super(OpenNebulaROCCIProvider,
              OpenNebulaROCCIProvider).populate_parser(parser)

        parser.add_argument(
            '--rocci-template-dir',
            metavar='<rocci-template-dir>',
            default='/etc/occi-server/backends/opennebula'
                    '/fixtures/resource_tpl',
            help='Location of the rOCCI-server resource template definitions.')

        parser.add_argument(
            '--rocci-remote-templates',
            action='store_true',
            default=False,
            help=('If set, resource template definitions will be retrieved '
                  'via OCA, not from a local directory.'))
