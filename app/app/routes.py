import sqlite3
import ssl
from io import StringIO
import json
from urllib.parse import urlparse, urljoin
import datetime

import flask
from flask import current_app as app
from flask import render_template, url_for, flash, redirect, make_response, request

from sqlalchemy import func
import ldap3
import pandas
import yaml
import plotly
import plotly.express as px
import plotly.graph_objs as go

from app import db
from app.forms import EffortForm
from app.models import Entry

import logging

logging.basicConfig(level=logging.INFO)

# If LDAP is disabled, then create dummy decorators
if app.config["DISABLE_LDAP"]:

    def dummy(func):
        return func

    class Dummy(object):
        pass

    login_manager = Dummy()
    ldap_manager = Dummy()
    flask_login = Dummy()

    login_manager.user_loader = dummy
    ldap_manager.save_user = dummy
    flask_login.login_required = dummy

else:
    import flask_ldap3_login
    import flask_login
    from flask_ldap3_login import forms as flask_ldap3_login_forms
    from flask_login import current_user

    # The login_manager handles Flask login operations, and the ldap_manager
    # handles communication and authentication with the LDAP server.
    login_manager = flask_login.LoginManager(app)
    ldap_manager = flask_ldap3_login.LDAP3LoginManager(app)

    # Setting this attribute tells Flask-Login what route to use when redirecting
    # a user to log in.
    login_manager.login_view = "login"
    login_manager.login_message = "Please log in to see this page."

    # Sets up a TLS context with cert, which we need for connecting to the LDAP
    # server.
    tls_ctx = ldap3.Tls(
        ca_certs_file=app.config["LDAP_CERT"],
        validate=ssl.CERT_REQUIRED,
    )

    # The configuration specifies LDAP_ADD_SERVER = False to allow us to add it
    # manually here with TLS cert.
    ldap_manager.add_server(
        app.config.get("LDAP_HOST"),
        app.config.get("LDAP_PORT"),
        app.config.get("LDAP_USE_SSL"),
        tls_ctx=tls_ctx,
    )

    # Stores current users
    users = {}

    class User(flask_login.UserMixin):
        """
        Standard Flask user object, mostly just a container. See
        https://flask-login.readthedocs.io/en/latest/#your-user-class for what is
        required on this class, and what is inherited from UserMixin
        """

        def __init__(self, dn, username, data):
            self.dn = dn
            self.username = username
            self.data = data
            self.name = username

        def __repr__(self):
            return self.dn

        def get_id(self):
            # Note: Flask-Login requires this to be a string.
            return self.dn

    # Flask-Login manager requires a callback that takes the string ID of a user
    # and returns the corresponding User object (here, they are stored in the
    # global dict keyed by LDAP DN)
    @login_manager.user_loader
    def load_user(id):
        if id in users:
            return users[id]
        return None

    # This is the means by which we communicate between LDAP authentication (via
    # the LDAP3LoginManager) and Flask-Login's LoginManager
    @ldap_manager.save_user
    def save_user(dn, username, data, memberships):
        user = User(dn, username, data)
        users[dn] = user
        return user


def _get_projects():
    """
    Dynamically load projects
    """
    projects = yaml.load(open(app.config["PROJECTS_PATH"]), Loader=yaml.FullLoader)
    return projects


def _get_personnel():
    """
    Dynamically load personnel
    """
    personnel = yaml.load(open(app.config["PERSONNEL_PATH"]), Loader=yaml.FullLoader)
    return personnel


@app.route("/login", methods=["GET", "POST"])
def login():
    # This does the work to set up the form's validation to contack the LDAP
    # server
    form = flask_ldap3_login_forms.LDAPLoginForm()

    if form.validate_on_submit():
        # If the LDAP form validated, we can tell the Flask-Login manager that
        # the user is logged in.
        flask_login.login_user(form.user)
        flask.flash("Logged in successfully")

        # This is to prevent attackers from redirecting to another site, see
        # https://flask-login.readthedocs.io/en/latest/#login-example
        target = flask.request.args.get("next")
        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        if not (
            test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc
        ):
            return flask.abort(400)

        return flask.redirect(flask.url_for("index"))
    return flask.render_template("login.html", form=form)


@app.route("/")
@app.route("/index")
@flask_login.login_required
def index():
    # Identify the set of personnel to include in the selection dropdown,
    # populated from what's actually in the db (rather than the YAML)
    entries = Entry.query.all()
    personnel_list = ["all"] + list(set([e.personnel for e in entries]))
    bar = plot_over_time()
    return render_template(
        "index.html", entries=entries, plot=bar, personnel_list=personnel_list
    )


@app.route("/delete/<id>")
@flask_login.login_required
def delete(id):
    entry = Entry.query.get(id)
    flash(f"Deleted {entry}", "danger")
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for("index"))


