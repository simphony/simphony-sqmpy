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

from sqmpy import admin
from sqmpy.database import db_session
from sqmpy.job import models as job_models
from sqmpy.job import job_blueprint


__author__ = 'Mehdi Sadeghi'

# Adding appropriate admin views
admin.add_view(ModelView(job_models.Job, db_session))
admin.add_view(ModelView(job_models.Program, db_session))
admin.add_view(ModelView(job_models.Queue, db_session))


@job_blueprint.route('/job', methods=['GET'])
@job_blueprint.route('/jobs', methods=['GET'])
@job_blueprint.route('/job/list', methods=['GET'])
@job_blueprint.route('/job/<job_id>', methods=['GET'])
@login_required
def list_jobs(job_id=None):
    """
    Show list of jobs
    :param request:
    :return:
    """

    if job_id is not None:
        # Get the job and show job detail page
        return render_template('job/job_detail.html', active_page="jobs")
    else:
        return render_template('job/job_list.html', active_page="jobs")
