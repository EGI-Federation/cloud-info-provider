# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-09-05
### Removed
- Support for formatters other than JSON
- Support 

## [0.13.0] - 2023-10-05
### Added
- Add flavor name to templates (#231) (Enol Fernández)
- Support sites with URLs in the endpoints of GOCDB (#234) (Enol Fernández)
- Add new providers: AWS, Mesos and onedata (#237) (Pablo Orviz, Enol Fernández)
- Support regions in OpenStack (#229) (Enol Fernández)
- Add support for infiniband & GPUs in OpenStack (#237, #240) (Pablo Orviz, Enol Fernández)

### Fixed
- Update GitHub Actions syntax (#234) (Enol Fernández)
- Remove `/` from VO names (#230) (Enol Fernández)
- Use main as default branch (#236) (Enol Fernández)
- Improved CMDB templates (#237) (Pablo Orviz)

## [0.12.2] - 2021-05-17

- Support crendential refresh without client secret (#222) (Enol Fernández)
- Add --ignore-share-errors to continue publishing data even if there are
  issues in a given share (#217, #218, 221) (Enol Fernández)
- Add timeout option to core (#219) (Enol Fernández)
- Minor fixes related to templates (#212) (Enol Fernández)

## [0.12.1] - 2020-11-19
- Migrate from travis to GitHub Actions (#195, #198) (Enol Fernández)
- Reformatted code with black (#196) (Enol Fernández)
- Move templates inside the module (#194) (Enol Fernández)
- Publish project name and project domain name (#190) (Enol Fernández)
- Improve py3 compatibility (#189, #192) (Enol Fernández)
- Add EOSC-hub funding acknowledgement as requested by project (#188) (Enol Fernández)
- Update list of requirements for CentOS7 RPM building (#183) (Pablo Orviz)

## [0.12.0] - 2019-11-06

- Refactor SSL checks (#175). (Enol Fernández)
- Do not fail if JSON cannot be decoded (#176). (Enol Fernández)
- Code Clean-up (#177). (Enol Fernández)
- Import stdout (default one) and ams publishers (#178). (Enol Fernández)
- Multiple output plugin are now available (stdout for standard output and ams
  for Argo Messaging System). OpenNebula sites have to ensure that they
  publish both to BDII and AMS an update of the configuration and parameters
  is required (see README.md)
