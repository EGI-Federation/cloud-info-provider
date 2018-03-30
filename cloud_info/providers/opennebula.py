import json
import os
import string

from cloud_info import exceptions
from cloud_info import providers
from cloud_info import utils

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
        self.cloudkeeper_images = opts.cloudkeeper_images

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

    def _handle_response(self, response):
        if not response:
            msg = 'Invalid response from OpenNebula\'s XML RPC endpoint'
            raise exceptions.OpenNebulaProviderException(msg)
        if not response[0]:
            raise exceptions.OpenNebulaProviderException(response[1])

        doc = self.xml_parser.fromstring(response[1])
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

    def get_images(self):
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
        img_schema = defaults.get('image_schema', 'template')

        templates = {}
        for tpl_id, tpl in self._get_one_templates().items():
            aux_tpl = template.copy()
            aux_tpl.update(defaults)

            aux_tpl['image_name'] = tpl['name']
            aux_tpl['image_id'] = self._gen_id(tpl['name'], tpl_id, img_schema)

            if 'template' in tpl:
                aux_tpl['image_marketplace_id'] = tpl['template'].get(
                    'cloudkeeper_appliance_mpuri')
                aux_tpl['image_description'] = tpl['template'].get(
                    'cloudkeeper_appliance_description')
                aux_tpl['image_version'] = tpl['template'].get(
                    'cloudkeeper_appliance_version')
                aux_tpl['image_platform'] = tpl['template'].get(
                    'cloudkeeper_appliance_architecture')

            if self.cloudkeeper_images:
                if not aux_tpl['image_marketplace_id']:
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
            '--cloudkeeper-images', '--vmcatcher-images',
            action='store_true',
            default=False,
            help=('If set, include only information on images that '
                  'have cloudkeeper metadata, ignoring the others.'))

    @staticmethod
    def _gen_id(image_name, image_id, schema):
        # FIXME(aloga): make this an abstrac method
        """Generate image id."""
        return '%s#%s' % (schema, image_id)

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


class IndigoONProvider(OpenNebulaBaseProvider):
    def __init__(self, opts):
        super(IndigoONProvider, self).__init__(opts)

    def get_templates(self):
        template = {
            'template_id': None,
            'template_name': None,
            'template_description': None,
            'template_memory': None,
            'template_cpu': None,
            'template_disk': None,
            'template_platform': 'amd64',
            'template_network': 'private',
        }
        defaults = self.static.get_image_defaults(prefix=True)
        img_schema = defaults.get('template_schema', 'template')

        templates = {}
        for tpl_id, tpl in self._get_one_templates().items():
            aux_tpl = template.copy()
            aux_tpl.update(defaults)

            aux_tpl['template_id'] = self._gen_id(
                tpl['name'], tpl_id, img_schema)
            aux_tpl['template_name'] = tpl['name']

            if 'template' in tpl:
                aux_tpl['template_description'] = tpl['template'].get(
                    'description')
                aux_tpl['template_cpu'] = tpl['template'].get('cpu')
                aux_tpl['template_memory'] = tpl['template'].get('memory')
                aux_tpl['image_marketplace_id'] = tpl['template'].get(
                    'cloudkeeper_appliance_mpuri')
                aux_tpl['image_description'] = tpl['template'].get(
                    'cloudkeeper_appliance_description')
                aux_tpl['image_version'] = tpl['template'].get(
                    'cloudkeeper_appliance_version')

            if self.cloudkeeper_images:
                if not aux_tpl['image_marketplace_id']:
                    continue

            templates[tpl_id] = aux_tpl
        return templates

    def get_images(self):
        image = {
            'image_name': None,
            'image_id': None,
            'image_marketplace_id': None,
            'image_version': None,
            'image_description': None,
        }
        defaults = self.static.get_image_defaults(prefix=True)

        images = {}
        for img_id, img in self._get_one_images().items():
            aux_img = image.copy()
            aux_img.update(defaults)

            aux_img['image_name'] = img['name']
            aux_img['image_id'] = img_id

            if 'template' in img:
                aux = img['template']
                for name, value in aux.items():
                    aux_img[name] = value

                aux_img['image_marketplace_id'] = aux.get(
                    'cloudkeeper_appliance_mpuri')
                aux_img['image_version'] = aux.get(
                    'cloudkeeper_appliance_version')
                aux_img['image_description'] = (
                    aux.get('cloudkeeper_appliance_description') or
                    aux.get('description') or
                    aux.get('cloudkeeper_appliance_title'))

            if self.cloudkeeper_images:
                if not aux_img['image_marketplace_id']:
                    continue

            images[img_id] = aux_img
        return images


class OpenNebulaROCCIProvider(OpenNebulaBaseProvider):
    def __init__(self, opts):
        self.rocci_template_dir = opts.rocci_template_dir
        self.rocci_remote_templates = opts.rocci_remote_templates
        if not self.rocci_template_dir and not self.rocci_remote_templates:
            msg = ('ERROR, You must provide a rocci_template_dir '
                   'via --rocci-template-dir')
            raise exceptions.OpenNebulaProviderException(msg)
        super(OpenNebulaROCCIProvider, self).__init__(opts)

    def get_templates(self):
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
            templates = self.remote_templates(template)
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

    def remote_templates(self, template):
        document_type = 999  # TODO(bparak): configurable?

        templates = {}
        for doc_id, doc in self._get_one_documents(document_type).items():
            document = json.loads(doc['template']['body'])

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

    @staticmethod
    def _gen_id(image_name, image_id, schema):
        """Generate image uiid as rOCCI does."""
        replace_punctuation = utils.maketrans(
            string.punctuation + string.whitespace,
            '_' * len(string.punctuation + string.whitespace)
        )
        image_name = utils.translate(image_name.lower(),
                                     replace_punctuation).strip('_')
        return '%s#uuid_%s_%s' % (schema, image_name, image_id)
