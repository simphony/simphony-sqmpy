__author__ = 'Mehdi Sadeghi'

from flask import Flask
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(120))
    text = db.Column(db.UnicodeText, nullable=False)

admin = Admin(app)
admin.add_view(ModelView(Post, db.session))