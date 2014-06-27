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
from sqmpy.job.forms import JobSubmissionForm
from sqmpy.job.models import Resource
import sqmpy.job.services as job_services


__author__ = 'Mehdi Sadeghi'

# Adding appropriate admin views
admin.add_view(ModelView(job_models.Job, db_session))
admin.add_view(ModelView(job_models.Resource, db_session))
#admin.add_view(ModelView(job_models.Program, db_session))
#admin.add_view(ModelView(job_models.Queue, db_session))


@job_blueprint.route('/job', methods=['GET'])
def index():
    """
    Entry page for job subsystem
    :return:
    """
    return list_jobs()


#@job_blueprint.route('/job/list', methods=['GET'])
@login_required
def list_jobs(job_id=None):
    """
    Show list of jobs
    :param request:
    :return:
    """
    if job_id is not None:
        # Get the job and show job detail page
        return render_template('job/job_detail.html')
    else:
        return render_template('job/job_list.html', jobs=job_services.list_jobs())


@job_blueprint.route('/job/<int:job_id>', methods=['GET'])
@login_required
def detail(job_id):
    """
    Show detail page for a job
    :return:
    """
    job=None
    return render_template('job/job_detail.html', job=job)


@job_blueprint.route('/job/submit', methods=['GET', 'POST'])
@job_blueprint.route('/job/submit/<job_id>', methods=['GET'])
@login_required
def submit(job_id=None):
    """
    Submit a single job into the selected machine or queue
    :return:
    """
    if job_id is not None:
        pass

    form = JobSubmissionForm()
    form.resource.choices = [(h.id, h.url) for h in Resource.query.all()]

    if request.method == 'POST' and form.validate():
        # Submit the job
        job_id = \
            job_services.submit_job(form.name.data, form.resource.data, form.script.data, form.input_file.data, form.description.data)
        # Redirect to list
        return redirect(url_for('.detail', job_id=job_id))

    return render_template('job/job_submit.html', form=form)