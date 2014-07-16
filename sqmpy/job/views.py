"""
    sqmpy.job.views
    ~~~~~~~~~~~~~~~~~~~~~

    View functions for jobs mudule
"""
from flask import request, session, g, redirect, url_for, abort, \
    render_template, flash, send_from_directory
from flask.ext.login import login_required, current_user

from werkzeug import secure_filename

from sqmpy.job import job_blueprint
from sqmpy.job.exceptions import JobNotFoundException, FileNotFoundException
from sqmpy.job.forms import JobSubmissionForm
from sqmpy.job.models import Resource
import sqmpy.job.services as job_services

__author__ = 'Mehdi Sadeghi'


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
        f = request.files['input_file']
        input_files = None
        if f:
            # Remove unsupported characters from filename
            safe_filename = secure_filename(f.filename)
            # Save file to upload folder under user's username
            input_files = [(safe_filename, f.stream)]
            #raise Exception('for fun')

        # Correct line endings before sending the script content
        script = ''
        if form.script.data is not None:
            script = form.script.data.replace('\r\n', '\n')

        # Submit the job
        job_id = \
            job_services.submit_job(form.name.data,
                                    form.resource.data,
                                    script,
                                    input_files,
                                    form.description.data)
        # Redirect to list
        return redirect(url_for('.detail', job_id=job_id))

    return render_template('job/job_submit.html', form=form)

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

    #if not os.path.isfile(os.path.join(upload_dir, filename)):
    #    abort(404)
    return send_from_directory(upload_dir, filename)
