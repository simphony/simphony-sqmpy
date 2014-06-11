from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from sqmpy import app
import sqmpy.models
from sqmpy.database import db_session

TEST = 0

@app.route('/', methods=["GET"])
def index():
    """Index page handler"""
    global TEST
    TEST += 1
    return "Hello World! (index: %s)" % TEST

