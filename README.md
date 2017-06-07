# Cloud Information provider

[![BuildStatus](https://travis-ci.org/EGI-FCTF/cloud-info-provider.svg?branch=master)](https://travis-ci.org/EGI-FCTF/cloud-info-provider)

The Cloud Information provider generates a representation of cloud resources,
that can be published inside a BDII (using the provided LDIF templates for a
GlueSchema v2 representation) or any other component like the INDIGO
Configuration Management Database (CMDB) (Using specific templates).

The generated representation is described using a
[Mako](http://www.makotemplates.org/) template having access to the cloud
middleware information.

## Installation

### Dependencies

The cloud-provider depends on PyYAML, which is already included as a dependency for 
binary packages and when installing from source.

For running the cloud-provider in a production environment with a BDII you will
probably need:
 - bdii (available in Ubuntu/Debian repos, for RH based distros it is in EPEL, for
 Debian wheezy it is available in the backports repo).
 - if you are generating information for OpenStack, you will also need
 to install python-novaclient.

On RHEL you will also need to enable the [EPEL repository](http://fedoraproject.org/wiki/EPEL) for python-defusedxml.

### Binary packages

Packages are available at [EGI's AppDB](https://appdb.egi.eu/store/software/cloud.info.provider).
Use the appropriate repository for your distribution and install using the usual tools.

#### Building the packages using docker containers

[python-pbr](https://docs.openstack.org/developer/pbr/) is used for building
the python module and is available through the OpenStack repositories.

The version is set according to the repository information (tags, commits,...).

##### Building a RPM

* The OpenStack repositories are only used to get the `python-pbr` build
  dependency.
* On CentOS 6 install `centos-release-openstack` instead of
  `centos-release-openstack-liberty`.


```sh
# Checkout tag to be packaged
git clone https://github.com/EGI-FCTF/cloud-info-provider.git
cd cloud-info-provider
git checkout X.X.X
# Create a source tarball
python setup.py sdist
# Building in a container using the tarball
docker run --rm -v $(pwd):/source -v $HOME/rpmbuild:/root/rpmbuild -it centos:7
yum install centos-release-openstack-liberty rpm-build
yum install python-pbr python-setuptools
echo '%_topdir %(echo $HOME)/rpmbuild' > ~/.rpmmacros
mkdir -p ~/rpmbuild/SOURCES
cp /source/dist/cloud_info_provider-*.tar.gz ~/rpmbuild/SOURCES/
cp /source/rpm/cloud-info-provider.spec ~/rpmbuild/SPECS/
rpmbuild -ba ~/rpmbuild/SPECS/cloud-info-provider.spec
```

The RPM will be available into the `~/rpmbuild` directory.

##### Building a deb

```sh
# Checkout tag to be packaged
git clone https://github.com/EGI-FCTF/cloud-info-provider.git
cd cloud-info-provider
git checkout X.X.X
# Building in a container using the source files
docker run --rm -v $(pwd):/source -v $HOME/debs:/root/debs -it ubuntu:xenial
apt update
apt install devscripts debhelper git python-all-dev python-pbr python-setuptools
cd /source
debuild --no-tgz-check clean binary
cp ../*.deb ~/debs
```

The deb will be available into the `~/debs` directory.

### From source

Get the source by cloning this repo and do a pip install.

As pip will have to copy files to /etc/cloud-info-provider directory, the
installation user should be able to write to it, so it is recommended to create
it before using pip.

```sh
sudo mkdir /etc/cloud-info-provider
sudo chgrp you_user /etc/cloud-info-provider
sudo chmod g+rwx /etc/cloud-info-provider
```

```sh
git clone https://github.com/EGI-FCTF/cloud-info-provider
cd cloud-info-provider
pip install .
```

## Generation of the LDIF 

By default the cloud-info-provider generates a LDIF according to the
information in a yaml file describing the static information of the cloud
resources.
It will uses template located inside `/etc/cloud-info-provider/templates` with
the LDIF extension. It is possible to specify another template extension using
the `--template-extension` parameter.
By default `/etc/cloud-info-provider/static.yaml` is used, but this path can be
overriden with the `--yaml-file` option. A complete example with comments is
available in the `sample.static.yaml` file.

Dynamic information can be further obtained with the middleware providers
(OpenStack and OpenNebula via rOCCI supported currently). Use the
`--middleware` option for specifying the provider to use (see the command
help for exact names). cloud-info-provider will fallback to static information
defined in the yaml file if a dynamic provider is not able to return any
information. See the `sample.openstack.yaml` and `sample.opennebularocci.yaml`
for example configurations for each provider.

There are three different maps in the yaml file considered by the provider:
`site`, `compute`, and `storage`:
 * `site` contains basic information of the site. The only attribute to define
    here is the `name` which must contain the site name as defined in GOCDB.
    Alternatively, the site name can be fetched from
    `/etc/glite-info-static/site/site.cfg` (or by the file set with the
    `--glite-site-info-static` option).
    Any other information is only relevant to generate a LDIF for a complete 
    site-BDII (*this is not the recommended deployment mode*).

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
```sh
cloud-info-provider-service --yaml-file /etc/cloud-info-provider/static.yaml \
    --middleware OpenStack --os-username <username> --os-password <password> \
    --os-tenant-name <tenant> --os-auth-url <auth-url>
```

**Test the generation of the LDIF before running the provider into your BDII!**

### Legacy OpenStack OCCI-OS interface

If you are using [OCCI-OS](https://github.com/EGI-FCTF/occi-os) for providing
OCCI support for OpenStack, use the `legacy-occi-os` command line option. This
will produce output with ids compatible with your setup instead of the current
default that supports [ooi](https://launchpad.net/ooi).

## Running the provider in a resource-BDII

This is the normal deployment mode for the cloud provider. It should be installed
in a node with access to your cloud infrastructure: for OpenStack, access to
nova service is needed; for OpenNebula-rOCCI provider, access to the files
describing the rOCCI templates is needed (e.g. installing the provider in the same
host as rOCCI-server).

### Create the provider script

In `/var/lib/bdii/gip/provider/` create a `cloud-info-provider` file that 
calls the provider with the correct options for your site:

```sh
#!/bin/sh

cloud-info-provider-service --yaml /etc/cloud-info-provider/openstack.yaml \
                            --middleware openstack \
                            --os-username <username> --os-password <passwd> \
                            --os-tenant-name <tenant> --os-auth-url <url>

```

Give execution permission:
```sh
chmod +x /var/lib/bdii/gip/provider/cloud-info-provider
```
and test it:
```sh
/var/lib/bdii/gip/provider/cloud-info-provider
```
It should output the full ldif describing your site.

### Start the bdii service

Once the provider script is working, start the bdii service:
```sh
service bdii start
```

The ldap server should contain all your cloud resource information:
```sh
ldapsearch -x -h localhost -p 2170 -b o=glue
```

### Adding the resource provider to the site-BDII

Sites should have a dedicated host for the site-BDII. Information on how to
set up this machine is avaiable in the EGI.eu wiki at
[How to publish site information](https://wiki.egi.eu/wiki/MAN01_How_to_publish_Site_Information). 

Add your cloud-info-provider to your site-BDII by adding a new URL that looks like this:
```
ldap://<cloud-info-provier-hostname>:2170/GLUE2GroupID=cloud,o=glue
```

## Other deployment modes

**These deployment modes cover special cases that should not be used in
  production!**

### Running the cloud-provider in a site-BDII

If your site does not have a separated site-BDII and you want to use the cloud
provider in the site-BDII host (NOTE: any problems in the cloud provider
will affect your site-BDII!), you can add the `--site-in-suffix` to the provider
in `/var/lib/bdii/gip/provider/cloud-info-provider`.

### Generate complete BDII information

**This does not generate GlueSchema 1.3 information and will fail SAM tests**

The cloud provider can also generate the GlueSchema 2.0 info for a site by
using the `--full-bdii-ldif` option.
