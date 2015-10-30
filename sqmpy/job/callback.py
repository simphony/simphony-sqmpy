"""
    sqmpy.job.saga_helper
    ~~~~~

    Provides ways to interact with saga classes
"""
import datetime

import saga
from flask import current_app

from ..database import db
from .models import JobStateHistory
import helpers


__author__ = 'Mehdi Sadeghi'


class JobStateChangeCallback(saga.Callback):
    """
    Handle job state changes
    """
    def __init__(self, job, wrapper):
        """
        Initializing callback with an instance of sqmpy job
        :param job: sqmpy job
        :param wrapper: job wrapper
        :return:
        """
        self._job = job
        self._wrapper = wrapper

    def cb(self, obj, key, val):
        """
        Callback itself.
        :param obj: the watched object instance
        :param key:the watched attribute, e.g. state or state_detail
        :param val:the new value of the watched attribute
        :return:
        """
        saga_job = obj
        try:
            template = \
                "### Job State Change Report\n"\
                "ID: {id}\n"\
                "Name: {name}\n"\
                "State Trnsition from {old} ---> {new}\n"\
                "Exit Code: {exit_code}\n"\
                "Exec. Hosts: {exec_host}\n"\
                "Create Time: {create_time}\n"\
                "Start Time: {start_time}\n"\
                "End Time: {end_time}\n"
            current_app.logger.debug(
                template.format(id=self._job.id,
                                name=self._job.name,
                                old=self._job.last_status,
                                new=val,
                                exit_code=saga_job.exit_code,
                                exec_host=saga_job.execution_hosts,
                                create_time=saga_job.created,
                                start_time=saga_job.started,
                                end_time=saga_job.finished))
        except saga.IncorrectState, error:
            # Job is not in final state yet
            current_app.logger.debug('Error querying the saga job: %s' % error)
        except Exception, error:
            current_app.logger.debug(
                'Unknown error while querying the job: %s' % error)

        # Update job status
        if self._job.last_status != val:
            try:
                helpers.send_state_change_email(self._job.id,
                                                self._job.owner_id,
                                                self._job.last_status,
                                                val)
            except Exception, ex:
                current_app.logger.debug(
                    "Callback: Failed to send mail: %s" % ex)
            # Insert history record
            history_record = JobStateHistory()
            history_record.change_time = datetime.datetime.now()
            history_record.old_state = self._job.last_status
            history_record.new_state = val
            history_record.job_id = self._job.id
            db.session.add(history_record)

            # If there are new files, transfer them back, along with output
            #   and error files
            helpers.download_job_files(self._job.id,
                                       self._wrapper.get_job_description(),
                                       self._wrapper.get_saga_session())
            # Update last status
            if self._job not in db.session:
                db.session.merge(self._job)
            self._job.last_status = val
            current_app.logger.debug(
                'Before commit the new value is %s ' % val)
            db.session.commit()

        if val in (saga.DONE,
                   saga.FAILED,
                   saga.CANCELED):
            # Un-register
            current_app.logger.debug(
                "Callback: I un-register myself since job number "
                "{no} is in {state} state".format(no=self._job.id, state=val))
            return False

        # Remain registered
        current_app.logger.debug(
            "Callback: I listen further since job number {no} "
            "is in {state} state".format(no=self._job.id, state=val))
        return True
