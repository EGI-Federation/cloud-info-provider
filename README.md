# Cloud Information provider

[![BuildStatus](https://travis-ci.org/EGI-Foundation/cloud-info-provider.svg?branch=master)](https://travis-ci.org/EGI-Foundation/cloud-info-provider)
[![Coveralls](https://img.shields.io/coveralls/EGI-Foundation/cloud-info-provider.svg)](https://coveralls.io/github/EGI-Foundation/cloud-info-provider)
[![GitHub release](https://img.shields.io/github/release/EGI-Foundation/cloud-info-provider.svg)](https://github.com/EGI-Foundation/cloud-info-provider/releases)

The Cloud Information provider generates a representation of cloud resources,
that can be published by different systems, like a BDII (using the provided LDIF
templates for GlueSchema representation) or any other component like the INDIGO
Configuration Management Database (CMDB) (Using specific JSON templates).

The provider extracts information from a cloud deployment using its public API
and formats it according to [Mako](http://www.makotemplates.org/) templates.

Currently supported cloud middleware:

- OpenNebula/rOCCI
- OpenStack
- OpenStack/ooi

## Acknowledgement

This work is co-funded by the [EOSC-hub project](http://eosc-hub.eu/)
(Horizon 2020) under Grant number 777536.
<img src="https://wiki.eosc-hub.eu/download/attachments/1867786/eu%20logo.jpeg?version=1&modificationDate=1459256840098&api=v2" height="24">
<img src="https://wiki.eosc-hub.eu/download/attachments/18973612/eosc-hub-web.png?version=1&modificationDate=1516099993132&api=v2" height="24">

## Installation

### From binaries

Packages are always attached to the
[releases page in GitHub](https://github.com/EGI-Foundation/cloud-info-provider/releases)
and after they are made available at
[EGI's AppDB](https://appdb.egi.eu/store/software/cloud.info.provider). AppDB
providers package repositores ready to be used with `yum` or `apt`.

Packages having gone through a the
[EGI CMD](https://wiki.egi.eu/wiki/EGI_Cloud_Middleware_Distribution)
[Stagged Rollout and SQA process](https://wiki.egi.eu/wiki/EGI_Cloud_Middleware_Distribution_process)
are available in the [CMD repositories](http://repository.egi.eu/).

Use the appropriate repository for your distribution and install using the
OS-specific tools.

Dependencies are maintained in the `requirements.txt` file. Binary packages
already include those dependencies (RH based distributions need to enable the
[EPEL repository](http://fedoraproject.org/wiki/EPEL)).

For running the provider in a production environment with a BDII you will also
need the `bdii` package (available in Ubuntu/Debian repos, in EPEL for RH based
distros it is in EPEL).

Providers-specific metapackages bring a convenient way to install the tool as
they depend on the main cloud-info-provider package (common to all providers)
and on any extra provider-specific dependencies.

#### Available packages

RPMs:

- cloud-info-provider-openstack
- cloud-info-provider-opennebula
- cloud-info-provider

debs:

- python-cloud-info-provider-openstack
- python-cloud-info-provider-opennebula
- python-cloud-info-provider

### From source

#### Using pip

Source-based installation is not recommended for production usage, but is very
handy for testing or development purpose. Get the source by cloning this repo
and do a pip install.

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

##### Provider dependencies

The OpenStack/ooi providers require the following extra libraries:

- python-keystoneclient
- python-novaclient
- python-glanceclient

These are not installed by default.

#### Building the packages using docker containers

[python-pbr](https://docs.openstack.org/developer/pbr/) is used for building the
python module and is available through the OpenStack repositories.

The version is set according to the repository information (tags, commits,...).

##### Building RPMs

- The OpenStack repositories are only used to get the `python-pbr` build
  dependency that is required to build the `cloud-info-provider` package.
- On CentOS 6 install `centos-release-openstack` instead of
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

## Usage

### Configuration

#### Static information

The cloud-info-provider uses a YAML file describing the static information of
the cloud resources to represent. Default location of this YAML file is
`/etc/cloud-info-provider/static.yaml` and can be overriden with the
`--yaml-file` option. [Sample configuration files](etc) are available at
`/etc/cloud-info-providder`. The file has two main maps:

- `site`: includes a single attribute `name` with the site name as available in
  GOCDB.

- `compute`: configures the VOs supported at a given cloud deployment and extra
  information not retrievable using the middleware APIs. Every supported VO must
  be described by a map under `shares`. Name of the share should match the name
  of the VO. Only mandatory configuration is the authorisation options for
  OpenStack/ooi (OpenNebula will consider the name of the VO as the name of the
  OpenNebula group). See below an example for ops VO. For other attributes of
  the `compute` map, check the sample configuration files that contain
  documentation on the available keys and values.

```yaml
compute:
  # Configure here the VOs supported at your site
  shares:
    # include one share for each supported VO
    # should match the name of the VO
    ops:
      # Authentication for the VO into OpenStack
      auth:
        # the project id in OpenStack
        project_id: xxxxx
      # Other optional information:
      # sla: https://egi.eu/sla/ops    # link to the SLA document
      # network_info: infiniband       # Type of network: infiniband, gigabiteethernet...
      # default membership is VO:<share name>, only specify if
      # using a more restrictive role/group for authorising users
      # membership:
      #    - VO:ops
```

#### Templates

By default the cloud-info-provider generates a LDIF (GLUE Schema) using the
templates located inside `/etc/cloud-info-provider/templates`. Additionally,
other supported formats include GLUE 2.1 Schema and CMDB. Use the `--format`
option of cloud-info-provider-service command (allowed values: `glue`, `glue21`,
`cmdb`) to use a different formatter. Likewise, the default location of the
templates can be changed using the `--template-dir` option.

#### Publishers

The cloud-info-provider has a pluggable system for producing its output. Two of
these `publishers` are provided in this repo: `stdout` and `ams`:

- `stdout`: just prints output to the standard output. This is the default
  publisher and the one to use when the cloud-info-provider is used in a BDII
  set up.

- `ams`: pushes a message to the Argo Messaging System with the parameters
  specified. It can either authenticate with a token (using `--ams-token`
  option, or with a certificate and key pair (using `--ams-cert` and `--ams-key`
  options). The topic to be used for publishing should be in the form:
  `SITE_<SITE_NAME>_ENDPOINT_<ENDPOINT_ID>`, where `<SITE_NAME>` is the site
  name in GOCDB and the `<ENDPOINT_ID>` is the id of the endpoint in GOCDB.

#### Providers

Dynamic information is obtained with the middleware providers (OpenStack, ooi,
and OpenNebula via rOCCI supported currently). Use the `--middleware` option for
specifying the provider to use (see the command help for exact names).
cloud-info-provider will fallback to static information defined in the YAML file
if a dynamic provider is not able to return any information.

Each dynamic provider has its own commandline options for specifying how to
connect to the underlying service. Use the `--help` option for a complete
listing of options.

##### OpenStack/ooi

The `openstack` and `ooi` providers require a working keystone endpoint and
valid credentials to access that endpoint. It uses
[keystoneauth](https://docs.openstack.org/keystoneauth/latest/) so any Keystone
authentication method available in that library can be used. The configured user
for authentication must be a member of every project configured in your shares.
Authentication options largely depend on the authentication method used, default
is username/password. For example, using OpenID Connect against a EGI Check-in
integrated endpoint:

```sh
cloud-info-provider-service --middleware openstack \
    --os-auth-type v3oidcaccesstoken \
    --os-identity-provider egi.eu --os-protocol oidc \
    --os-access-token $ACCESS_TOKEN \
    --os-auth-url https://<keystone-endpoint>:5000/v3
```

The `openstack` provider will only generate native OpenStack information, while
the `ooi` provider will only generate OCCI information and requires a correctly
configured [ooi](https://ooi.readthedocs.io/en/stable/) deployment.

Other extra options for the providers (defaults should be ok):

- `--select-flavors {all,public,private}` Select all (default), public or
  private flavors/templates. For more details see
  [OpenStack flavors documentation](https://docs.openstack.org/nova/pike/admin/flavors.html).

- `--all-images` If set, include information about all images (including
  snapshots), otherwise only publish images with cloudkeeper metadata, ignoring
  the others.

##### OpenNebula

The `opennebularocci` require a OpenNebula with rOCCI installation available.
The following options can be used to specify authentication against the
OpenNebula:

- `--on-auth <auth>` Specify authorization information. For core drivers, it
  should be `<username>:<password>`. Defaults to `env[ON_USERNAME]` or
  `oneadmin:opennebula`.

- `--on-rpcxml-endpoint <auth-url>` Specify OpenNebula XML RPC endpoint.
  Defaults to `env[ON_RPCXML_ENDPOINT]` or `http://localhost:2633/RPC2`.

Extra configuration can be provided with:

- `--rocci-template-dir <rocci-template-dir>` Location of the rOCCI-server
  resource template definitions. (default:
  `/etc/occi-server/backends/opennebula/fixtures/resource_tpl`)

- `--rocci-remote-templates` If set, resource template definitions will be
  retrieved via OCA, not from a local directory.

###### Upgrading to 0.11.x

Version 0.11.0 introduce a new configuration format for the cloud-info-provider,
now VOs need to be explicitly declared in your configuration in order to be
published, you will need a `shares` section on your `yaml` configuration like
this:

```yaml
compute:
  # any other existing compute sections should be kept as before
  # and add the shares with an entry per VO
  # there is no need to specify values for those entries as
  # defaults are safe for OpenNebula
  shares:
    ops:
    dteam:
    fedcloud.egi.eu:
    vo.access.egi.eu:
    # ...
```

###### Publishing to BDII and AMS

OpenNebula providers upgrading to 0.12.0 should publish information both to BDII
and AMS. For that you can take advantage of your existing provider at
`/var/lib/bdii/gip/provider/` that is called periodically and add an invocation
publishing to AMS as follows:

```shell
$ cat /var/lib/bdii/gip/provider/cloud-info-provider
#!/bin/bash

# your existing cloud-info-provider invocation
# do not change this one
cloud-info-provider-service  --yaml-file /etc/cloud-info-provider/bdii.yaml \
                             --on-auth <user>:<secret> \
                             --on-rpcxml-endpoint http://<your opennebula endpoint>:2633/RPC2 \
                             --rocci-remote-templates --middleware opennebularocci

# and add now the AMS publishing, same options but adding a few more
cloud-info-provider-service  --yaml-file /etc/cloud-info-provider/bdii.yaml \
                             --on-auth <user>:<secret> \
                             --on-rpcxml-endpoint http://<your opennebula endpoint>:2633/RPC2 \
                             --rocci-remote-templates --middleware opennebularocci \
                             --format glue21 --publisher ams \
                             --ams-topic SITE_<SITE-NAME>_ENDPOINT_<ENDPOINT ID>G0 \
                             --ams-cert /etc/grid-security/hostcert-bdii.pem \
                             --ams-key /etc/grid-security/hostkey-bdii.pem >> /var/log/cloud-info.log 2>&1
```

Publishing to AMS requires access to your OCCI endpoint certificate (permission
should be granted to user ldap). The certificate/key pair is used to
authenticate to AMS. The `SITE-NAME` is your site name in GOCDB, the
`<ENDPOINT_ID>` is the id at GOCDB of your OCCI endpoint, you can obtain that id
by checking the URL of your endpoint, e.g. for
`https://goc.egi.eu/portal/index.php?Page_Type=Service&id=9420`, the
`ENDPOINT_ID` is `9420`.

### Running the provider

The provider will represent the resources using the configured providers and
templates and dump it to standard output. Normally this is run within a
resource-level BDII so the information is published into the site BDII.

#### CAs

The provider will use your python default CAs for checking and connecting to
your endpoints and GOCDB, so please make sure those CAs include the IGTF CAs.
The location of the CAs depending on how you installed the different python
packages (using deb/rpm packages or `pip`).

For debian-based systems (e.g. ubuntu), use the following:

```sh
cd /usr/local/share/ca-certificates
for f in /etc/grid-security/certificates/*.pem ; do ln -s $f $(basename $f .pem).crt; done
update-ca-certificates
```

For RH-based systems (e.g. CentOS), you can include the IGTF CAs with:

```sh
cd /etc/pki/ca-trust/source/anchors
ln -s /etc/grid-security/certificates/*.pem .
update-ca-trust extract
```

Otherwise, you need to add the IGTF CAs to the internal requests bundle:

```sh
cat /etc/grid-security/certificates/*.pem >> $(python -m requests.certs)
```

#### Running the provider in a resource-BDII

This is the normal deployment mode for the cloud provider. It should be
installed in a node with access to your cloud infrastructure: for OpenStack/ooi,
access to nova/glance APIs is needed; for OpenNebula-rOCCI provider, access to
the files describing the rOCCI templates is needed (i.e. installing the provider
in the same host as rOCCI-server).

##### Create the provider script

In `/var/lib/bdii/gip/provider/` create a `cloud-info-provider` file that calls
the provider with the correct options for your site:

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

Give it execution permission:

```sh
chmod +x /var/lib/bdii/gip/provider/cloud-info-provider
```

and test it:

```sh
/var/lib/bdii/gip/provider/cloud-info-provider
```

It should output the full ldif describing your site.

**Test the generation of the LDIF before running the provider into your BDII!**

###### Publishing both native OpenStack and ooi information

In your `/var/lib/bdii/gip/provider/cloud-info-provider` include calls to both
OpenStack and ooi providers:

```sh
#!/bin/sh

cloud-info-provider-service --yaml /etc/cloud-info-provider/openstack.yaml \
                            --middleware openstack \
                            --os-username <username> --os-password <password> \
                            --os-user-domain-name default \
                            --os-project-name <tenant> \
                            --os-project-domain-name default --os-auth-url <auth-url>
cloud-info-provider-service --yaml /etc/cloud-info-provider/openstack.yaml \
                            --middleware ooi \
                            --os-username <username> --os-password <password> \
                            --os-user-domain-name default \
                            --os-project-name <tenant> \
                            --os-project-domain-name default --os-auth-url <auth-url>
```

##### Start the bdii service

Once the provider script is working, start the bdii service:

```sh
service bdii start
```

The ldap server should contain all your cloud resource information:

```sh
ldapsearch -x -h localhost -p 2170 -b o=glue
```

##### Adding the resource provider to the site-BDII

Sites should have a dedicated host for the site-BDII. Information on how to set
up this machine is avaiable in the EGI.eu wiki at
[How to publish site information](https://wiki.egi.eu/wiki/MAN01_How_to_publish_Site_Information).

Add your cloud-info-provider to your site-BDII by adding a new URL that looks
like this: `ldap://<cloud-info-provider-hostname>:2170/GLUE2GroupID=cloud,o=glue`

### GLUE 2.1 Schema

GLUE 2.1 Schema output can be generated by using `--format glue21`, e.g. using
OpenStack provider:

```sh
cloud-info-provider-service --format glue21 \
    --middleware openstack \
    --os-username <username> --os-password <password> \
    --os-user-domain-name default \
    --os-project-name <tenant> \
    --os-project-domain-name default --os-auth-url <auth-url>
```

This cannot be used with current BDII implementations as the schema is still not
supported by the infrastructure.

### CMDB Schema

[CMDB (CouchDB) Schema](https://github.com/indigo-dc/cmdb/tree/master/indigo-schema-couch)
is generated by using `--format cmdb`, e.g. using OpenStack provider:

```sh
cloud-info-provider-service --format cmdb \
    --middleware openstack \
    --os-username <username> --os-password <password> \
    --os-user-domain-name default \
    --os-project-name <tenant> \
    --os-project-domain-name default --os-auth-url <auth-url>
```

## Release management

Release management is documented in [RELEASING.md](RELEASING.md)
