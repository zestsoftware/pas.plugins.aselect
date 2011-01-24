#!/bin/bash

I18NDUDE="i18ndude"
DOMAIN="pas.plugins.aselect"

# Synchronise the .pot with the templates.
$I18NDUDE rebuild-pot --pot locales/${DOMAIN}.pot --create ${DOMAIN} .

# Synchronise the resulting .pot with the po .po files
for po in locales/*/LC_MESSAGES/${DOMAIN}.po; do
    $I18NDUDE sync --pot locales/${DOMAIN}.pot $po
done
