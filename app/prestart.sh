#! /bin/bash

set -e

# The Docker container will look for this specially-named file and run it
# before starting the app.

CERT_URL=${CERT_URL:-""}
LDAP_CERT=${LDAP_CERT:=""}

if [ "$CERT_URL" != "" ] && [ "$LDAP_CERT" != "" ]; then
    curl -O "$CERT_URL" > "$LDAP_CERT"
    chmod ugo+r "$LDAP_CERT"
fi

if [ ! -e migrations/ ]; then
    flask db init
fi
flask db migrate || echo "migrate failed with exit code $?"
flask db upgrade

