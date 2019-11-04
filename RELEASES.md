# DEEP releases in Cloud Information provider

The current document describe the main features implemented for the Cloud
Information Provider under the DEEP-Hybrid-Datacloud project.

Main documentation for the product is maintained [upstream](https://github.com/EGI-Foundation/cloud-info-provider), including usage and contribution (for developers) guidelines. The documentation for the features pending to be merged upstream and/or specific to DEEP-Hybrid-Datacloud will be added below, associated with the release version.

__Note that these features may not be available or merged upstream.__

## cloud-info-provider-deep-0.10.5

In a nutshell: 
 - Implements a new provider in order to fetch data from Mesos and Marathon frameworks.
 - Extracts GPU information from OpenStack and Mesos providers.
 - Publishes data in CMDBv1 format, support for multi-tenancy in OpenStack

### Mesos and Marathon providers

A new Mesos provider has been added to the list of supported ones (OpenStack, OpenNebula). This provider extracts data dynamically from Mesos and Marathon endpoints by calling the corresponding APIs. In particular, CIP uses the API endpoints:
 - `/metrics/snapshot` for Mesos, and
 - `/v2/info` and `/v2/leader` for Marathon.

The specific command-line (CLI) arguments for Mesos provider can be checked with the `--help` flag:
```
mesos provider options:
  --mesos-framework {mesos,marathon,chronos}
                        Select the type of framework to collect data from
                        (required). (default: None)
  --mesos-endpoint <api-url>
                        Specify Mesos|Marathon API endpoint. Defaults to
                        env[MESOS_ENDPOINT] (default: )
  --mesos-cacert <ca-certificate>
                        Specify a CA bundle file to verify HTTPS connections
                        to Mesos endpoints. (default: )
  --oidc-auth-bearer-token <bearer-token>
                        Specify OIDC bearer token to use when authenticating
                        with the API. Defaults to env[IAM_ACCESS_TOKEN]
                        (default: )
```

`--mesos-framework` and `--mesos-endpoint` are the only mandatory arguments. OIDC tokens can be provided through `--oidc-auth-bearer-token` to authenticate with protected APIs.

A sample `CIP` execution using Mesos provider:
```
cloud-info-provider-service \
    --middleware mesos \
    --format cmdb \
    --mesos-cacert /etc/ssl/certs \
    --mesos-framework mesos \
    --mesos-endpoint https://mesos.ifca.es/mesos \
    --oidc-auth-bearer-token $IAM_ACCESS_TOKEN \
    --yaml-file /cip/sites/mesos.IFCA-LCG2.yaml \
    --template-dir /cip/etc/templates/
```

#### Mesos static parameters

Required parameters that cannot be obtained dinamically through the data provided by the APIs are statically provided through the configuration file. This is the case for Chronos endpoints, whose API does not provide the relevant information (from CIP's standpoint) about the state of the service, so all the required information is static.

Apart from the GPU support (discussed in the following section), the following [static parameters](https://github.com/indigo-dc/cloud-info-provider-sites/blob/master/mesos.RECAS-BARI.yaml#L36) are now supported as part of the Mesos framework definition:

- `load_balancer_ips`: array of IPs for load balancing, e.g. `[193.146.75.183]`
- `local_volumes_host_base_path`: base path for the local volumes, e.g. `/tmp`
- `persistent_storage_drivers`: array with the list of supported persistent storage drivers, e.g.`[rexray]`

### GPU information

#### Mesos

For Mesos frameworks, CIP checks GPU support through the existing APIs. As mentioned above, additional information is provided through the static configuration. 

In the specific case of Chronos, GPU support can only be obtained through the static configuration. Thus, a `total_accelerators` value greater than 0 represents [GPU-enabled Chronos](https://github.com/indigo-dc/cloud-info-provider-sites/blob/master/mesos.RECAS-BARI.yaml#L42) endpoint.

#### OpenStack

In the case of OpenStack CMFs, CIP uses the nova API to gather dinamically all the information about flavors and images. The `properties` field is used to add this extra metadata about GPUs.

(e.g. flavor GPU metadata)
```
+----------------------------+-------------------------------------------------------------------------------------------------------------+
| Field                      | Value                                                                                                       |
+----------------------------+-------------------------------------------------------------------------------------------------------------+
| OS-FLV-DISABLED:disabled   | False                                                                                                       |
| OS-FLV-EXT-DATA:ephemeral  | 100                                                                                                         |
| disk                       | 30                                                                                                          |
| id                         | d5cdda3c-4885-4862-974e-4ca7f49429ae                                                                        |
| name                       | g5.large                                                                                                    |
| os-flavor-access:is_public | False                                                                                                       |
| properties                 | gpu:model='1080 Ti', gpu:number='1', gpu:vendor='NVIDIA Corporation', pci_passthrough:alias='NVIDIA1080TI:1'|
| ram                        | 11625                                                                                                       |
| rxtx_factor                | 1.0                                                                                                         |
| swap                       |                                                                                                             |
| vcpus                      | 1                                                                                                           |
+----------------------------+-------------------------------------------------------------------------------------------------------------+
```

The key used for each GPU property is not fixed, so in order to be able to match those, there have been defined the following set of CLI arguments:
```
--property-flavor-gpu-number <value>
--property-flavor-gpu-vendor <value>
--property-flavor-gpu-model <value>
--property-image-gpu-driver <value>
--property-image-gpu-cuda <value>
--property-image-gpu-cudnn <value>
```

##### Additional info for OpenStack images

As in the case of GPU data, CIP relies on the image properties to better describe the operating system it contains. For this, useful metadata are:
- `os_type`: operating system type, e.g. Linux
- `os_distro`: the operating system distribution, e.g. ubuntu
- `os_version`: the version of the operating system distribution, e.g. 16.04

So, in order for CIP to reflect this data in the output, all the OpenStack images have to have this metadata defined in the `properties` field.

### CMDBv1 format

This CIP release includes support for CMDBv1 format, which is rendered as a JSON array. The argument `--format cmdb` shall be used in order to format the output as CMDBv1-compliant.

Unlike BDII, CMDBv1 format lacked multi-tenancy, thus OpenStack images could not be published for different projects. This new release includes support for multi-tenancy through the inclusion of the `tenant` entity in the CMDBv1 schema. Tenants derive from the `service` entity and have `image` as the underlying entity. Additionally, `flavor` entity has been added to the current schema, which was missing from the latest implementation.

```
|- provider
   |- service
      |- tenant
         |- image
         |- flavor
```

Some additional fields have been added to the current version of CMDBv1:

#### iam_organisation

For the specific case of [PaaS Orchestrator](https://github.com/indigo-dc/orchestrator) needs, which relies on [INDIGO IAM](https://github.com/indigo-iam/iam) solution for authentication, a new `iam_organisation` field has been added to the tenant records. This allows the Orchestrator to get the list of images and flavors with the new multi-tenancy CMDBv1 schema. The value is provided in the [static configuration](https://github.com/indigo-dc/cloud-info-provider-sites/blob/master/os.IFCA-LCG2.yaml#L43), under the project definition.

#### service_parent_id

When getting information about Marathon or Chronos frameworks, it is interesting to know the Mesos service they are linked. The `service_parent_id` field, within the [endpoint defintion](https://github.com/indigo-dc/cloud-info-provider-sites/blob/master/mesos.IFCA-LCG2.yaml#L23), provides the Mesos parent URL endpoint.

#### is_public

As part of the site definition, the `is_public` field indicates whether the site provides public or private clouds. This information is useful for hybrid deployments of the PaaS Orchestrator.

## cloud-info-provider-deep-0.10.4

Adds support for publishing Infiniband information on OpenStack setups. The
implementation iterates over the `aggregate_instance_extra_specs` metadata
field in all the defined flavors, trying to match the _key_ and _value_
provided. These parameters are passed through the CLI options
`--extra-specs-infiniband-key` (defaults to _infiniband_) and
`--extra-specs-infiniband-value` (defaults to _true_),respectively.

Therefore, the following OpenStack's flavor configuration:

```
+----------------------------+----------------------------------------------------------------------------------------------------------------------------------+
| Field                      | Value                                                                                                                            |
+----------------------------+----------------------------------------------------------------------------------------------------------------------------------+
| OS-FLV-DISABLED:disabled   | False                                                                                                                            |
| OS-FLV-EXT-DATA:ephemeral  | 60                                                                                                                               |
| access_project_ids         | None                                                                                                                             |
| disk                       | 30                                                                                                                               |
| id                         | 81b73fef-a3dd-4bec-a136-98ebbac51c9c                                                                                             |
| name                       | cm5.xlarge                                                                                                                       |
| os-flavor-access:is_public | True                                                                                                                             |
| properties                 | aggregate_instance_extra_specs:flavor:cm5='true', aggregate_instance_extra_specs:type='infiniband', pci_passthrough:alias='IB:1' |
| ram                        | 3700                                                                                                                             |
| rxtx_factor                | 1.0                                                                                                                              |
| swap                       |                                                                                                                                  |
| vcpus                      | 4                                                                                                                                |
+----------------------------+----------------------------------------------------------------------------------------------------------------------------------+
```

will be matched if passing `--extra-specs-infiniband-key type
----extra-specs-infiniband-value infiniband`. In that case, the Cloud
Information Provider will publish the GLUE2 attribute
`GLUE2ExecutionEnvironmentNeworkInfo` for the given flavor:

```
dn: GLUE2ResourceID=http://schemas.openstack.org/template/resource#81b73fef-a3dd-4bec-a136-98ebbac51c9c_https://keystone.ifca.es:5000/v3,GLUE2ServiceID=https://keystone.ifca.es:5000/v3_cloud.compute,GLUE2GroupID=cloud,o=glue
objectClass: GLUE2Entity
objectClass: GLUE2Resource
objectClass: GLUE2ExecutionEnvironment
(..)
GLUE2ExecutionEnvironmentNetworkInfo: infiniband
```
