import os
import sys

def env(*args, **kwargs):
    """
    returns the first environment variable set
    if none are non-empty, defaults to '' or keyword arg default
    """
    for arg in args:
        value = os.environ.get(arg, None)
        if value:
            return value
    return kwargs.get('default', '')

class OpenStackProvider(object):
    def __init__(self, opts):
        try:
            import novaclient.client
        except ImportError:
            print >> sys.stderr, "ERROR: Cannot import nova module."
            sys.exit(1)

        (os_username, os_password, os_tenant_name, os_tenant_id,
            os_auth_url, cacert, insecure) = (
                opts.os_username, opts.os_password,
                opts.os_tenant_name, opts.os_tenant_id,
                opts.os_auth_url, opts.os_cacert, opts.insecure)

        if not os_username:
            print >> sys.stderr, ("ERROR, You must provide a username "
                                  "via either --os-username or "
                                  "env[OS_USERNAME]")
            sys.exit(1)

        if not os_password:
            print >> sys.stderr, ("ERROR, You must provide a password "
                                  "via either --os-password or "
                                  "env[OS_PASSWORD]")
            sys.exit(1)

        if not os_tenant_name and not os_tenant_id:
            print >> sys.stderr, ("You must provide a tenant name "
                                  "or tenant id via --os-tenant-name, "
                                  "--os-tenant-id, env[OS_TENANT_NAME] "
                                  "or env[OS_TENANT_ID]")
            sys.exit(1)

        if not os_auth_url:
            print >> sys.stderr, ("You must provide an auth url "
                                  "via either --os-auth-url or "
                                  "env[OS_AUTH_URL] ")
            sys.exit(1)

        client_cls = novaclient.client.get_client_class("2")
        self.api = client_cls(os_username,
                              os_password,
                              os_tenant_name,
                              tenant_id=os_tenant_id,
                              auth_url=os_auth_url,
                              insecure=insecure,
                              cacert=cacert)

        self.api.authenticate()

    def get_templates(self):
        flavors = []

        for flavor in self.api.flavors.list(detailed=True):
            if not flavor.is_public:
                continue
            aux = {
                'occi_id': 'resource#%s' % flavor.name,
                'memory': flavor.ram,
                'cpu': flavor.vcpus,
                'network': 'public',
                'platform': None,
            }
            flavors.append(aux)
        return flavors

    def get_images(self):
        images = []

        template = {
            'image_name': None,
            'image description': None,
            'image_version': None,
            'marketplace_id': None,
            'occi_id': None,
            'os_family': None,
            'os_name': None,
            'os_version': None,
            'platform': None,
        }

        for image in self.api.images.list(detailed=True):
            aux = template.copy()
            aux.update({'image_name': image.name,
                        'occi_id': 'os#%s' % image.id,
                        'image_description': image.name,
            })
            image.metadata.pop("image_name", None)
            image.metadata.pop("occi_id", None)
            aux.update(image.metadata)
            images.append(aux)
        return images

    @staticmethod
    def populate_parser(parser):
        parser.add_argument('--os-username',
            metavar='<auth-user-name>',
            default=env('OS_USERNAME', 'NOVA_USERNAME'),
            help='Defaults to env[OS_USERNAME].')

        parser.add_argument('--os-password',
            metavar='<auth-password>',
            default=env('OS_PASSWORD', 'NOVA_PASSWORD'),
            help='Defaults to env[OS_PASSWORD].')

        parser.add_argument('--os-tenant-name',
            metavar='<auth-tenant-name>',
            default=env('OS_TENANT_NAME', 'NOVA_PROJECT_ID'),
            help='Defaults to env[OS_TENANT_NAME].')

        parser.add_argument('--os-tenant-id',
            metavar='<auth-tenant-id>',
            default=env('OS_TENANT_ID'),
            help='Defaults to env[OS_TENANT_ID].')

        parser.add_argument('--os-auth-url',
            metavar='<auth-url>',
            default=env('OS_AUTH_URL', 'NOVA_URL'),
            help='Defaults to env[OS_AUTH_URL].')

        parser.add_argument('--os-cacert',
            metavar='<ca-certificate>',
            default=env('OS_CACERT', default=None),
            help='Specify a CA bundle file to use in '
                 'verifying a TLS (https) server certificate. '
                 'Defaults to env[OS_CACERT]')

        parser.add_argument('--insecure',
            default=env('NOVACLIENT_INSECURE', default=False),
            action='store_true',
            help="Explicitly allow novaclient to perform \"insecure\" "
                 "SSL (https) requests. The server's certificate will "
                 "not be verified against any certificate authorities. "
                 "This option should be used with caution.")

