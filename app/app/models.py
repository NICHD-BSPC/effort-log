from datetime import datetime
from app import db
import flask_login


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pi = db.Column(db.String(64), index=True)
    project = db.Column(db.String(120), index=True)
    date = db.Column(db.Date, index=True, default=datetime.utcnow)
    personnel = db.Column(db.String(64), index=True)
    fraction = db.Column(db.Float, default=1)
    notes = db.Column(db.String(1000))

    order = ["pi", "project", "date", "personnel", "fraction", "notes"]

    def __repr__(self):
        return f"<Entry [{self.id}] {self.personnel} | {self.date} | {self.pi} | {self.project} | {self.fraction}>"

    def to_dict(self):
        return {i: getattr(self, i) for i in self.order}

class User(flask_login.UserMixin, db.Model):
    """
    Standard Flask user object, mostly just a container. See
    https://flask-login.readthedocs.io/en/latest/#your-user-class for what is
    required on this class, and what is inherited from UserMixin
    """
    username = db.Column(db.String(120), primary_key=True)
    dn = db.Column(db.String(240), index=True)
    name = db.Column(db.String(120), index=True)
    data = db.Column(db.String(1000))
    order = ["username", "dn", "name", "data"]

    def __init__(self, username, dn, data):
        self.username = username
        self.dn = dn
        self.data = build_user_data(data)
        self.name = data["displayName"]

    def __repr__(self):
        return self.username

    def get_id(self):
        # Note: Flask-Login requires this to be a string.
        return self.username
    
    def to_dict(self):
        return {i: getattr(self, i) for i in self.order}

def build_user_data(data):
    # For security reasons, save limited information.
    user_data = {
        "displayName": data["displayName"]
    }
    return str(user_data)