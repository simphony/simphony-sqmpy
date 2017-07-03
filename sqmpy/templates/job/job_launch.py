import yaml
import sys
import shutil
import tempfile
import os

from werkzeug import secure_filename
from sqmpy.job import manager

stream = open("launchScript.yml", "r")
doc = yaml.load(stream)

# Remote and local job
l_job = doc['job']
r_job = doc['job']['remote']

# Launches the job locally
if l_job['resource_type']['value'] == 'local':
    call = [l_job['command']['value']]
    for arg in l_job['arguments']['value']:
        print(arg)
        call.append(arg)

    out_file = sys.stdout
    err_file = sys.stderr

    if l_job['out_file'] and l_job['out_file']['value']:
        out_file = open(l_job['out_file']['value'], 'w+')
    if l_job['err_file'] and l_job['err_file']['value']:
        err_file = open(l_job['err_file']['value'], 'w+')

    subprocess.call(
        call,
        stdout=out_file,
        stderr=err_file
    )

    if l_job['out_file'] and l_job['out_file']['value']:
        out_file.close()
    if l_job['err_file'] and l_job['err_file']['value']:
        err_file.close()

# Launches the job remotely ( based on the send job view from sqmpy)
elif l_job['resource_type']['value'] == 'remote':

    # Make a temporal upload dir like in the saga script
    upload_dir = tempfile.mkdtemp()

    # Fetch the filename and the script type
    script_filename = l_job['arguments']['value'][0]
    script_type = l_job['script_type']['value']

    # Copy Files
    for f in request.files.getlist('input_files'):
        if f.filename not in (None, ''):
            # Remove unsupported characters from filename
            safe_filename = secure_filename(f.filename)

            # Save file to upload temp directory
            f.save(os.path.join(upload_dir, 'input_' + safe_filename))

    # Fetch the resource url
    resource_url = r_job['resource_url']['value']

    # Parse the properties ( More can be added )
    data = {
        'working_directory': r_job['working_directory']['value'],
        'description': r_job['description'],
        'total_cpu_count': r_job['total_cpu']['value'],
        'walltime_limit': r_job['wall_time']['value'],
        'spmd_variation': r_job['spmd_variation']['value'],
        'queue': r_job['queue']['value'],
        'project': l_job['project']['value'],
        'total_physical_memory': r_job['total_physical_memory']['value'],
    }

    shutil.copy2(script_filename, os.path.join(
        upload_dir,
        'script_' + script_filename)
    )

    job_id = manager.submit(
        resource_url,
        upload_dir,
        script_type,
        **data
    )
else:
    print 'Invalid resource type'
