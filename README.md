# Cloud BDII provider

## Installation

### Binary packages ###

#### For RHEL/CentOS/ScientificLinux ####

    yum localinstall http://repository.egi.eu/community/software/cloud.info.provider/0.x/releases/sl/6/x86_64/RPMS/cloud-info-provider-service-0.3-1.el6.noarch.rpm
    
#### For Debian/Ubuntu ####

    apt-get -y install python-yaml
    wget http://repository.egi.eu/community/software/cloud.info.provider/0.x/releases/debian/dists/wheezy/main/binary-i386/cloud-info-provider-service_0.3-2_all.deb
    dpkg -i cloud-info-provider-service_0.3-2_all.deb

### From Source ###

    pip install -e .

## Usage

### Within a site BDII ###

If you are going to use this script with the EGI BDII information system, see the full
configuration instructions at https://wiki.egi.eu/wiki/Fedclouds_BDII_instructions

### Standalone usage ###

See the usage information with:

    cloud-info-provider-service --help

To produce a complete LDIF to be used without a site-BDII use:

    cloud-info-provider-service --full-bdii-ldif

The provider will use a YAML file to load static information. By default it will
look for `etc/bdii.yaml` but this path can be overwriten with:

    cloud-info-provider-service --yaml-file /path/to/yaml/file.yaml

To specify a middleware provider instead of the static provider use
the following (OpenStack, OpenNebula and OpenNebula via rOCCI are supported so far).

    cloud-info-provider-service --middleware OpenStack

The provider will use static information if no dynamic values are present or if a
dynamic provider is not able to return information.

### Using the static provider

The static provider will read values from a YAML file and will generate a LDIF
according to those values. See `etc/sample.static.yaml` for a commented sample.

### Using the a dynamic provider

The dynamic provider will get dynamic information from the cloud middleware.
Dynamic providers included within this release are:
 * openstack (for OpenStack Nova)
 * opennebula (for bare OpenNebula)
 * opennebularocci (for OpenNebula plus rOCCI server)

The quantity of dynamic information gathered depends on the provider itself. For
example, openstack provider retreives information about the endpoints, the flavours
and the images, while opennebula providers retreives only data about teh images

Thus, some static information is still needed, so you will have to create a YAML file.
A sample of a YAML file for each provider can be found in the `etc/` directory.

Once you've generated your YAML file you can run the provider with

    cloud-info-provider-service  --yaml-file etc/sample.openstack.yaml
    
You can also specify credentials and middleware parameters from the command line, eg.

    cloud-info-provider-service  --middleware OpenStack \
        --os-username <username> --os-password <password> \
        --os-tenant-name <tenant> --os-auth-url <auth-url>

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
