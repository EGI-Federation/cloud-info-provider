import cgi
import collections
import os.path
import socket


class Data(object):
    @property
    def site_info(self):
        return {
            'suffix': 'o=glue',
            'site_name': 'SITE_NAME',
        }

    @property
    def site_info_full(self):
        return {
            'suffix': 'GLUE2DomainID=SITE_NAME,o=glue',
            'site_name': 'SITE_NAME',
            'site_url': 'http://site.url.example.org/',
            'site_ngi': 'NGI_FOO',
            'site_country': 'ES',
            'site_longitude': 0.0,
            'site_latitude': 0.0,
            'site_general_contact': 'general-support@example.org',
            'site_sysadmin_contact': 'support@example.org',
            'site_security_contact': 'security-support@example.org',
            'site_user_support_contact': 'user-support@example.org',
            'site_production_level': 'production',
            'site_bdii_host': 'site.bdii.example.org',
            'site_bdii_port': 2170,
        }

    @property
    def storage_endpoints(self):
        return {
            'endpoints': {
                'https://storage-service01.example.org:8080': {
                    'storage_api_authn_method': 'X509-VOMS',
                    'storage_api_endpoint_technology': 'REST',
                    'storage_api_type': 'CDMI',
                    'storage_api_version': '1.0.1',
                    'storage_production_level': 'production',
                },
                'https://storage-service02.example.org:8080': {
                    'storage_api_authn_method': 'X509-VOMS',
                    'storage_api_endpoint_technology': 'REST',
                    'storage_api_type': 'CDMI',
                    'storage_api_version': '1.0.1',
                    'storage_production_level': 'testing',
                }
            },
            'storage_capabilities': ['cloud.data.upload'],
            'storage_middleware': 'A Middleware',
            'storage_middleware_developer': 'Middleware Developer',
            'storage_middleware_version': 'v1.0',
            'storage_total_storage': 0,
            'storage_service_production_level': 'production',
            'storage_service_name': socket.getfqdn(),
        }

    @property
    def compute_endpoints(self):
        return {
            'compute_capabilities': ['cloud.managementSystem',
                                     'cloud.vm.uploadImage'],
            'compute_hypervisor': 'Foo Hypervisor',
            'compute_hypervisor_version': '0.0.0',
            'compute_middleware': 'A Middleware',
            'compute_middleware_developer': 'Middleware Developer',
            'compute_middleware_version': 'v1.0',
            'compute_total_cores': 0,
            'compute_total_ram': 0,
            'compute_service_production_level': 'production',
            'compute_service_name': socket.getfqdn(),
            'endpoints': {
                'https://cloud-service01.example.org:8787': {
                    'compute_api_authn_method': 'X509-VOMS',
                    'compute_api_endpoint_technology': 'REST',
                    'compute_api_type': 'OCCI',
                    'compute_api_version': 1.1,
                    'compute_production_level': 'unknown',
                },
                'https://cloud-service02.example.org:8787': {
                    'compute_api_authn_method': 'X509',
                    'compute_api_endpoint_technology': 'REST',
                    'compute_api_type': 'OCCI',
                    'compute_api_version': 1.1,
                    'compute_production_level': 'testing',
                },
                'https://cloud-service03.example.org:8787': {
                    'compute_api_authn_method': 'User/Password',
                    'compute_api_endpoint_technology': 'REST',
                    'compute_api_type': 'OCCI',
                    'compute_api_version': 1.1,
                    'compute_production_level': 'unknown',
                }
            }
        }

    @property
    def compute_images(self):
        return {
            'os_tpl#foobarid': {
                'image_name': 'Foo Image',
                'image_version': 1.0,
                'image_marketplace_id': (
                    'http://url.to.marketplace.id.example.org/foo/bar'
                ),
                'image_os_family': 'linux',
                'image_os_name': 'Cirros',
                'image_os_version': 1.0,
                'image_platform': 'amd64',
            },
        }

    @property
    def compute_templates(self):
        return {
            'resource_tpl#extra_large': {
                'template_cpu': 8,
                'template_memory': 16384,
                'template_network': 'public',
                'template_platform': 'amd64'
            },
            'resource_tpl#large': {
                'template_cpu': 4,
                'template_memory': 8196,
                'template_network': 'public',
                'template_platform': 'amd64'
            },
            'resource_tpl#medium': {
                'template_cpu': 2,
                'template_memory': 4096,
                'template_network': 'public',
                'template_platform': 'amd64'
            },
            'resource_tpl#small': {
                'template_cpu': 1,
                'template_memory': 1024,
                'template_network': 'public',
                'template_platform': 'amd64'
            }
        }


