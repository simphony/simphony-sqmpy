"""
    sqmpy.job.views
    ~~~~~~~~~~~~~~~~~~~~~

    View functions for jobs mudule
"""
from flask_login import current_user
import os

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, send_from_directory
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.login import login_required

from werkzeug import secure_filename

from sqmpy import app, admin
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
    job = \
        job_services.get_job(job_id)

    return render_template('job/job_detail.html', job=job)


@job_blueprint.route('/job/submit', methods=['GET', 'POST'])
#@job_blueprint.route('/job/submit/<job_id>', methods=['GET'])
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
        file = request.files['input_file']
        input_file_location = None
        if file:
            # Remove unsupported characters from filename
            safe_filename = secure_filename(file.filename)
            # Save file to upload folder under user's username
            upload_dir = os.path.join(app.config['STAGING_FOLDER'], current_user.name)
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            input_file_location = os.path.join(upload_dir, safe_filename)
            file.save(input_file_location)

            #return redirect(url_for('uploaded_file',
            #                        filename=safe_filename))
        # Submit the job
        job_id = \
            job_services.submit_job(form.name.data, form.resource.data, form.script.data, input_file_location, form.description.data)
        # Redirect to list
        return redirect(url_for('.detail', job_id=job_id))

    return render_template('job/job_submit.html', form=form)

# # This route is expecting a parameter containing the name
# # of a file. Then it will locate that file on the upload
# # directory and show it on the browser, so if the user uploads
# # an image, that image is going to be show after the upload
# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['STAGING_FOLDER'],
#                                filename)
#
# from werkzeug import SharedDataMiddleware
# app.add_url_rule('/uploads/<filename>', 'uploaded_file',
#                  build_only=True)
# app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
#     '/uploads':  app.config['STAGING_FOLDER']
# })
