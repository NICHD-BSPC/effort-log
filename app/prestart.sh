#! /bin/bash

# The Docker container will look for this specially-named file and run it
# before starting the app.
flask db migrate || echo "migrate failed with exit code $?"
flask db upgrade
