Simple Queue Manager
====================

 sqmpy stands for simple queue manager written in python and is a web application which is based on Flask miroframework
 and SAGA-Python distributed computing access layer.
 Sqmpy lets user to submit simple python or shell scripts on remote machines. Then user can monitor the running job in job detail page. The notification system will send emails after status changes to the user. Moreover sqmpy lets user
 to have a history of previous jobs and all files related to those jobs.

## Dependencies
Sqmpy has a few dependencies which will be installed while installing with _python setup_ or _pip_:
* SAGA-python
* Flask
* Flask-SQLAlchemy
* Flask-Login
* Flask-WTF
* Flask-Admin
* Flask-CSRF
* enum34
* py-bcrypt

## Installation
I suggest to install a virtaul environment to try sqmpy or if you want to run it on your local machine. If you have
virtual-env installed then:
   
    $ virtual-env --no-site-packages sqmpy-env
    $ . sqmpy-env/bin/activate
    
If you don't have virutal-env on your machine then try to download it. **Please be aware that this is outdated since new versions of virtualenv do not download and install pip and setuptools for security reasons**:

    $ wget https://raw.githubusercontent.com/pypa/virtualenv/1.9.X/virtualenv.py
    $ python virtualenv.py --no-site-packages sqmpy-env
    $ . sqmpy-env/bin/activate
    

    
To install sqmpy from pypi:

    pip install sqmpy
    
To install from git:

    git clone git://github.com/mehdix/simple-queue-manager.git
    cd simple-queue-manager
    python setup install
    
## Configuration
There are a few settings which sqmpy can read from a configuration file. There is a _default_config_ python module in sqmpy package that contains default configuration values. The same configurations can be read from a user defined config file via __SQMPY_CONFIG__ environment variable:

    export SQMPY_CONFIG = /path/to/config/file/config.py
    python run.py

### Run With No Configuration
In this case sqmpy will user in-memory sqlite db, logging to stdout, and a temp folder for staging files. State
will lost after restarting the application.

## Using Sqmpy
Sqmpy is a flask web application therefor it runs like any other flask applications. Put the following code in apython file called run.py and run it:

    from sqmpy import app
    app.run('0.0.0.0', port=5001, debug=True)
    
## About Files and Folders, Local or Remote
Sqmpy will create a _sqmpy.log_ and _sqmpy.db_ and a staging folder called _staging_. The path to these files are being read from config values: ```LOG_FILE```, ```SQLALCHEMY_DATABASE_URI``` and ```STAGING_FOLDER```.
Staginf folder will contain uploaded files and script files created by sqmpy. Moreover on remote machiens Sqmpy will create another folder called _sqmpy_ in user home directory and will upload files there before running tasks. For each job one folder will be created and will be set as job working directory. This folder will contain input and output files as well as script file and any other files being produced or consumed by the remote job.
