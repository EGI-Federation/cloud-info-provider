#
# cloud-info-provider-openstack RPM
#

Summary: Cloud Information provider meta-package for OpenStack
Name: cloud-info-provider-deep-openstack
Version: %{_pbr_version}
Release: 1%{?dist}
Group: Applications/Internet
License: Apache Software License 2.0
URL: https://github.com/EGI-Foundation/cloud-info-provider

Requires: cloud-info-provider
# OpenStack-specific dependencies
Requires: python-novaclient
Requires: python-glanceclient
Requires: python-keystoneauth1
BuildArch: noarch

%description
OpenStack-specific meta-package for Information provider for Cloud Compute and
Cloud Storage services.
Install the cloud-information-provider and the Cloud Middleware dependencies.

%files

%changelog
* Fri Oct 25 2019 Pablo Orviz <orviz@ifca.unican.es> 0.10.5
- DPD-331 Fetch information from Mesos clusters
- DPD-333 Re-structure the code to allow choice of formatters
- DPD-382 Make the usage of project ID more clear in code and configuration files
- DPD-545 OpenStack flavor & image information in CMDBv1 format
- DPD-546 Multitenancy support in CMDBv1: images and flavors
- DPD-548 Support for Mesos provider
- DPD-561 Add CMDBv1 formatter
- DPD-564 Support for Marathon provider
- DPD-571 Validate produced CMDBv1 JSON
- DPD-573 CMDBv1 JSON should be produced as a list of objects
- DPD-612 Support Chronos data from static config
- DPD-613 Test publication in CMDB of CIP Mesos data
- DPD-669 Attribute to feature public and private providers (and services)
- DPD-670 Wrong string types in resultant CMDB JSON record
- DPD-673 Image record changes
- DPD-674 Restructure tenant records to rely on IAM organisation
- DPD-699 Generate service IDs in CMDB records as the service endpoint
* Mon Mar 25 2019 Pablo Orviz <orviz@ifca.unican.es> 0.10.4
- Adds support for publishing Infiniband information on OpenStack setups
