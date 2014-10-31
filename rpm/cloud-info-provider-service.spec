#
# cloud-info-provider-service RPM
#

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Information provider for Cloud Compute and Cloud Storage services for BDII.
Name: cloud-info-provider-service
Version: 0.5
Release: 1%{?dist}
Group: Applications/Internet
License: ASL 2.0
URL: https://github.com/EGI-FCTF/BDIIscripts
Source0: %{name}-%{version}.tar.gz

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: python-setuptools
BuildRequires: python-pbr
Requires: python
Requires: python-argparse
Requires: python-yaml
Requires: bdii
BuildArch: noarch

%description
Information provider for Cloud Compute and Cloud Storage services for BDII.
It supports static information specification, OpenNebula nad OpenStack cloud
middlewares.
The provider uses GLUE 2.0 EGI Cloud Profile to publish the information.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
python setup.py install --root $RPM_BUILD_ROOT  --install-data /

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{python_sitelib}/cloud_bdii*
/usr/bin/cloud-info-provider-service
/etc/cloud-info-provider/

%changelog
* Fri Oct 31 2014 Release 0.5 - Enol Fernandez <enol.fernandez@egi.eu>
- Fixed issue when storage is not defined (#13).
* Wed Oct 01 2014 Release 0.4 - Enol Fernandez <enol.fernandez@egi.eu>
- Incorporate changes from Alvaro Lopez.
- Enhance the published schema by adding a service name.
- Packaging improvements.
* Mon Aug 18 2014 Release 0.3 - Salvatore Pinto
- Fixed OpenNebula provider (thanks to Boris Parak)
* Tue Jul 25 2014 Release 0.2 - Salvatore Pinto
- Added rpm packaging and bin wrapper
- Added possibility to setup options via YAML
- Added retreival of Site name from BDII configuration
- Moved production_level to service and endpoint objects
- Changed basic tree for cloud services to GLUE2GroupID=cloud
- Added OpenNebula and OpenNebulaROCCI drivers
- Small changes to OpenStack driver (Marketplace information from glancepush, rewritten template, possibility to filter images without marketplace ID)
- Removed support for Tenant ID (insthead of Tenant name) for retro-compatibility with older versions of novaclient libraries
* Wed May 28 2014 Release 0.1 - Alvaro Lopez Garcia
- First release
