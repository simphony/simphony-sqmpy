from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from sqmpy import app
import sqmpy.models
from sqmpy.database import db_session

TEST = 0

@app.route('/')
def index():
    """Index page handler"""
    global TEST
    TEST += 1
    return 'Hello World! (index: %s)' % TEST

@app.route('/add', methods=['POST', 'GET'])
def add_entry():
    #if not session.get('logged_in'):
    #    abort(401)
    #db = get_db()
    #db.execute('insert into entries (title, text) values (?, ?)',
    #             [request.form['title'], request.form['text']])
    #db.commit()
    #flash('New entry was successfully posted')
    #return redirect(url_for('show_entries'))
    return request.form['filedata']

