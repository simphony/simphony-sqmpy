"""Job monitoring stuff."""
import time
import threading
from Queue import Queue

import saga
from flask_sqlalchemy import SQLAlchemy

from sqmpy.job.helpers import send_state_change_email
from sqmpy.job.models import StagingFile, Job
from sqmpy.job.saga_helper import download_job_files


class JobMonitorThread(threading.Thread):
    """Job monitoring thread."""

    def __init__(self, *args, **kwargs):
        """Init."""
        threading.Thread.__init__(self, *args, **kwargs)
        self.app = kwargs.get('kwargs').get('app')
        self.input_queue = Queue()
        self.db = SQLAlchemy()
        self.db.init_app(self.app)

    def send(self, item):
        """Send a job to monitor."""
        self.input_queue.put(item)

    def close(self):
        """Close the monitor thread."""
        self.input_queue.put(None)
        self.input_queue.join()

    def run(self):
        """Run the monitor thread."""
        while True:
            job_id, job_service, = self.input_queue.get()
            if job_id is None:
                break
            # Process the job
            with self.app.app_context():
                self.process(job_id, job_service)
            self.input_queue.task_done()
            time.sleep(1)
        # Done
        self.input_queue.task_done()
        return

    def process(self, job_id, job_service):
        """Process job state changes."""
        print('Monitoring job %s' % job_id)
        local_job = Job.query.get(job_id)
        remote_job = job_service.get_job(local_job.remote_job_id)

        # TODO: catch saga.IncorrectState
        remote_job_state = remote_job.state

        if local_job.last_status != remote_job_state:
            self.send_notifications(local_job, remote_job)
            self.download_files(local_job, remote_job, job_service)
            self.update_state(local_job, remote_job)

        # Add task back to the queue if still running
        if remote_job_state not in (saga.FAILED,
                                    saga.DONE,
                                    saga.CANCELED,
                                    saga.FINAL,
                                    saga.EXCEPTION):
            self.send((job_id, job_service))

    def send_notifications(self, local_job, remote_job):
        print('sending notifications...')
        # Todo: use signals here
        send_state_change_email(local_job.id,
                                local_job.owner_id,
                                local_job.last_status,
                                remote_job.state,
                                silent=True)

    def download_files(self, local_job, remote_job, job_service):
        print('downloading files...')
        # If there are new files, transfer them back, along
        # with output and error files
        download_job_files(local_job.id,
                           remote_job.description,
                           job_service.get_session())

    def update_state(self, local_job, remote_job):
        print('updating state...')
        # Update last status
        local_job.last_status = remote_job.state
        self.db.session.flush()
        if local_job not in self.db.session:
            self.db.session.merge(local_job)
        self.db.session.commit()
