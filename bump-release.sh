#!/bin/sh

# Prepares new release

set -ue

new_release=$(grep "^## \[[0-9]" CHANGELOG | head -1 | sed -e "s/## \[\(.*\)\]/\1/")

## RPM specs
rpm_changes=$(mktemp)

echo "* $(date "+%a %b %d %Y") $(git config user.name) <$(git config user.email)> $new_release" > "$rpm_changes"
sed -e "/^## \[$new_release\]$/,/^##/!d;//d;/^$/d" CHANGELOG >> "$rpm_changes"

for spec in rpm/*.spec; do
    sed -i "" -e "/%changelog/r $rpm_changes" "$spec"
    sed -i "" -e "s/^\(Version.\).*/\\1 $new_release/" "$spec"
done

rm -f "$rpm_changes"

## Deb packages

for deb in debian/ debs/cloud-info-provider-opennebula/debian/ debs/cloud-info-provider-openstack/debian/ ; do
    deb_changes=$(mktemp)
    pkg=$(head -1 "$deb/changelog" | cut -f1 -d" ")
    {
        echo "$pkg ($new_release-1) xenial; urgency=medium"
        echo ""
        sed -e "/^## \[$new_release\]$/,/^##/!d;//d;/^$/d" CHANGELOG | \
            sed -e "s/^-/*/" | sed -e "s/^/ /"
        echo ""
        echo " -- $(git config user.name) <$(git config user.email)> $(date -R)"
        echo ""
    } >> "$deb_changes"
    cat "$deb_changes" "$deb/changelog" > "$deb/changelog.new"
    mv "$deb/changelog.new" "$deb/changelog"
    rm -f "$deb_changes"
done

## .zenodo.json
## Requires pandoc!
zenodo_changes=$(sed -e "/^## \[$new_release\]$/,/^##/!d;//d;/^$/d" CHANGELOG | \
                 pandoc --from gfm --to html | \
                 tr -s "\n" " ")

jq ".version = \"$new_release\" | \
    .title = \"EGI-Foundation/cloud-info-provider: $new_release\" | \
    .related_identifiers[0].identifier = \"https://github.com/EGI-Foundation/cloud-info-provider/tree/$new_release\" | \
    .publication_date = \"$(date '+%Y-%m-%d')\" | \
    .description = \"$zenodo_changes\"" < .zenodo.json > .zenodo.json.new
mv .zenodo.json.new .zenodo.json
