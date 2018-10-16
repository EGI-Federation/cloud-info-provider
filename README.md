# Cloud Information provider

[![BuildStatus](https://travis-ci.org/EGI-Foundation/cloud-info-provider.svg?branch=master)](https://travis-ci.org/EGI-Foundation/cloud-info-provider)
[![Coveralls](https://img.shields.io/coveralls/EGI-Foundation/cloud-info-provider.svg)](https://coveralls.io/github/EGI-Foundation/cloud-info-provider)
[![GitHub release](https://img.shields.io/github/release/EGI-Foundation/cloud-info-provider.svg)](https://github.com/EGI-Foundation/cloud-info-provider/releases)

The Cloud Information provider generates a representation of cloud resources,
that can be published inside a BDII (using the provided LDIF templates for a
GlueSchema v2 representation) or any other component like the INDIGO
Configuration Management Database (CMDB) (Using specific templates).

The generated representation is described using a
[Mako](http://www.makotemplates.org/) template having access to the cloud
middleware information.

Supported cloud middleware providers:

* OpenNebula
* OpenStack/ooi using Keystone authentication with API v3 *only*

## Installation

### Dependencies

The cloud-provider depends on PyYAML, which is already included as a dependency for
binary packages and when installing from source.

For running the cloud-provider in a production environment with a BDII you will
probably need:

* bdii (available in Ubuntu/Debian repos, for RH based distros it is in EPEL, for
  Debian wheezy it is available in the backports repo).
* if you are generating information for OpenStack, you will also need
  to install python-novaclient.

On RHEL you will also need to enable the
[EPEL repository](http://fedoraproject.org/wiki/EPEL) for python-defusedxml
that is required for the OpenNebula provider.

Providers-specific dependencies are managed using provider-specific metapackages.
Those metapackages are dependent on the main cloud-info-provider that is common
to all the providers and also includes the provider-specific dependencies.

RPMs:

* cloud-info-provider-openstack
* cloud-info-provider-opennebula
* cloud-info-provider

debs:

* python-cloud-info-provider-openstack
* python-cloud-info-provider-opennebula
* python-cloud-info-provider

#### OpenStack/ooi provider dependencies

* python-novaclient
* python-glanceclient
* python-keystoneauth1

#### OpenNebula provider dependencies

* python-defusedxml

### Binary packages

Latest packages are made available at [EGI's AppDB](https://appdb.egi.eu/store/software/cloud.info.provider).

Packages having gone through a the [EGI CMD](https://wiki.egi.eu/wiki/EGI_Cloud_Middleware_Distribution)
[Stagged Rollout and SQA process](https://wiki.egi.eu/wiki/EGI_Cloud_Middleware_Distribution_process)
are available in the [CMD repositories](http://repository.egi.eu/).

Use the appropriate repository for your distribution and install using the
OS-specific tools.

#### Building the packages using docker containers

[python-pbr](https://docs.openstack.org/developer/pbr/) is used for building
the python module and is available through the OpenStack repositories.

The version is set according to the repository information (tags, commits,...).

##### Building RPMs

* The OpenStack repositories are only used to get the `python-pbr` build
  dependency that is required to build the `cloud-info-provider` package.
* On CentOS 6 install `centos-release-openstack` instead of
  `centos-release-openstack-newton`.

```sh
# Checkout tag to be packaged
git clone https://github.com/EGI-Foundation/cloud-info-provider.git
cd cloud-info-provider
git checkout X.X.X
# Create a source tarball
python setup.py sdist
mkdir ~/rpmbuild
# Building in a container using the tarball
docker run --rm -v $(pwd):/source -v $HOME/rpmbuild:/root/rpmbuild -it centos:7
yum install -y rpm-build
# Required only for cloud-info-provider package to build python package
# Will configure repository containing python-pbr
yum install -y centos-release-openstack-newton
# Required only for cloud-info-provider package to build python package
yum install -y python-pbr python-setuptools
echo '%_topdir %(echo $HOME)/rpmbuild' > ~/.rpmmacros
mkdir -p ~/rpmbuild/{SOURCES,SPECS}
cp /source/dist/cloud_info_provider-*.tar.gz ~/rpmbuild/SOURCES/
cp /source/rpm/cloud-info-provider-*.spec ~/rpmbuild/SPECS/
rpmbuild -ba ~/rpmbuild/SPECS/cloud-info-provider.spec
rpmbuild -ba ~/rpmbuild/SPECS/cloud-info-provider-openstack.spec
rpmbuild -ba ~/rpmbuild/SPECS/cloud-info-provider-opennebula.spec
```

The RPM will be available into the `~/rpmbuild` directory.

##### Building a deb

```sh
# Checkout tag to be packaged
git clone https://github.com/EGI-Foundation/cloud-info-provider.git
cd cloud-info-provider
git checkout X.X.X
mkdir -p ~/debs/xenial
# Building in a container using the source files
docker run --rm -v $(pwd):/source -v $HOME/debs:/root/debs -it ubuntu:xenial
apt update
apt install -y devscripts debhelper git
# Required only for cloud-info-provider package to build python package
apt install -y python-all-dev python-pbr python-setuptools
cd /source && debuild --no-tgz-check clean binary
cd /source/debs/cloud-info-provider-openstack && debuild --no-tgz-check clean binary
cd /source/debs/cloud-info-provider-opennebula && debuild --no-tgz-check clean binary
cp ../*.deb ~/debs/xenial
```

The deb will be available into the `~/debs/xenial` directory.

### From source

Source-based installation is not recommended for production usage, but is very
handy for testing or development purpose.
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
git clone https://github.com/EGI-Foundation/cloud-info-provider
cd cloud-info-provider
pip install .
```

## Usage

### Generation of the LDIF

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
(OpenStack, ooi, and OpenNebula via rOCCI supported currently). Use the
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
    --middleware openstack --os-username <username> --os-password <password> \
    --os-user-domain-name default --os-project-name <tenant> \
    --os-project-domain-name default --os-auth-url <auth-url>
```

**Test the generation of the LDIF before running the provider into your BDII!**

### OpenStack provider

The OpenStack provider only publishes information about native OpenStack API access,
for ooi information check below

#### Filtering public or private flavors

By default the OpenStack provider will return 'all' flavors, but it is also
possible to select only 'public' or 'private' flavors using the
`--select-flavors` parameter set to `all`, `public` or `private`.
For more details see
[OpenStack flavors documentation](https://docs.openstack.org/nova/pike/admin/flavors.html).

### ooi provider

The ooi provider publishes information for those sites using ooi on top of OpenStack
nova to provide OCCI support. It has the same options as the openstack provider and yaml 
configuration file can be used without any changes.

### Running the provider in a resource-BDII

This is the normal deployment mode for the cloud provider. It should be installed
in a node with access to your cloud infrastructure: for OpenStack/ooi, access to
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
                            --os-username <username> --os-password <password> \
                            --os-user-domain-name default \
                            --os-project-name <tenant> \
                            --os-project-domain-name default \
                            --os-auth-url <auth-url>
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

#### Publishing both native OpenStack and ooi information

In your `/var/lib/bdii/gip/provider/cloud-info-provider` include calls to both OpenStack and ooi
providers:

```sh
#!/bin/sh

cloud-info-provider-service --yaml /etc/cloud-info-provider/openstack.yaml \
                            --middleware openstack \
                            --os-username <username> --os-password <password> \
                            --os-user-domain-name default --os-project-name <tenant> \
                            --os-project-domain-name default --os-auth-url <auth-url>
cloud-info-provider-service --yaml /etc/cloud-info-provider/openstack.yaml \
                            --middleware ooi \
                            --os-username <username> --os-password <password> \
                            --os-user-domain-name default --os-project-name <tenant> \
                            --os-project-domain-name default --os-auth-url <auth-url>
```

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

Add your cloud-info-provider to your site-BDII by adding a new URL that looks
like this:

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

Warning: **This does not generate GLUE1.3 information and will fail SAM tests**

The cloud provider can also generate the GlueSchema 2.0 info for a site by
using the `--full-bdii-ldif` option.
