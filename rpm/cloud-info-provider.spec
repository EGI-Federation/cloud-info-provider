#
# cloud-info-provider-service RPM
#

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Information provider for Cloud Compute and Cloud Storage services for BDII
Name: cloud-info-provider
Version: 0.6
Release: 1%{?dist}
Group: Applications/Internet
License: ASL 2.0
URL: https://github.com/EGI-FCTF/cloud-bdii-provider
Source: cloud_info_provider-%{version}.tar.gz

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: python-setuptools
BuildRequires: python-pbr
Requires: python
Requires: python-argparse
Requires: python-yaml
Requires: python-requests
Requires: python-mako
Requires: python-six
#Recommends: bdii
#Recommends: python-novaclient
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
%{python_sitelib}/cloud_info*
/usr/bin/cloud-info-provider-service
%config /etc/cloud-info-provider/

%changelog
* Mon Aug 03 2016 Baptiste Grenier <baptiste.grenier@egi.eu>
- Use Mako for templates.
- Rename python packages and packages.
* Mon Jul 18 2016 Alvaro Lopez Garcia <aloga@ifca.unican.es>
- Add Python 3 support (#27).
- Add support for new 'ooi' ID generation.
- Style improvements.
* Wed Feb 4 2015 Enol Fernandez <enol.fernandez@egi.eu> - 0.5-{%release}
- Fixed issue when storage is not defined (#13).
- Allow to define a image and resource template schema in OpenStack(#15).
- Add option to include the site name in the DN's suffix.
- Changed bdii dependency to Recommends.
- Added python-novaclient to Recommends.
* Wed Oct 01 2014 Enol Fernandez <enol.fernandez@egi.eu> - 0.4
- Incorporate changes from Alvaro Lopez.
- Enhance the published schema by adding a service name.
- Packaging improvements.
* Mon Aug 18 2014 Salvatore Pinto - 0.3
- Fixed OpenNebula provider (thanks to Boris Parak)
* Fri Jul 25 2014 Salvatore Pinto -0.2
- Added rpm packaging and bin wrapper
- Added possibility to setup options via YAML
- Added retrieval of Site name from BDII configuration
- Moved production_level to service and endpoint objects
- Changed basic tree for cloud services to GLUE2GroupID=cloud
- Added OpenNebula and OpenNebulaROCCI drivers
- Small changes to OpenStack driver (Marketplace information from glancepush, rewritten template, possibility to filter images without marketplace ID)
- Removed support for Tenant ID (instead of Tenant name) for retro-compatibility with older versions of novaclient libraries
* Wed May 28 2014 Alvaro Lopez Garcia - 0.1
- First release
