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




def compute_service(site_name,production_level, service_type,capabilities):
    '''Return the GLUE2Service entity
    site_name: Unique name of the cloud-site
    capabilities: list of strings containing the various capabilities
    service_type: IaaS,PaaS,SaaS
    '''
    text = """dn: GLUE2ServiceID=cloud.compute.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
objectClass: GLUE2Entity
objectClass: GLUE2Service
objectClass: GLUE2ComputingService
GLUE2ServiceAdminDomainForeignKey: %s
GLUE2ServiceID: cloud.compute.%s_service
GLUE2ServiceQualityLevel: %s
GLUE2ServiceType: %s
GLUE2ServiceCapability: %s
creatorsName: o=glue
entryDN: GLUE2ServiceID=cloud.compute.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
hasSubordinates: TRUE
modifiersName: o=glue
structuralObjectClass: GLUE2Service
subschemaSubentry: cn=Subschema
"""%(site_name,site_name,site_name,site_name, production_level, 'IaaS',capabilities,site_name,site_name)

    return text


def compute_manager(site_name,product_name,product_version,total_cpus,total_ram,vm_name,vm_version):
  ''' Not intensively used, so far, used only to attach execution environment.'''

  text = """dn: GLUE2ManagerID=cloud.compute.%s_manager,GLUE2ServiceID=cloud.compute.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
objectClass: GLUE2Entity
objectClass: GLUE2Manager
objectClass: GLUE2ComputingManager
GLUE2ManagerID: cloud.compute.%s_manager
GLUE2ManagerProductName: %s
GLUE2ManagerServiceForeignKey: cloud.compute.%s_service
GLUE2ComputingManagerComputingServiceForeignKey: cloud.compute.%s_service
GLUE2EntityName: Cloud Manager at %s
GLUE2ManagerProductVersion: %s
GLUE2ComputingManagerTotalLogicalCPUs: %s
GLUE2ComputingManagerWorkingAreaTotal: %s
creatorsName: o=glue
entryDN: GLUE2ManagerID=cloud.compute.%s_manager,GLUE2ServiceID=cloud.compute.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
hasSubordinates: FALSE
modifiersName: o=glue
structuralObjectClass: GLUE2Manager
subschemaSubentry: cn=Subschema
"""%(site_name,site_name,site_name,site_name,vm_name,site_name,site_name,site_name,vm_version,total_cpus,total_ram,site_name,site_name,site_name)
  return text


def computing_endpoint (site_name,endpoint_url,endpoint_interface,capabilities,service_type_name,service_type_version,service_type_developer,interface_version,endpoint_technology, auth_method):
    ''' '''
    text = """
dn: GLUE2EndpointID=%s_%s_%s_%s,GLUE2ServiceID=cloud.compute.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
objectClass: GLUE2Entity
objectClass: GLUE2Endpoint
objectClass: GLUE2ComputingEndpoint
GLUE2EndpointHealthState: ok
GLUE2EndpointID: %s_%s_%s_%s"""%(endpoint_url,endpoint_interface,interface_version, auth_method, site_name,site_name,endpoint_url,endpoint_interface,interface_version, auth_method)
    text += """
GLUE2EndpointInterfaceName: %s
GLUE2EndpointQualityLevel: production
GLUE2EndpointServiceForeignKey: cloud.compute.%s_service
GLUE2EndpointServingState: production
GLUE2EndpointURL: %s"""%(endpoint_interface,site_name,endpoint_url)
    text +="""
GLUE2ComputingEndpointComputingServiceForeignKey: cloud.compute.%s_service
GLUE2EndpointCapability: %s
GLUE2EndpointImplementationName: %s
GLUE2EndpointImplementationVersion: %s
GLUE2EndpointImplementor: %s"""%(site_name,capabilities,service_type_name,service_type_version,service_type_developer)
    text += """
GLUE2EndpointInterfaceVersion: %s
#GLUE2EndpointSemantics:
#GLUE2EndpointSupportedProfile:
GLUE2EntityOtherInfo: Authn=%s
GLUE2EndpointTechnology: %s"""%(interface_version,auth_method, endpoint_technology)
    text +="""
entryDN: GLUE2EndpointID=%s_%s_%s_%s,GLUE2ServiceID=cloud.compute.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
hasSubordinates: TRUE
modifiersName: o=glue
structuralObjectClass: GLUE2Endpoint
subschemaSubentry: cn=Subschema
"""%(endpoint_url,endpoint_interface,interface_version, auth_method,site_name,site_name)
    return text


