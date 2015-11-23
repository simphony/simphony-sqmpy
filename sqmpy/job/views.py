"""
    sqmpy.job.views
    ~~~~~~~~~~~~~~~~~~~~~

    View functions for jobs module
"""
import os
import shutil
import tempfile
import mimetypes

from flask import request, redirect, url_for, abort, \
    render_template, flash, send_from_directory, Blueprint, g
from flask.ext.login import login_required
from flask.ext.csrf import csrf_exempt
from werkzeug import secure_filename
import names

from .exceptions import JobNotFoundException
from .forms import JobSubmissionForm
from .models import Resource
from .constants import ScriptType
from . import manager as job_services
from ..utils import get_redirect_target

__author__ = 'Mehdi Sadeghi'


job_blueprint = Blueprint('jobs', __name__, url_prefix='/jobs')


@job_blueprint.context_processor
def job_cnx_processor():
    return dict(active_page=job_blueprint.name)


@job_blueprint.before_request
def add_job_list(*args, **kwargs):
    g.__jobs = {}


@job_blueprint.route('/', methods=['GET'], defaults={'page': 1})
@job_blueprint.route('/page<int:page>', methods=['GET'])
@login_required
def index(page):
    """
    Entry page for job subsystem
    :return:
    """
    pagination = job_services.list_jobs(page=page)
    return render_template('job/job_list.html',
                           pagination=pagination,
                           jobs=pagination.items)


@job_blueprint.route('/<string:job_id>', methods=['GET'])
@login_required
def detail(job_id):
    """
    Show detail page for a job
    :return:
    """
    try:
        job = job_services.get_job(job_id)
        return render_template('job/job_detail.html', job=job)
    except JobNotFoundException:
        abort(404)


@csrf_exempt
@job_blueprint.route('/new', methods=['GET', 'POST'])
@login_required
def submit(job_id=None):
    """
    Submit a single job into the selected machine or queue
    :return:
    """
    form = JobSubmissionForm()

    # Fill resource dropdown list choices
    form.resource.choices = [(h.url, h.name) for h in Resource.query.all()]

    # Temporary directory to store uploaded files before job object creation
    # We use a simple protocol here. The script file with start with `script_'
    # in file name and input files will start with `input_' in their names.
    # This will help us not to pass around lots of parameters, only upload
    # directory would be enough.
    upload_dir = tempfile.mkdtemp()

    if form.validate_on_submit():
        # Save script file to upload directory
        script_file = request.files.get('script_file')

        # Make sure file name is safe
        script_safe_filename = secure_filename(script_file.filename)

        # Recognize type of the script
        script_type = _recognize_script_type(script_safe_filename)

        # TODO: recognize she bang in scripts
        script_file.save(os.path.join(upload_dir,
                         'script_' + script_safe_filename))

        # Save input files to upload directory
        for f in request.files.getlist('input_files'):
            if f.filename not in (None, ''):
                # Remove unsupported characters from filename
                safe_filename = secure_filename(f.filename)
                # Save file to upload temp directory
                f.save(os.path.join(upload_dir, 'input_' + safe_filename))

        # Assing the default value
        resource_url = 'localhost'

        # Check if user has filled `new_resource' field
        if form.resource.data != 'None':
            resource_url = form.resource.data
        # New url field and priority
        if form.new_resource.data not in (None, ''):
            resource_url = form.new_resource.data

        try:
            # Submit the job
            job_id = \
                job_services.submit(resource_url,
                                    upload_dir,
                                    script_type,
                                    job_name=form.name.data
                                    or names.get_last_name(),
                                    **form.data)
            # Redirect to list
            return redirect(url_for('.detail', job_id=job_id))
        except Exception, ex:
            # Delete temporary directory with its contents
            if os.path.exists(upload_dir):
                shutil.rmtree(upload_dir)
            if "message too long" in str(ex):
                flash("sftp error: Make sure you can do sftp/scp to the"
                      " remote host and there are no echo statements in the"
                      " .bashrc of the remote machine.", category='error')
            else:
                flash(str(ex), category='error')

    return render_template('job/job_submit.html', form=form)


@job_blueprint.route('/<string:job_id>/resubmit', methods=['POST'])
@login_required
def resubmit(job_id):
    """
    Create and submit a new job out of an existing one
    :return:
    """
    try:
        # Submit the job
        new_job_id = \
            job_services.resubmit(job_id)
        flash('Job resubmitted successfully', category='success')
        # Redirect to the job's detail page
        return redirect(url_for('.detail', job_id=new_job_id))
    except Exception, ex:
        flash(str(ex), category='error')
        raise
        return redirect(get_redirect_target() or url_for('.index'))


@csrf_exempt
@job_blueprint.route('/<int:job_id>/cancel', methods=['GET', 'POST'])
@login_required
def cancel(job_id):
    """
    Cancel a running job
    :param job_id:
    :return:
    """
    job_services.cancel_job(job_id)
    return redirect(url_for('.detail', job_id=job_id))


# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be show after the upload
@job_blueprint.route('/<int:job_id>/files/<string:file_name>')
@login_required
def get_file(job_id, file_name):
    # Get file location
    job_file = job_services.get_file_by_name(job_id, file_name)

    # Add extra mime types
    mimetypes.add_type('text/plain', '.lammps')
    mimetypes.add_type('text/plain', '.couette')
    print 'Got these: ', (job_file.location, job_file.name)
    return send_from_directory(job_file.location, job_file.name)


@job_blueprint.app_template_global(name='url_for_other_page')
def url_for_other_page(page):
    """
    Helper to create next page url
    :param page:
    :return:
    """
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


def _recognize_script_type(script_safe_filename):
    """
    Find type of the script.
    """
    if script_safe_filename.endswith('.sh'):
        return ScriptType.shell.value
    elif script_safe_filename.endswith('.py'):
        return ScriptType.python.value
    else:
        raise Exception('Invalid script type. '
                        'Only python or shell scripts are allowed.')
