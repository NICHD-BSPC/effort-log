#! /bin/bash

# The Docker container will look for this specially-named file and run it
# before starting the app.

if [ ! -e migrations/ ]; then
    flask db init
fi
flask db migrate || echo "migrate failed with exit code $?"
flask db upgrade
