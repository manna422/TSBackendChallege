from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/nmanna/workspace/TSBackendChallenge/test.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


class Aircraft(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    description = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return '{!s} - {!r}'.format(self.id, self.description)


class LocationRecord(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), primary_key=True, nullable=False)
    datetime = db.Column(db.DateTime, primary_key=True, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    elevation = db.Column(db.Integer, nullable=False)

