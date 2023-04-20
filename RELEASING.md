# Instructions for creating a new release

Once a release and corresponding tag have been created in GitHub, packages will
be built using Travis and attached to the tag.

## Preparing the release

Steps:

1. Open an issue to track the release process
1. Check changes since latest tag (using browser or CLI)
1. Agree release version
1. Prepare changelog
   - Provide main changes, with related author(s)
   - Document changes impacting deployment/configuration/usage
1. Update AUTHORS as needed
1. Merge a PR for updating CHANGELOG and any other needed
   changes for the release
   - Version should follow [SemVer](https://semver.org/) like 0.42.0
1. Push a `release` event to GitHub
   - Requires a valid personal token that can be obtained as described
     [here](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token)
1. Merge PR created by the event
1. Present release to [EGI UMD Release Team](https://wiki.egi.eu/wiki/URT)

### Doing it from the Command-Line Interface

```console
# Using GitHub CLI https://cli.github.com/
# And hub feature: https://hub.github.com/
# git must be an alias to hub

# Create a new issue
gh issue create -t "Release new package version"
# Synchronize fork with upstream
git fetch upstream
git rebase upstream/main main
git checkout main
# Check latest tag
git tag --list --sort version:refname
# Compare latest tag (0.8.3 here) with main
# Using GitHub
git compare EGI-Federation 0.8.3..main
# Using CLI
git log --abbrev-commit 0.8.3..main
# Prepare a PR to prepare version (0.9.0 here)
git checkout -b prepare-0.9.0
# Prepare the changelog and add it as a new entry to CHANGELOG
vim CHANGELOG
# Take care to changes in dependencies and configuration
# Depending on the changes update relevant packages
# Debian: dependencies in debian/control files
# Debian: debs/cloud-info-provider-opennebula/debian/changelog
# Debian: debs/cloud-info-provider-openstack/debian/changelog
# RHEL: change dependencies at the top
# RHEL: rpm/cloud-info-provider.spec
# RHEL: rpm/cloud-info-provider-opennebula.spec
# RHEL: rpm/cloud-info-provider-openstack.spec
# Update Zenodo configuration if needed
# Update AUTHORS file if needed
vim AUTHORS
# Commit changes
git commit -am 'Prepare release 0.9.0'
# Create pull request
gh pr create
# After PR merging
curl \
    -X POST \
    -H "Accept: application/vnd.github.v3+json" \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/EGI-Federation/cloud-info-provider/dispatches \
    -d '{"event_type":"release"}'
# Merge PR
gh pr merge --squash <pr number>
```

## Submitting the package to EGI Cloud Middleware Distribution (CMD)

To distribute the `cloud-info-provider` as part of
[Cloud Middleware Distribution (CMD)](https://wiki.egi.eu/wiki/EGI_Cloud_Middleware_Distribution),
it's required to follow the
[EGI Software provisioning process](https://wiki.egi.eu/wiki/EGI_Software_Provisioning).

- Submitting a [GGUS ticket](https://ggus.eu/?mode=ticket_submit) to the
  `EGI Software provisioning support` Support Unit
  - Ticket category: release
  - Type of issue: Middleware
  - Assign to support unit: `EGI Software Provisioning Support`
  - Version number
  - Link to release notes (GitHub release pages)
  - List of packages to release in CMD
