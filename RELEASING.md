# Instructions for creating a new release

Once a release and corresponding tag are created in GitHub, packages will be
built using Travis and attached to the tag.

## Preparing the release

Steps:

* Checking changes since latest tag (using browser or CLI)
* Agreeing release version
* Preparing changelog
  * Provide main changes, with related author(s)
    * Document changes impacting deployment/configuration/usage
* Updating AUTHORS as needed
* Updating zenodo.json as needed
  * Bump version, description and authors
* Merging a PR for updating build files to bump release version and changelog
* Creating a Tag in GitHub
  * Release title == Tag version, in a [semver](https://semver.org/) form like 0.42.0
  * Description is the changelog added to the build files

### Doing it from the Command Line Interface

```console
# Synchronize fork with upstream
git fetch upstream
git rebase upstream/master master
git checkout master
# Check latest tag
git tag --list
# Compare latest tag (0.8.3 here) with master
git compare EGI-FCTF 0.8.3..master
# Prepare a PR to prepare version (0.9.0 here)
git checkout -b prepare-0.9.0
# Update changelog in
# debian/changelog: add an entry at the top
# rpm/cloud-info-provider.spec: bump version at the top, add entry at the bottom
vim -o debian/changelog rpm/cloud-info-provider.spec
# Update AUTHORS file if needed
vim AUTHORS
# Update Zenodo configuration
vim .zenodo.json
# Commit changes
git commit -am 'Prepare release 0.9.0'
# Push new branch to fork
git push --set-upstream origin prepare-0.9.0
# Create pull request
git pull-request
```
