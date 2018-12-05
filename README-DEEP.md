# DEEP releases in Cloud Information provider

[![Build Status](https://jenkins.indigo-datacloud.eu:8080/buildStatus/icon?job=Pipeline-as-code/cloud-info-provider-deep/DEEP)](https://jenkins.indigo-datacloud.eu:8080/job/Pipeline-as-code/job/cloud-info-provider-deep/job/DEEP/)

The current document describe the main features implemented for the Cloud
Information Provider under the DEEP-Hybrid-Datacloud project.

Main documentation for the product is maintained [upstream](https://github.com/EGI-Foundation/cloud-info-provider), including usage and contribution (for developers) guidelines. The documentation for the features pending to be merged upstream and/or specific to DEEP-Hybrid-Datacloud will be added below, associated with the release version.

__Note that these features may not be available or merged upstream.__

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
