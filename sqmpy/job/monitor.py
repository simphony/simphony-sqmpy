"""Job monitoring stuff."""
import time
import threading
from Queue import Queue

from flask_sqlalchemy import SQLAlchemy

from sqmpy.job.helpers import send_state_change_email
from sqmpy.job.models import StagingFile, Job


class JobMonitorThread(threading.Thread):
    """Job monitoring thread."""

    def __init__(self, *args, **kwargs):
        """Init."""
        threading.Thread.__init__(self, *args, **kwargs)
        self.input_queue = Queue()
        self.db = SQLAlchemy()

    def send(self, item):
        """Send a job id to monitor."""
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
        remote_job = job_service.get_job(job.remote_job_id)

        if self.is_state_changed(local_job, remote_job):
            self.send_notifications(local_job, remote_job)
            self.download_files(local_job, remote_job)
            self.update_state(local_job, remote_job)

    def get_state(self, job_id, job_service):
        job = Job.query.get(job_id)
        remote_job = job_service.get_job(job.remote_job_id)
        return remote_job.state


    def is_state_changed(self, local_job, remote_job):
        return local_job.last_status == remote_job.state

    def send_notifications(self, local_job, remote_job):
        print('sending notifications...')
        return
        # Todo: use signals here
        send_state_change_email(local_job.id,
                                local_job.owner_id,
                                local_job.last_status,
                                remote_job.state,
                                silent=True)

    def download_files(self, local_job, remote_job):
        print('downloading files...')
        pass
        # If there are new files, transfer them back, along
        # with output and error files
        #download_job_files(self._job.id,
        #                   self._saga_job.description,
        #                   self._job_service.get_session())

    def update_state(self, local_job, remote_job):
        print('updating state...')
        # Update last status
        local_job.last_status = remote_job.state
        self.db.session.flush()
        #if self._job not in db.session:
        #    db.session.merge(self._job)
        #db.session.commit()
        #if val in (saga.FAILED,
        #           saga.DONE,
        #           saga.CANCELED,
        #           saga.FINAL,
        #           saga.EXCEPTION):
        #            return
        #    except saga.IncorrectState:
        #        pass

