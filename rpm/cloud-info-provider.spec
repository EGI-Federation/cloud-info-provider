#
# cloud-info-provider-service RPM
#

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Information provider for Cloud Compute and Cloud Storage services for BDII
Name: cloud-info-provider-deep
Version: %{_pbr_version}
Release: 1%{?dist}
Group: Applications/Internet
License: Apache Software License 2.0
URL: https://github.com/EGI-Federation/cloud-info-provider
Source: cloud_info_provider-%{version}.tar.gz

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: python-setuptools
BuildRequires: python-pbr
Requires: python
Requires: python-argparse
Requires: python-yaml
Requires: python-mako
Requires: python-six
Requires: python-stevedore
# gocdb
Requires: python-requests
Requires: python-defusedxml
# ssl_utils
Requires: pyOpenSSL
#Recommends: bdii
Obsoletes: cloud-info-provider-service
BuildArch: noarch

%description
Information provider for Cloud Compute and Cloud Storage services.
It supports static information specification, OpenNebula and OpenStack cloud
middleware.
By default the provider uses GLUE 2.0 EGI Cloud Profile to publish the
information, but custom format can be created.

%prep
%setup -q -n cloud_info_provider-%{version}

%build

%install
rm -rf $RPM_BUILD_ROOT
python setup.py install --root $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{python_sitelib}/cloud_info_provider*
/usr/bin/cloud-info-provider-service
%config /etc/cloud-info-provider/

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
