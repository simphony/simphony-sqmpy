"""
    sqmpy.job.views
    ~~~~~~~~~~~~~~~~~~~~~

    View functions for jobs module
"""
import os
import shutil
import tempfile
import mimetypes

from flask import request, redirect, url_for, abort,\
    render_template, flash, send_from_directory, Blueprint, g
from flask_login import login_required
from werkzeug import secure_filename
from flask_wtf import CSRFProtect

from sqmpy.job.exceptions import JobNotFoundException
from sqmpy.job.forms import JobSubmissionForm, DropletJobSubmissionForm
from sqmpy.job.models import Resource
from sqmpy.job.constants import ScriptType
from sqmpy.job import manager as job_services
from sqmpy.utils import get_redirect_target
from sqmpy.job.droplet_script import droplet_script_template

__author__ = 'Mehdi Sadeghi'


job_blueprint = Blueprint('jobs', __name__, url_prefix='/jobs')
csrf = CSRFProtect()


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


@csrf.exempt
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
                                    **form.data)
            # Redirect to list
            return redirect(url_for('.detail', job_id=job_id))
        except Exception, ex:
            # Delete temporary directory with its contents
            if os.path.exists(upload_dir):
                shutil.rmtree(upload_dir)
            # This is a workaround to recognize the error, regarding cases,
            # when user's login page produces a lot of text upon SSH, which
            # confuses sftp. This is a well known issue on the net and
            # this is this is a trick to recognize the error.
            raise
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
        return redirect(get_redirect_target() or url_for('.index'))


@csrf.exempt
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


@csrf.exempt
@job_blueprint.route('/new_droplet', methods=['GET', 'POST'])
@login_required
def submit_droplet(job_id=None):
    """
    Submit a single job into the selected machine or queue
    :return:
    """
    form = DropletJobSubmissionForm()

    # Fill resource dropdown list choices
    form.resource.choices = [(h.url, h.name) for h in Resource.query.all()]

    # Temporary directory to store uploaded files before job object creation
    # We use a simple protocol here. The script file with start with `script_'
    # in file name and input files will start with `input_' in their names.
    # This will help us not to pass around lots of parameters, only upload
    # directory would be enough.
    upload_dir = tempfile.mkdtemp()

    if form.validate_on_submit():
        # Populate the template
        droplet_script = droplet_script_template.format(
            simulation_name=form.simulation_name.data,
            simulation_box_side_length=form.simulation_box_side_length.data,
            mesh_grid_size=form.mesh_grid_size.data,
            end_time=form.end_time.data,
            time_step=form.time_step.data,
            number_of_states=form.number_of_states.data,
            wetting_angle=form.wetting_angle.data,
            drop_volume=form.drop_volume.data,
            dynamic_viscosity_of_gas_phase=form.dynamic_viscosity_of_gas_phase.data,
            density_of_gas_phase=form.density_of_gas_phase.data,
            dynamic_viscosity_of_liquid_phase=form.dynamic_viscosity_of_liquid_phase.data,
            density_of_liquid_phase=form.density_of_liquid_phase.data,
            surface_tension_of_liquid_gas_interface=form.surface_tension_of_liquid_gas_interface.data)

        # Recognize type of the script
        script_type = ScriptType.python.value

        script_file = open(os.path.join(upload_dir, 'script_droplet_app.py'), 'w')
        script_file.write(droplet_script)
        script_file.close()

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
                                    **form.data)
            # Redirect to list
            return redirect(url_for('.detail', job_id=job_id))
        except Exception, ex:
            # Delete temporary directory with its contents
            if os.path.exists(upload_dir):
                shutil.rmtree(upload_dir)
            # This is a workaround to recognize the error, regarding cases,
            # when user's login page produces a lot of text upon SSH, which
            # confuses sftp. This is a well known issue on the net and
            # this is this is a trick to recognize the error.
            raise
            if "message too long" in str(ex):
                flash("sftp error: Make sure you can do sftp/scp to the"
                      " remote host and there are no echo statements in the"
                      " .bashrc of the remote machine.", category='error')
            else:
                flash(str(ex), category='error')

    return render_template('job/droplet_submit.html', form=form)