def execution_environment (site_name,memory,occi_id,platform,cpu,network):
    ''' '''
    text = """dn: GLUE2ResourceID=%s_%s,GLUE2ServiceID=cloud.compute.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
objectClass: GLUE2Entity
objectClass: GLUE2Resource
objectClass: GLUE2ExecutionEnvironment
GLUE2ExecutionEnvironmentConnectivityIn: TRUE
GLUE2ExecutionEnvironmentConnectivityOut: TRUE
GLUE2ExecutionEnvironmentVirtualMachine: TRUE
GLUE2ExecutionEnvironmentMainMemorySize:%s
GLUE2ExecutionEnvironmentPlatform: %s
GLUE2ExecutionEnvironmentOSFamily: linux
GLUE2ResourceManagerForeignKey: cloud.compute.%s_manager
GLUE2EntityName: %s
GLUE2ExecutionEnvironmentComputingManagerForeignKey: cloud.compute.%s_manager
GLUE2ExecutionEnvironmentCPUModel: %s
GLUE2ExecutionEnvironmentCPUMultiplicity: multicpu-multicore
GLUE2ExecutionEnvironmentCPUVendor: %s
GLUE2ExecutionEnvironmentLogicalCPUs: %s
GLUE2ExecutionEnvironmentPhysicalCPUs: %s
creatorsName: o=glue
entryDN: GLUE2ResourceID=%s,GLUE2ServiceID=cloud.compute.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
hasSubordinates: TRUE
modifiersName: o=glue
structuralObjectClass: GLUE2Resource
subschemaSubentry: cn=Subschema
"""%(site_name,occi_id,site_name,site_name,memory,platform,site_name,occi_id,site_name,'virtual model','virtual vendor',cpu,cpu,site_name,site_name,site_name)
    return text


def application_environment (site_name,image_name,image_version,os_family,os_name,os_version,platform,occi_id,marketplaceid):
    ''' '''
    text = """dn: GLUE2ApplicationEnvironmentID=%s_%s,GLUE2ServiceID=cloud.compute.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
objectClass: GLUE2Entity
objectClass: GLUE2ApplicationEnvironment
GLUE2ApplicationEnvironmentAppName: %s
GLUE2ApplicationEnvironmentAppVersion: %s
GLUE2ApplicationEnvironmentRepository: %s
GLUE2ApplicationEnvironmentDescription: %s version %s on %s %s %s %s
GLUE2EntityName: %s
GLUE2ApplicationEnvironmentComputingManagerForeignKey: cloud.compute.%s_manager
creatorsName: o=glue
entryDN: GLUE2ApplicationEnvironmentID=%s,GLUE2ServiceID=cloud.compute.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
hasSubordinates: TRUE
modifiersName: o=glue
structuralObjectClass: GLUE2ApplicationEnvironment
subschemaSubentry: cn=Subschema
"""%(site_name,occi_id,site_name,site_name,image_name,image_version,marketplaceid,image_name,image_version,os_family,os_name,os_version,platform,occi_id,site_name,site_name,site_name,site_name)
    return text


def storage_service(site_name,production_level,service_type,capabilities):
    '''Return the GLUE2Service entity
    site_name: Unique name of the cloud-site
    capabilities: list of strings containing the various capabilities
    service_type: IaaS,PaaS,SaaS
    '''
    text = """dn: GLUE2ServiceID=cloud.storage.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
objectClass: GLUE2Entity
objectClass: GLUE2Service
objectClass: GLUE2StorageService
GLUE2ServiceAdminDomainForeignKey: %s
GLUE2ServiceID: cloud.storage.%s_service
GLUE2ServiceQualityLevel: %s
GLUE2ServiceType: %s
GLUE2ServiceCapability: %s
creatorsName: o=glue
entryDN: GLUE2ServiceID=cloud.storage.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
hasSubordinates: TRUE
modifiersName: o=glue
structuralObjectClass: GLUE2Service
subschemaSubentry: cn=Subschema
"""%(site_name,site_name,site_name,site_name, production_level, 'STaaS',capabilities,site_name,site_name)
    return text