DATA = Data()


class OpenStackFakes(object):
    def __init__(self):
        Flavor = collections.namedtuple(
            'Flavor',
            ('id', 'name', 'ram', 'vcpus', 'is_public', 'disk'))

        flavors = (
            {
                'id': 1,
                'name': 'm1.foo',
                'ram': 10,
                'vcpus': 20,
                'is_public': True,
                'disk': 0,
            },
            {
                'id': 2,
                'name': 'm1 bar',
                'ram': 20,
                'vcpus': 30,
                'is_public': False,
                'disk': 10,
            },
            {
                'id': 3,
                'name': 'm1.baz',
                'ram': 2,
                'vcpus': 3,
                'is_public': True,
                'disk': 5,
            },
        )

        self.flavors = [Flavor(**f) for f in flavors]

        Image = collections.namedtuple(
            'Image',
            ('name', 'id', 'links', 'metadata'))

        # XXX add docker information
        # XXX some fake images should include more information from AppDB
        images = (
            {
                'name': 'fooimage',
                'id': 'foo.id',
                'metadata': {},
                'links': [{
                    'type': 'application/vnd.openstack.image',
                    'href': 'http://example.org/',
                }]
            },
            {
                'name': 'barimage',
                'id': 'bar id',
                'metadata': {},
                'links': []
            },
            {
                'name': 'bazimage',
                'id': 'baz id',
                'metadata': {
                    'docker_id': 'sha1:xxxxxxxxxxxxxxxxxxxxxxxxxx',
                    'docker_tag': 'latest',
                    'docker_name': 'test/image',
                },
                'links': []
            },
        )
        self.images = [Image(**i) for i in images]

        catalog = (
            (
                'nova', 'compute', '1b7f14c87d8c42ad962f4d3a5fd13a77',
                'https://cloud.example.org:8774/v1.1/ce2d'
            ),
            (
                'ceilometer', 'metering', '5acd54c66f3641fd948fa363fa5c9d0a',
                'https://cloud.example.org:8777/'
            ),
            (
                'nova-volume', 'volume', '5afb318eedd44a71ab8362cc917f929b',
                'http://cloudvolume01.example.org:8776/v1/ce2d'
            ),
            (
                'ec2', 'ec2', '93ccd85773d24f238c6f2fab802cfd06',
                'https://cloud.example.org:8773/services/Admin'
            ),
            (
                'occi', 'occi', '03e087c8fb3b495c9a360bcba3abf914',
                'https://cloud.example.org:8787/'
            ),
            (
                'keystone', 'identity', '510c45b865ba4f40997b91a85552f3e2',
                'https://keystone.example.org:35357/v2.0'
            ),
            (
                'glance', 'image', '0ceb45ad3ee84f9ca5c1809b07715d40',
                'https://glance.example.org:9292/',
            ),
        )

        self.catalog = {
            'access': {
                'serviceCatalog': [],
            }
        }

        for name, type_, id_, url in catalog:
            service = {
                'endpoints': [{
                    'adminURL': url,
                    'publicURL': url,
                    'internalURL': url,
                    'id': id_,
                    'region': 'RegionOne'
                }],
                'endpoints_links': [],
                'name': name,
                'type': type_
            }
            self.catalog['access']['serviceCatalog'].append(service)

OS_FAKES = OpenStackFakes()


class OpenNebulaFakes(object):
    response_doc = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<methodResponse>'
        '<params>'
        '<param><value><array><data>'
        '<value><boolean>1</boolean></value>'
        '<value><string>'
        '%(response)s'
        '</string></value>'
        '<value><i4>0</i4></value>'
        '</data></array></value></param>'
        '</params>'
        '</methodResponse>'
    )

    def __init__(self):
        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, 'one.imagepool.info.xml'), 'r') as f:
            self.imagepool = f.read()

        self.imagepool = cgi.escape(self.imagepool)
        self.imagepool = self.response_doc % {'response': self.imagepool}

        with open(os.path.join(cwd, 'one.templatepool.info.xml'), 'r') as f:
            self.templatepool = f.read()

        self.templatepool = cgi.escape(self.templatepool)
        self.templatepool = self.response_doc % {'response': self.templatepool}

ONE_FAKES = OpenNebulaFakes()
