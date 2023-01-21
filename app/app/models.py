from datetime import datetime
from app import db


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
