import os
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, InputRequired, ValidationError
from wtforms.fields import DateField, DecimalRangeField, DecimalField
from .models import Entry
from flask_login import current_user

USE_LOGIN = not bool(int(os.environ.get("DISABLE_LDAP")))

if USE_LOGIN:

    def IsLoggedInUser(form, field):
        admin_users = os.environ.get("ADMIN_USERS", "").split(",")
        if (
            form.personnel.data != current_user.username
            and current_user.username not in admin_users
        ):
            raise ValidationError(
                f"""
                You are creating an entry for {form.personnel.data}...but you are
                logged in as {current_user.username}!
                """
            )

else:

    def IsLoggedInUser(*args, **kwargs):
        pass


def not_dashes(form, field):
    if field.data == "---":
        raise ValidationError("Must select a valid PI or lab")


def less_than_1(form, field):
    if float(field.data) > 1:
        raise ValidationError("Fraction must be <=1")


def day_sums_to_1(form, field):
    # Get the entries for same day and person
    existing = Entry.query.filter_by(
        date=form.date.data, personnel=form.personnel.data
    ).all()

    # Store the existing entries in the form so the template can access them in
    # the warning message
    form._other_entries_on_date = existing

    existing_total = 0
    for i in existing:
        # If the form is in edit mode, the Entry object already has an ID (from
        # being originally added to the database). We should not include this
        # entry's fraction in the total so we skip it
        if form.id.data and i.id == int(form.id.data):
            continue
        existing_total += float(i.fraction)

    proposed_total = existing_total + float(field.data)
    use = 1 - existing_total

    if proposed_total > 1:
        raise ValidationError(
            f"""
            For {form.date.data}, {form.personnel.data}'s total fraction in
            other entries is {existing_total} so the fraction of {field.data}
            here will push it to {proposed_total}. Please enter {use} or less,
            or edit the following other entries for this day:
            """
        )


class EffortForm(FlaskForm):
    pi = SelectField("PI", validators=[InputRequired(), not_dashes])
    project = SelectField("project", validators=[InputRequired()])
    date = DateField("date", default=datetime.utcnow)
    personnel = SelectField("personnel", validators=[IsLoggedInUser])
    fraction = DecimalField(
        "fraction", default=1, validators=[day_sums_to_1, less_than_1]
    )
    notes = TextAreaField("notes")
    submit = SubmitField("Submit")
    id = HiddenField("id")

    _other_entries_on_date = None


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()])
    password = StringField("Password", validators=[InputRequired()])
    id = HiddenField("id")
