#!/bin/bash

set -eo pipefail

function mvExampleFiles {
    echo "Moving example config files into usable places..."

    cp -r --update=none example_config/* config/

    echo "Moved!"
}

function uvSync {
    echo "Installing dependencies..."

    uv sync --all-groups --all-extras

    echo "Installed dependencies."
}

function configureArtemis {
    echo "Configuring ARTEMiS with default values..."

    yq --yaml-roundtrip --in-place '.server.listen_address = "0.0.0.0"' config/core.yaml
    yq --yaml-roundtrip --in-place '.server.port = 8080' config/core.yaml
    yq --yaml-roundtrip --in-place '.database.host = "mysql"' config/core.yaml
    yq --yaml-roundtrip --in-place '.database.memcached_host = "memcached"' config/core.yaml
    yq --yaml-roundtrip --in-place ".aimedb.id_secret = \"$(openssl rand --base64 64 | tr -d "\n")\"" config/core.yaml
    yq --yaml-roundtrip --in-place ".frontend.secret = \"$(openssl rand --base64 64 | tr -d "\n")\"" config/core.yaml
}

function createDatabaseTables {
    echo "Creating database tables..."

    .venv/bin/python3 dbutils.py create

    echo "Created database tables."
}

mvExampleFiles
uvSync

if [ -e BOOTSTRAP_OK ]; then
	echo "Already bootstrapped."
	exit 0
fi

configureArtemis
createDatabaseTables

echo "Bootstrap complete."

cat << EOF > BOOTSTRAP_OK
ARTEMiS was bootstrapped here on $(date).

The existence of this file stops ARTEMiS from bootstrapping again.
There's nothing harmful about this -- you can bootstrap as much as you want!
We just don't want to necessarily bootstrap *each* time we boot ARTEMiS.

To bootstrap again (in case you think something has gone wrong)
Delete this file and re-run ./dev/bootstrap.sh
EOF