def storage_manager(site_name,product_name,product_version,total_storage):
  ''' Not intensively used, so far, used only to attach execution environment.'''

  text = """dn: GLUE2ManagerID=cloud.storage.%s_manager,GLUE2ServiceID=cloud.storage.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
objectClass: GLUE2Entity
objectClass: GLUE2Manager
objectClass: GLUE2StorageManager
GLUE2ManagerID: cloud.storage.%s_manager
GLUE2ManagerProductName: %s
GLUE2ManagerServiceForeignKey: cloud.storage.%s_service
GLUE2StorageManagerStorageServiceForeignKey: cloud.storage.%s_service
GLUE2EntityName: Cloud Storage Manager at %s
GLUE2ManagerProductVersion: %s
creatorsName: o=glue
entryDN: GLUE2ManagerID=cloud.storage.%s_manager,GLUE2ServiceID=cloud.storage.%s_service,GLUE2GroupID=cloud,GLUE2DomainID=%s,o=glue
hasSubordinates: FALSE
modifiersName: o=glue
structuralObjectClass: GLUE2Manager
subschemaSubentry: cn=Subschema
"""%(site_name,site_name,site_name,site_name,product_name,site_name,site_name,site_name,product_version,site_name,site_name,site_name)
  return text


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
    def __init__(self, templates):
        self.ldif = {}
        for template in templates:
            with open('templates/%s.ldif' % template, 'r') as f:
                self.ldif[template] = f.read()


class CloudBDII(BaseBDII):
    def __init__(self, provider):
        self.provider_info = provider
        templates = ("headers", "domain", "bdii")
        super(CloudBDII, self).__init__(templates)

    def _format_headers(self):
        return self.ldif["headers"]

    def _format_bdii(self):
        return self.ldif["bdii"] % self.provider_info

    def _format_domain(self):
        return self.ldif["domain"] % self. provider_info

    def render(self):
        output = []
        output.append(self._format_headers())
        output.append(self._format_domain())
        output.append(self._format_bdii())
        return "\n".join(output)


def main():
    # NOTE(aloga): Refactored code >>>>
    bdii = CloudBDII(provider)
    print bdii.render()
    # NOTE(aloga): Refactored code <<<<

    if provider['iaas_endpoints']:
        print compute_service(provider['site_name'],provider['production_level'],'IaaS',provider['iaas_capabilities'])
        print compute_manager(provider['site_name'],provider['iaas_middleware'],provider['iaas_middleware_version'],provider['site_total_cpu_cores'],provider['site_total_ram_gb'],provider['iaas_hypervisor'],provider['iaas_hypervisor_version'])
        for endpoint in provider['iaas_endpoints']:
            print computing_endpoint(provider['site_name'],endpoint['endpoint_url'],endpoint['endpoint_interface'],provider['iaas_capabilities'],endpoint['service_type_name'],endpoint['service_type_version'],endpoint['service_type_developer'],endpoint['interface_version'],endpoint['endpoint_technology'],endpoint['auth_method'])
        for ex_env in provider['resource_tpl']:
            print execution_environment(provider['site_name'],ex_env['memory'],ex_env['occi_id'],ex_env['platform'],ex_env['cpu'],ex_env['network'])
        for app_env in provider['os_tpl']:
		print application_environment(provider['site_name'],app_env['image_name'],app_env['image_version'],app_env['os_family'],app_env['os_name'],app_env['os_version'],app_env['platform'],app_env['occi_id'],app_env['marketplace_id'])

    if provider['staas_endpoints']:
        print storage_service(provider['site_name'],provider['production_level'],'STaaS',provider['staas_capabilities'])
        print storage_manager(provider['site_name'],provider['staas_middleware'],provider['staas_middleware_version'],provider['site_total_storage_gb'])
        for endpoint in provider['staas_endpoints']:
            print storage_endpoint(provider['site_name'],endpoint['endpoint_url'],endpoint['endpoint_interface'],provider['staas_capabilities'],endpoint['service_type_name'],endpoint['service_type_version'],endpoint['service_type_developer'],endpoint['interface_version'],endpoint['endpoint_technology'],endpoint['auth_method'])
        print storage_capacity(provider['site_name'],provider['site_total_storage_gb'])

if __name__ == "__main__":
    main()
