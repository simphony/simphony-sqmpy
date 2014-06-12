__author__ = 'Mehdi Sadeghi'


class JobController:
    """ 
    This class is responsible to keep jobs information 
    and handles controll messages for jobs
    """

    def __init__(self):
        self.__jobs = {}

    def submit_job(self, job, *args, **kwargs):
        """
        Submit a new job
        @job: an instance of Job class
        """
        assert isinstance(job, Job)
        if job is not None and job.get_name() not in self.__jobs:
            self.__jobs[job.get_name()] = job

    def get_job(self, job_name, *args, **kwargs):
        """
        Get a job
        @job_name: name of the job
        """
        if job_name in self.__jobs:
            return self.__jobs[job_name]
