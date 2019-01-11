#
# cloud-info-provider-service RPM
#

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Information provider for Cloud Compute and Cloud Storage services for BDII
Name: cloud-info-provider
Version: 0.10.2
Release: 1%{?dist}
Group: Applications/Internet
License: ASL 2.0
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
* Wed Jan 09 2019 Enol Fernández <enol.fernandez@egi.eu> 0.10.3
- Updated dependencies
* Mon Oct 15 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.10.2
- Version bump (Baptiste Grenier)
* Mon Oct 01 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.10.0
- Integrate badges from shields.io and coveralls.io. (Alvaro Lopez)
- Improve and cleanup configuration files. (Enol Fernandez)
- Import a Jenkinsfile to handle SQA on Jenkins at IFCA. (Pablo Orviz)
- Fix utf-8 output for OpenNebula. (Ruben Diez)
- Introduce CMF-specific metapackages to deploy required dependencies. (Baptiste Grenier)
- Allow filtering private flavors. (Baptiste Grenier)
- Improve community health following discussions with Bruce Becker and al. (Baptiste Grenier)
- Use travis to lint, test, build and upload pacakges. (Baptiste Grenier)
- Integrate with zenodo. (Bruce Becker)
* Mon Apr 30 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.9.1
- OCCI is optional, do not fail if no OCCI endpoint is present (Enol Fernandez)
- Update organization name in documentation (Baptiste Grenier)
* Fri Mar 30 2018 Baptiste Grenier <baptiste.grenier@egi.eu> 0.9.0
- Use keystoneauth and v3 API, deprecate v2.0 API (Alvaro Lopez)
- Fix entry updates for ApplicationEnvironment (Boris Parak)
- Update package building and documentation (Baptiste Grenier)
* Tue Oct 03 2017 Baptiste Grenier <baptiste.grenier@egi.eu> 0.8.4
- Add support for rOCCI-server v2 (Boris Parak)
* Tue Jul 04 2017 Baptiste Grenier <baptiste.grenier@egi.eu> 0.8.3
- defusedxml is required only for OpenNebula provider (Baptiste Grenier)
* Tue Jul 04 2017 Baptiste Grenier <baptiste.grenier@egi.eu> 0.8.2
- Fix bandit usage to search for security issues when using tox (Baptiste Grenier)
- Optionally use the version entry from vmcatcher as image_version (OS provider) (Andre Gemuend)
- Use defusedxml to parse XML and fix bandit warnings (ON provider) (Baptiste Grenier)
- Fix deep hash lookup (ON provider) (Boris Parak)
- Misc documentation and packages building fixes (Baptiste Grenier)
* Wed Jun 07 2017 Baptiste Grenier <baptiste.grenier@egi.eu> 0.8.1
- Support for containerized Travis-CI
- Document RPM and Deb creation
- Fix deb creation on Xenial
* Mon May 29 2017 Baptiste Grenier <baptiste.grenier@egi.eu> 0.8.0
- Require a endpoint_url to be set for compute endpoints
- Updated OpenNebula provider
- Add disk size as OtherInfo of Resource templates
- Usage of a single template for storage info
* Sun Jan 01 2017 Alvaro Lopez Garcia <aloga@ifca.unican.es> 0.7.0
- Use templating engine.
- Bugfixes.
* Wed Aug 03 2016 Baptiste Grenier <baptiste.grenier@egi.eu>
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
