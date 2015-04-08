"""
    sqmpy.job.views
    ~~~~~~~~~~~~~~~~~~~~~

    View functions for jobs mudule
"""
from flask import request, session, g, redirect, url_for, abort, \
    render_template, flash, send_from_directory
from flask.ext.login import login_required, current_user
from flask.ext.csrf import csrf_exempt
from werkzeug import secure_filename

from .. import app
from . import job_blueprint
from .constants import FileRelation
from .exceptions import JobNotFoundException, FileNotFoundException, JobManagerException
from .forms import JobSubmissionForm
from .models import Job, Resource
from . import services as job_services

__author__ = 'Mehdi Sadeghi'

PER_PAGE = app.config.get('PER_PAGE', 20)


@job_blueprint.route('/job/', methods=['GET'])
def index():
    """
    Entry page for job subsystem
    :return:
    """
    return redirect(url_for('sqmpy.job.list_jobs'))


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


@job_blueprint.route('/jobs/', methods=['GET'], defaults={'page': 1})
@job_blueprint.route('/jobs/page/<int:page>', methods=['GET'])
@login_required
def list_jobs(page):
    """
    Show list of jobs for current user
    :return:
    """
    pagination = job_services.list_jobs(page=page)
    return render_template('job/job_list.html',
                           pagination=pagination,
                           jobs=pagination.items)


@job_blueprint.route('/job/<int:job_id>', methods=['GET'])
@login_required
def detail(job_id):
    """
    Show detail page for a job
    :return:
    """
    job = \
        job_services.get_job(job_id)

    return render_template('job/job_detail.html',
                           job=job,
                           status=job_services.get_job_status(job_id))


@csrf_exempt
@job_blueprint.route('/job/submit', methods=['GET', 'POST'])
@login_required
def submit(job_id=None):
    """
    Submit a single job into the selected machine or queue
    :return:
    """
    form = JobSubmissionForm()
    form.resource.choices = [(h.url, h.name) for h in Resource.query.all()]
    uploaded_files = []
    error = None
    if form.validate_on_submit():
        for f in request.files.getlist('input_files'):
            # Remove unsupported characters from filename
            safe_filename = secure_filename(f.filename)
            # Save file to upload folder under user's username
            uploaded_files.append((safe_filename, f.stream, FileRelation.input))

        # Correct line endings before sending the script content
        # script = ''
        # if form.script.data is not None:
        #     script = form.script.data.replace('\r\n', '\n')

        # Read script file
        script_safe_filename = secure_filename(request.files.get('script_file').filename)
        script_file = (script_safe_filename,
                       request.files.get('script_file').stream,
                       FileRelation.script)
        uploaded_files.append(script_file)

        # Check if user has filled `new_resource' field
        resource_url = form.resource.data
        if form.new_resource.data not in (None, ''):
            resource_url = form.new_resource.data
        job_id = None
        try:
            # Submit the job
            job_id = \
                job_services.submit_job(form.name.data,
                                        resource_url,
                                        uploaded_files,
                                        **form.data)
            # Redirect to list
            return redirect(url_for('.detail', job_id=job_id))
        except JobManagerException, ex:
            flash(str(ex), category='error')
            error = str(ex)

    return render_template('job/job_submit.html', form=form, error=error)

@csrf_exempt
@job_blueprint.route('/job/<int:job_id>/cancel', methods=['GET', 'POST'])
@login_required
def cancel(job_id):
    """
    Cancel a running job
    :param job_id:
    :return:
    """
    if job_id:
        job_services.cancel_job(job_id)
    return redirect(url_for('.detail', job_id=job_id))


# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be show after the upload
@job_blueprint.route('/uploads/<username>/<job_id>/<filename>')
def uploaded_file(username, job_id, filename):
    if username != current_user.name:
        abort(403)
    upload_dir = None
    try:
        upload_dir = job_services.get_file_location(job_id, filename)
    except JobNotFoundException:
        abort(404)
    except FileNotFoundException:
        abort(404)
    # Add proper mimetypes
    import mimetypes
    mimetypes.add_type('text/plain', '.lammps')
    mimetypes.add_type('text/plain', '.couette')
    return send_from_directory(upload_dir, filename)


def url_for_other_page(page):
    """
    Helper to create next page url
    :param page:
    :return:
    """
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)

app.jinja_env.globals['url_for_other_page'] = url_for_other_page