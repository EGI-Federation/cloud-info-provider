# Cloud BDII provider

The Cloud BDII provider generates a GlueSchema v2 representation of cloud
resources for publihing it into a BDII

## Installation

### Binary packages

Packages are available at [EGI's AppDB](https://appdb.egi.eu/store/software/cloud.info.provider).
Use the appropriate repos for your distribution and install using the usual tools.

### From source

Get the source by cloning this repo and do a pip install:

```
git clone https://github.com/EGI-FCTF/BDIIscripts
cd BDIIscripts 
pip install .
```

If you plan to use the script in a bdii, the `bdii` package should be also installed
(it should be available in standard OS repositories).

## Generation of the LDIF 

The cloud-info-provider generates a LDIF according to the information in a
yaml file describing the static information of the cloud resources.
By default `/etc/cloud-info-provider/bdii.yaml` is used, but this path can be
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
```
cloud-info-provider-service --yaml-file /etc/cloud-info-provider/bdii.yaml \
    --middleware OpenStack --os-username <username> --os-password <password> \
    --os-tenant-name <tenant> --os-auth-url <auth-url>
```

**Test the generation of the LDIF before running the provider into your BDII!**

## Running the provider in a resource-BDII

This is the normal deployment mode for the cloud provider. It should be installed
in a node with access to your cloud infrastructure: for OpenStack, access to
nova service is needed; for OpenNebula-rOCCI provider, access to the files
describing the rOCCI templates is needed (e.g. installing the provider in the same
host as rOCCI-server).

### Create the provider script

In `/var/lib/bdii/gip/provider/` create a `cloud-info-provider` file that 
calls the provider with the correct options for your site:

```
#!/bin/sh

cloud-info-provider-service --yaml /etc/cloud-info-provider/openstack.yaml \
                            --middleware openstack \
                            --os-username <username> --os-password <passwd> \
                            --os-tenant-name <tenant> --os-auth-url <url>

```

Give execution permission:
```
chmod +x /var/lib/bdii/gip/provider/cloud-info-provider
```
and test it:
```
/var/lib/bdii/gip/provider/cloud-info-provider
```
It should output the full ldif describing your site.

### Start the bdii service

Once the provider script is working, start the bdii service:
```
service bdii start
```

The ldap server should contain all your cloud resource information:
```
ldapsearch -x -h localhost -p 2170 -b o=glue
```

## Adding the resource provider in a site-BDII

Sites should have a dedicated host for the site-BDII. Information on how to
set up this machine is avaiable in the EGI.eu wiki at
[How to publish site information](https://wiki.egi.eu/wiki/MAN01_How_to_publish_Site_Information). 

Add your cloud-info-provider to your site-BDII by adding a new URL like this:
```
ldap://<cloud-info-provier-hostname>:2170/GLUE2GroupID=cloud,o=glue
```

## Running the cloud-provider in a site-BDII

**This is not recommended for production!!**

If your site does not have a separated site-BDII and you want to use the cloud
provider in the site-BDII host (NOTE: any problems in the cloud provider
will affect your site-BDII!), you can add the `--site-in-suffix` to the provider
in `/var/lib/bdii/gip/provider/cloud-info-provider`.

## Generate complete BDII information

**This is not recommended for production! It does not generate GlueSchema 1.3
  information and will fail SAM tests**

The cloud provider can also generate the GlueSchema 2.0 info for a site by
using the `--full-bdii-ldif` option. This option will probably be removed in the
future!
