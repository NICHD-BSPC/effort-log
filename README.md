# Streamlined effort application

The goal of this application is to make it as easy as possible for each person
to enter their daily work on various projects, exposing data to downstream
tools. It was originally developed for the [Bioinformatics and Scientific
Programming Core](https://bioinformatics.nichd.nih.gov) but generalized for
wider use.

This app is intended to be lightweight, and only aids in the recording of
effort. It assumes that users/projects/groups are changed infrequently, so they
are specified in YAML files. These files can be updated manually, or the files
can be tied in to other automation (e.g., using GitHub/GitLab APIs).

It is implemented as a Flask app served by nginx in a Docker container, saving
to a sqlite3 database on the host. Sqlite3 does not support concurrent writes,
so only one person can save to the database at a time. Thus, another assumption
is that usage is relatively low.

The only requirement is Docker Compose.

**Quickstart**

1. [Install Docker Compose](https://docs.docker.com/compose/install/).

2. In the top level of the repo, run:

```bash
# Note the "()" to run in a subshell
(
  source app/.env;
  touch $HOST_DATABASE;
  docker compose --env-file app/.env up --build -d
)
```
to run the app in the background. This command sources the env file in
a subshell (so as not to contaminate the main shell), touches the database in
case it does not already exist, builds the docker container if needed,  mounts
the database and the application directory in the running container, and starts
the app.

3. Visit https://localhost:3536 to see the app (or `IP:3536` to view it from another
  machine on the network).

4. To stop, run `docker compose --env-file app/.env down`.

When running, the app will be available on `localhost:3536`. Use the "Add
entry" button to add new entries; the home page will plot entries. Colors and
filtering are configurable by dropdown and radio buttons (e.g., color by person
to see who hasn't recorded any entries recently).

Get a CSV of the database by visiting `localhost:3536/csv`. You can use this
for all sorts of downstream aggregation and reporting.

The app's database will be found in the current directory, `app.db`, and will
be persistent across containers. Configure this location in `app/.env` using
the variable `HOST_DATABASE`.

## Configuration

- **See `app/.env` for the configuration**. This file is sourced by docker
  compose as well as in the app config (in `app/config.py`).
- If you want to use LDAP (and know the relevant settings), you can set
  `DISABLE_LDAP=0` and fill in the LDAP-related env vars (note: while this
  works locally, the current tests do not test LDAP functionality)
- `app/personnel.yaml` is a YAML file containing a simple list of users. It can
  be manually updated or plugged in to automation. This file can be modified on
  the host, and the running app will pick up the changes upon the next refesh
  of the entry form.
- `app/projects.yaml` is a YAML file representing a dictionary, where keys are
  top-level grouping (e.g., PIs or labs in the context of a bioinformatics
  core), and values are lists of projects under that grouping. It can be
  manually edited or plugged in to automation. Like the personnel file, it can
  be modified on the host and the running app will pick up the changes upon the
  next refresh of the entry form.

## Administration

- The file `compose.yml` contains the baseline docker config and is used by
  default
- The file `docker-compose.override.yml` is also used by default and fills in
  production values
- The file `compose-test.yml` is only used for testing (see testing section
  below). To avoid modifying any existing database, you should set the
  `$HOST_DATABASE` env var on the host -- see the testing section below.
- Run `docker logs effort-app -f` for logs
- Run `docker exec -it effort-app /bin/bash` to interactively inspect the
  running container

## Testing

GitHub Actions are configured in `.github/workflows/main.yml` to use Selenium
for testing. The file `compose-test.yml` overrides default settings in
`compose.yml`, which also starts a Selenium container on the same network and
uses a different database name. The tests are in `test/test.py`. They also
generate screenshots that are stored as GH Actions artifacts.

Running the tests requires the `selenium` Python package (can be `pip` or
`conda`-installed).

```bash
(
  source app/.env
  source app/.test_env
  docker compose --env-file app/.env -f compose.yml -f compose-test.yml up -d
)
```

Then run the tests:

```bash
python test/test.py
```

Watch what is happening with the tests by visiting this URL:
http://localhost:7900/?autoconnect=1&resize=scale&password=secret.

## Notes on architecture

The code is heavily inspired by the *excellent* [Flask Mega-Tutorial
series](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world).
Here's a brief guide to the moving parts.

### Config notes

- `app/config.py` reads in the YAML files below and sets up the location of the
  database. It uses the `dotenv` package to source `app/.env` variables into the
  environment.

- `app/personnel.yaml` is a simple list of people. It is used to populate
  dropdowns in the app.

- `app/projects.yaml` lists the labs and projects in each lab. It is used to
  populate other dropdowns.

- `app/migrations` contains the code for migrating database schemas between
  versions. This is generated by `flask db migrate` and the resulting code is
  applies with `flask db upgrade`. It should not be edited manually. These
  commands are run each time the docker container is started by
  `app/prestart.sh`.


### Code notes

- `app/app/main.py` is imported and called from `uwsgi.ini` (module is
  `app.main`; callable is `app`).

- `app/app/__init__.py` sets up the db and defines the `create_app()` function.
  **Note that the imports and order of everything in here is carefully
  crafted,** as outlined in the tutorial referenced above.

- `app/app/routes.py` is the "traditional" Flask routes module, which
  determines which functions run when which URLs are visted.

- `app/app/forms.py` defines the main `EffortForm`, the login form, and some
  validators.

- `app/app/models.py` defines the main `Entry` object which is stored in the db

### Templates, CSS, JavaScript notes

Templates use the Flask-Bootstrap template. Note that the Flask-Bootstrap
package currently uses a slightly out-of-date version of the Bootstrap
framework.

- `app/app/templates/base.html`: this template defines the base page that other
  templates inherit from. JQuery and DataTables are imported here (used for
  displaying the entries)

- `app/app/templates/entry.html`: this template defines the page with the form
  used for entries. This one gets a little complicated in that there is
  JavaScript to auto-populate the dropdowns of the form. This is so that the
  "projects" dropdown only shows the projects for the selected lab, to simplify
  the entry process. It also does some fancy things with checking the total
  time entered for the day.

- `app/app/templates/help.html` is the static help page, manually edited.

- `app/app/templates/changelog.html` is the static changelog, manually edited

- `app/app/templates/index.html` is the main page that renders the DataTable
  from the db.

### Docker-specific notes

The Docker container builds from the
[`uwsgi-nginx-flask`](https://github.com/tiangolo/uwsgi-nginx-flask-docker)
Docker container which has some nice docs.

The build process copies the entire app directory into the container.

- `Dockerfile` is used to define the Docker container

- `compose.yml` has baseline config which is by default extended by
  `docker-compose.override.yml`. It can instead be overridden with
  `compose-test.yml` by specifying in the command. See testing section above.

- `app/uwsgi.ini` configures the uWSGI instance running in the Docker
  container. **Its location and filename are expected by the Dockerfile.**

- `app/prestart.sh` is used by the uwsgi-nginx-flask Docker container's startup
  script. If this specially-named file is in the app directory, it will be run
  before starting the app.
