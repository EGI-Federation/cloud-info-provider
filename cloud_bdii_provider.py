#!/usr/bin/env python
#
# This (naive) script produces a text to be used in a LDIF file to be published by the Resource Provider LDAP server.
# Edit the information below with your site information then run the script.
#
# Report any bug to the FedClouds task force.
#

##
## Interfaces info
##
interface = {
    'IaaS_api': 'OCCI',
    'IaaS_api_version': '1.1',
    'IaaS_api_endpoint_technology': 'REST',
    'IaaS_api_authorization_method': 'X509-VOMS',
    'STaaS_api': 'CDMI',
    'STaaS_api_version': '1.0.1',
    'STaaS_api_endpoint_technology': 'REST',
    'STaaS_api_authorization_method': 'X509-VOMS',
}

##
## Site INFOS
##
provider = {
    'site_name': 'PRISMA-INFN-BARI',
    'www': 'http://recas-pon.ba.infn.it/',
    'country': 'IT',
    'site_longitude': '16.88',
    'site_latitude': '41.11',
    'affiliated_ngi': 'NGI_IT',
    'user_support_contact': 'prisma-iaas-open-support@lists.ba.infn.it',
    'general_contact': 'prisma-iaas-open-support@lists.ba.infn.it',
    'sysadmin_contact': 'prisma-iaas-open-support@lists.ba.infn.it',
    'security_contact': 'prisma-iaas-open-support@lists.ba.infn.it',
    'production_level': 'production', # e.g. 'production'
    'site_bdii_host': 'prisma-cloud.ba.infn.it',
    'site_bdii_port': '2170',


    'site_total_cpu_cores': '300',
    'site_total_ram_gb': '600',
    'site_total_storage_gb': '51200',

    'iaas_middleware': 'OpenStack Nova',
    'iaas_middleware_version': 'havana',
    'iaas_middleware_developer': 'OpenStack',
    'iaas_hypervisor': 'KVM',
    'iaas_hypervisor_version': '1.5.0',
    'iaas_capabilities': ('cloud.managementSystem','cloud.vm.uploadImage'),
}

provider['iaas_endpoints'] = (
    {
        'endpoint_url':'https://prisma-cloud.ba.infn.it:8787',
        'endpoint_interface': interface['IaaS_api'],
        'service_type_name': provider['iaas_middleware'],
        'service_type_version': provider['iaas_middleware_version'],
        'service_type_developer': provider['iaas_middleware_developer'],
        'interface_version': interface['IaaS_api_version'],
        'endpoint_technology': interface['IaaS_api_endpoint_technology'],
        'auth_method': interface['IaaS_api_authorization_method']
    },
)


provider['os_tpl'] = (
    {
        'image_name': 'SL64-x86_64',
        'image_version': '1.0',
        'marketplace_id': 'http://appdb.egi.eu/store/vm/image/2c24de6c-e385-49f1-b64f-f9ff35e70f43:9/xml',
        'occi_id': 'os#ef13c0be-4de6-428f-ad5b-8f32b31a54a1',
        'os_family': 'linux',
        'os_name': 'SL',
        'os_version': '6.4',
        'platform': 'amd64'
    },
    {
        'image_name': 'ubuntu-precise-server-amd64',
        'image_version': '1.0',
        'marketplace_id': 'http://appdb.egi.eu/store/vm/image/703157c0-e509-44c8-8371-58beb44d80d6:8/xml',
        'occi_id': 'os#c0a2f9e0-081a-419c-b9a5-8cb03b1decb5',
        'os_family': 'linux',
        'os_name': 'Ubuntu',
        'os_version': '12.04',
        'platform': 'amd64'
    },
    {
        'image_name': 'CernVM3',
        'image_version': '3.1.1.7',
        'marketplace_id': 'http://appdb.egi.eu/store/vm/image/dfb2f33e-ba3f-4c5a-a387-6257e8558ba1:24/xml',
        'occi_id': 'os#5364f77a-e1cb-4a6c-862e-96dc79c4ef67',
        'os_family': 'linux',
        'os_name': 'SL',
        'os_version': '6.4',
        'platform': 'amd64'
    },
)