def entry_page(entry=None):
    """
    This function factors out the form stuff needed for both new entry as well
    as edit entry pages.

    If `entry` is not None, it is expected to be an Entry object which will be
    updated (and committed to the db) based on the updated form contents.
    """
    if entry:
        form = EffortForm(obj=entry)
    else:
        form = EffortForm()

    configured_projects = _get_projects()
    configured_personnel = _get_personnel()

    # Note that the form validation will reject the "---"; it's used here as
    # a placeholder to remind the user that they need to select a PI first.
    #
    # Here we manually append the "other" option. It's not included in the YAML
    # config because doing so would make it harder to automatically update that
    # file
    form.pi.choices = ["---"] + sorted(configured_projects.keys()) + ["other"]

    # Add the "personnel" (=people)
    form.personnel.choices = configured_personnel

    # The WTForms validation will be checking for the following projects as
    # valid options, but the javascript in the template will be modifying the
    # entries based on the selected PI.
    #
    # We also include "other" at the end, similar to PIs above.
    projects = []
    for i in configured_projects.values():
        projects.extend(i)
    projects = sorted(projects) + ["other"]

    form.project.choices = projects

    if form.validate_on_submit():

        if entry:  # we're in edit mode
            # This automatically updates the existing Entry object with the
            # form's contents
            form.populate_obj(entry)

        else:  # we're in new entry mode so need to create a new one
            entry = Entry(
                pi=form.pi.data,
                project=form.project.data,
                date=form.date.data,
                personnel=form.personnel.data,
                notes=form.notes.data,
                fraction=form.fraction.data,
            )

        db.session.add(entry)
        db.session.commit()
        if entry:
            flash(f"updated {entry}")
        else:
            flash(f"entered {entry}")

        return redirect(url_for("index"))

    return render_template("entry.html", form=form, entry=entry)


@app.route("/entry", methods=["GET", "POST"])
@flask_login.login_required
def entry():
    """
    View with form for ADDING a new entry. Since much code is shared with
    editing, it is factored out into a separate function.
    """
    return entry_page()


@app.route("/edit/<id>", methods=["GET", "POST"])
@flask_login.login_required
def edit(id):
    """
    View with form for EDITING an existing entry. Since much code is shared
    with adding a new entry, it is factored out into a separate function.
    """
    entry = Entry.query.get(id)

    # Supplying `entry` here is what triggers the form-editing behavior for
    # entry_page()
    return entry_page(entry)


@app.route("/getprojects/<pi>")
@flask_login.login_required
def getprojects(pi):
    """
    Given a PI, returns a JSON list of configured projects.
    """
    return json.dumps(sorted(_get_projects()[pi]) + ["other"])


@app.route("/csv")
def tsv():
    """
    Exports a CSV of all entries.
    """
    results = []
    for entry in Entry.query.all():
        results.append(entry.to_dict())
    df = pandas.DataFrame(results)
    si = StringIO()
    df.to_csv(si, index=False)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-Type"] = "text/csv"
    return output


@app.route("/help")
@flask_login.login_required
def help():
    return render_template("help.html")


@app.route("/changelog")
@flask_login.login_required
def changelog():
    return render_template("changelog.html")


@flask_login.login_required
@app.route("/bar", methods=["GET", "POST"])
def bar():
    """
    The AJAX in index.html uses this as a mechanism for updating the JSON for
    the plot upon choosing a new person from the dropdown. It will send the
    updated JSON to the relevant JavaScript function.

    So this function behaves like a REST API that is specific to the AJAX.
    """
    feature = request.args["selected"]
    exclude_weekends = request.args["exclude_weekends"]
    color_by = request.args["color_by"]
    graphJSON = plot_over_time(
        feature, exclude_weekends=exclude_weekends, color_by=color_by
    )
    return graphJSON


def plot_over_time(personnel="all", exclude_weekends="yes", color_by="pi"):
    """
    Build a plotly plot showing the effort so far for the specified personnel.

    Parameters
    ----------

    personnel : str
        If "all", then show all personnel; otherwise filter the data to only
        show data for this person.

    exclude_weekends : str
        If "yes" then don't show data for weekends. Note this is not boolean
        because we're getting this right from the form (whose values are
        strings)

    color_by : str
        Color by a field available in Entry objects
    """

    # This is used to set the xmin/xmax for the zoomed-in plot; there will be
    # a date range slider underneath for more fine-grained control.
    today = datetime.date.today()
    last_week = today - datetime.timedelta(days=10)

    # Select entries to plot from the database using the ORM
    if personnel == "all":
        entries = Entry.query.all()
    else:
        entries = Entry.query.filter(Entry.personnel == personnel)

    # Build up  a dataframe provide to plotly.express
    ds = []
    for entry in entries:
        ds.append(
            {
                "date": entry.date,
                "personnel": entry.personnel,
                "pi": entry.pi,
                "project": entry.project,
                "fraction": entry.fraction,
                "notes": entry.notes,
            }
        )
    df = pandas.DataFrame(ds)

    title = "Effort for " + personnel

    if len(df) == 0:
        return {}

    fig = px.bar(
        df,
        x="date",
        y="fraction",
        color=color_by,
        hover_data=["project", "notes", "personnel"],
        range_x=[last_week, today],
        title=title,
    )

    fig.update_xaxes(rangeslider_visible=True)

    if exclude_weekends == "yes":
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]),
            ],
        )

    return fig.to_json()
