"""
    sqmpy.sheduling.views
    ~~~~~~~~~~~~~~~~~~~~~

    View functions for jobs mudule
"""
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.login import login_required

import sqmpy.job.models
from sqmpy import app, admin
from sqmpy.database import db_session


__author__ = 'Mehdi Sadeghi'

# Adding appropriate admin views
admin.add_view(ModelView(sqmpy.job.models.Job, db_session))
admin.add_view(ModelView(sqmpy.job.models.Program, db_session))
admin.add_view(ModelView(sqmpy.job.models.Queue, db_session))


@app.route('/jobs', methods=['GET'])
@login_required
def list_jobs():
    """
    Show list of jobs
    :param request:
    :return:
    """
    return render_template('job/jobs.html', active_page="jobs")