provider['resource_tpl'] = (
    {
        'occi_id': 'resource#tiny-with-disk',
        'memory': '512',
        'cpu': '1',
        'platform': 'amd64',
        'network': 'public'
    },
    {
        'occi_id': 'resource#small',
        'memory': '1024',
        'cpu': '1',
        'platform': 'amd64',
        'network': 'public'
    },
    {
        'occi_id': 'resource#medium',
        'memory': '4096',
        'cpu': '2',
        'platform': 'amd64',
        'network': 'public'
    },
    {
        'occi_id': 'resource#large',
        'memory': '8196',
        'cpu': '4',
        'platform': 'amd64',
        'network': 'public'},
    {
        'occi_id': 'resource#extra_large',
        'memory': '16384',
        'cpu': '8',
        'platform': 'amd64',
        'network': 'public'
    },
)

#STorage-as-a-Service
provider['staas_middleware'] = 'OpenStack Swift' #e.g. CDMI Proxy. Leave empty for no storage service
provider['staas_middleware_version'] = 'havana' #CLOUD_MW version, e.g. 3.0
provider['staas_middleware_developer'] = 'OpenStack' #CLOUD_MW version, e.g. 3.0
provider['staas_capabilities'] = 'cloud.data.upload' # Capabilities must be agreed with the FedClouds task force

provider['staas_endpoints'] = (
    {
        'endpoint_url': 'https://prisma-swift.ba.infn.it:8080',
        'endpoint_interface': interface['STaaS_api'],
        'service_type_name': provider['staas_middleware'],
        'service_type_version': provider['staas_middleware_version'],
        'service_type_developer': provider['staas_middleware_developer'],
        'interface_version': interface['STaaS_api_version'],
        'endpoint_technology': interface['STaaS_api_endpoint_technology'],
        'auth_method': interface['STaaS_api_authorization_method']
    },
)


def storage_endpoint (site_name,endpoint_url,endpoint_interface,capabilities,service_type_name,service_type_version,service_type_developer,interface_version,endpoint_technology, auth_method):
    ''' '''
    text = """
dn: GLUE2EndpointID=%s_%s_%s_%s,GLUE2ServiceID=cloud.storage.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
objectClass: GLUE2Entity
objectClass: GLUE2Endpoint
objectClass: GLUE2StorageEndpoint
GLUE2EndpointHealthState: ok
GLUE2EndpointID: %s_%s_%s_%s"""%(endpoint_url,endpoint_interface,interface_version, auth_method, site_name,site_name,endpoint_url,endpoint_interface,interface_version, auth_method)
    text += """
GLUE2EndpointInterfaceName: %s
GLUE2EndpointQualityLevel: production
GLUE2EndpointServiceForeignKey: cloud.storage.%s_service
GLUE2EndpointServingState: production
GLUE2EndpointURL: %s"""%(endpoint_interface,site_name,endpoint_url)
    text +="""
GLUE2StorageEndpointStorageServiceForeignKey: cloud.storage.%s_service
GLUE2EndpointCapability: %s
GLUE2EndpointImplementationName: %s
GLUE2EndpointImplementationVersion: %s
GLUE2EndpointImplementor: %s"""%(site_name,capabilities,service_type_name,service_type_version,service_type_developer)
    text += """
GLUE2EndpointInterfaceVersion: %s
GLUE2EntityOtherInfo: Authn=%s
GLUE2EndpointTechnology: %s"""%(interface_version,auth_method, endpoint_technology)
    text +="""
entryDN: GLUE2EndpointID=%s_%s_%s_%s,GLUE2ServiceID=cloud.storage.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
hasSubordinates: TRUE
modifiersName: o=glue
structuralObjectClass: GLUE2Endpoint
subschemaSubentry: cn=Subschema
"""%(endpoint_url,endpoint_interface,interface_version, auth_method,site_name,site_name)
    return text


