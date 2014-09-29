# Cloud BDII provider

The Cloud BDII provider generates a GlueSchema v2 representation of cloud resources for publihing it into
a BDII

## Installation

### Binary packages

Packages are available at [EGI's AppDB](http://appdb.egi.eu/xxxx). Use the appropriate repos for your distribution and install using the usual tools.

For RHEL/CentOS/ScientificLinux:

```
wget http://repository.egi.eu/community/software/cloud.info.provider/ccc > /etc/yum.repos.d/cloud-info-provider.repo
yum install cloud-info-provider
```

For Debian/Ubuntu:

```
wget http://repository.egi.eu/community/software/cloud.info.provider/ccc > /etc/.list
apt-get update
apt-get install cloud-info-provider
```

### From source

Get the source by cloning this repo and do a pip install:

```
git clone https://sddsfsdf/
cd cloud-info-provider
pip install .
```

## Generation of the LDIF 

The cloud-info-provider generates a LDIF according to the information in a
yaml file describing the static information of the cloud resources.
By default `etc/bdii.yaml` is used, but this path can be overriden with
the `--yaml-file` option. A complete example with comments is available 
in the `sample.static.yaml` file.

Dynamic information can be further obtained with the middleware providers
(OpenStack and OpenNebula via rOCCI supported currently). Use the
`--middleware` option for specifying the provider to use (see the command
help for exact names). cloud-info-provider will fallback to static information
defined in the yaml file if a dynamic provider is not able to return any
information. See the `sample.openstack.yaml` and `sample.opennebularocci.yaml`
for example configurations for each provider.

There are three different XYXXX in the yaml file considered by the provider:
`site`, `compute`, and `storage`:
 * `site` contains basic information of the site. It is only needed if the
    cloud-info-provider will be used to generate LDIF for a complete site-BDII
    information. This is 'not' the recommended deployment mode in a production
    infrastructure. 
   
 * `compute` should be present for those sites providing a IaaS computing
    service. It describes the available resources, service endpoints,
    the available VM images and the templates to run those images.
    Dynamic providers will fetch most of the information in this section.
    See the sample yaml files for details.

 * `storage` should be present for sites providing IaaS storage service.
    Similarly to the `compute`, it contains a description of the resources
    and enpoints providing the service. There are no dynamic providers for
    `storage`at the moment.

Each dynamic provider has its own commandline options for specifying how
to connect to the underlying service. Use the `--help` option for a complete
listing of options.

For example for OpenStack, use a command line similar to the following:
```
cloud-info-provider-service --yaml-file /etc/openstack.bdii.yaml
    --middleware OpenStack --os-username <username> --os-password <password> \
    --os-tenant-name <tenant> --os-auth-url <auth-url>
```

'Test the generation of the LDIF before running the provider into your BDII!'

### Running the provider in a resource-BDII

u
u ha

### Running the provider in a site-BDII

'This is not the recommended deployment mode in the production infrastructure'

If your site does not have a site-BDII and you want to generate both the
resource information and the site information with the cloud-bdii-provider....


## Development

### Build packages for RHEL/CentOs/ScientificLinux ###

Install RPM build tools

    yum install -y rpm-build
    
Create a non-root user for the build

    useradd rpmbuild

Setup the user build environment

    su - rpmbuild
    mkdir -p BUILD BUILDROOT LOGS RPMS SOURCES SPECS SRPMS tmp

Download sources from GitHub (for the latest release)

    wget https://github.com/EGI-FCTF/BDIIscripts/archive/0.3.zip -O SOURCES/BDIIscripts-0.3.zip
    
Extract the spec file

    unzip -p SOURCES/BDIIscripts-0.3.zip BDIIscripts-0.3/rpm/cloud-info-provider-service.spec > SPECS/cloud-info-provider-service.spec   
    
Compile rpm

    rpmbuild --define '_topdir /home/rpmbuild' --define '_tmpdir /home/rpmbuild/tmp' --define '_tmppath /home/rpmbuild/tmp' -bb SPECS/cloud-info-provider-service.spec

### Build packages for Debian/Ubuntu ###

For Debian/Ubuntu, you can just convert the RHEL rpm to debian using Alien

    alien cloud-info-provider-service-0.3-1.el6.noarch.rpm