def storage_capacity (site_name,total_storage):
    ''' '''
    text = """
dn: GLUE2StorageServiceCapacityID=cloud.storage.%s_capacity,GLUE2ServiceID=cloud.storage.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
objectClass: GLUE2Entity
objectClass: GLUE2StorageServiceCapacity
GLUE2StorageServiceCapacityID: cloud.storage.%s_capacity
GLUE2StorageServiceCapacityType: online
GLUE2StorageServiceCapacityStorageServiceForeignKey: cloud.storage.%s_service
GLUE2StorageServiceCapacityTotalSize: %s
entryDN: GLUE2StorageServiceCapacityID=cloud.storage.%s_capacity,GLUE2ServiceID=cloud.storage.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
hasSubordinates: TRUE
modifiersName: o=glue
structuralObjectClass: GLUE2StorageServiceCapacity
subschemaSubentry: cn=Subschema
"""%(site_name,site_name,site_name,site_name,site_name,total_storage,site_name,site_name,site_name)
    return text


####


class BaseBDII(object):
    def __init__(self, templates, info):
        self.info = info
        self.ldif = {}
        self.templates = templates
        for tpl in self.templates:
            with open('templates/%s.ldif' % tpl, 'r') as f:
                self.ldif[tpl] = f.read()

    def _format_template(self, template, info=None, extra={}):
        if not info:
            info = self.info
        fd = info.copy()
        fd.update(extra)
        return self.ldif.get(template, "") % fd


class StaaSBDII(BaseBDII):
    def __init__(self, provider):
        self.provider_info = provider
        templates = ("storage_service",)
        super(StaaSBDII, self).__init__(templates, provider)

    def render(self):
        output = []
        output.append(self._format_template("storage_service"))
        return "\n".join(output)


class IaaSBDII(BaseBDII):
    def __init__(self, provider):
        self.provider_info = provider
        templates = ("compute_service", "compute_endpoint", "execution_environment", "application_environment")
        super(IaaSBDII, self).__init__(templates, provider)

    def render(self):
        output = []
        output.append(self._format_template("compute_service"))

        for endpoint in self.provider_info['iaas_endpoints']:
            output.append(self._format_template("compute_endpoint", extra=endpoint))

        for ex_env in self.provider_info['resource_tpl']:
            output.append(self._format_template("execution_environment", extra=ex_env))

        for app_env in self.provider_info['os_tpl']:
            output.append(self._format_template("application_environment", extra=app_env))

        return "\n".join(output)


class CloudBDII(BaseBDII):
    def __init__(self, provider):
        self.services = []
        if provider.get('iaas_endpoints', None):
            self.services.append(IaaSBDII(provider))

        if provider.get('staas_endpoints', None):
            self.services.append(StaaSBDII(provider))

        self.templates = ("headers", "domain", "bdii")
        super(CloudBDII, self).__init__(self.templates, provider)

    def render(self):
        output = []
        for tpl in self.templates:
            output.append(self._format_template(tpl))
        for i in self.services:
            output.append(i.render())
        return "\n".join(output)


def main():
    # NOTE(aloga): Refactored code >>>>
    bdii = CloudBDII(provider)
    print bdii.render()
    # NOTE(aloga): Refactored code <<<<

    if provider['staas_endpoints']:
        for endpoint in provider['staas_endpoints']:
            print storage_endpoint(provider['site_name'],endpoint['endpoint_url'],endpoint['endpoint_interface'],provider['staas_capabilities'],endpoint['service_type_name'],endpoint['service_type_version'],endpoint['service_type_developer'],endpoint['interface_version'],endpoint['endpoint_technology'],endpoint['auth_method'])
        print storage_capacity(provider['site_name'],provider['site_total_storage_gb'])

if __name__ == "__main__":
    main()
