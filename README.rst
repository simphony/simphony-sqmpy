====================
Simple Queue Manager
====================

.. image:: https://travis-ci.org/simphony/sqmpy.svg?branch=master
        :target: https://travis-ci.org/simphony/sqmpy

.. image:: https://codecov.io/github/simphony/sqmpy/coverage.svg?branch=master
    :target: https://codecov.io/github/simphony/sqmpy?branch=master

sqmpy stands for simple queue manager written in python and is a web application which is based on Flask miroframework
and SAGA-Python distributed computing access layer.
sqmpy lets user to submit simple python or shell scripts on remote machines. Then user can monitor the running job in
job detail page. The notification system will send emails after status changes to the user. Moreover sqmpy lets user
to have a history of previous jobs and all files related to those jobs.

Dependencies
------------
sqmpy has a few dependencies which will be installed while installing with *python setup* or *pip*:

- SAGA-python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- Flask-CSRF
- Flask-Uploads
- enum34
- py-bcrypt
- python-ldap (for experimental LDAP login support)

Installation
------------
I suggest to install a virtaul environment to try sqmpy or if you want to run it on your local machine. If you have
virtual-env installed then:

::

    $ virtual-env --no-site-packages sqmpy-env
    $ . sqmpy-env/bin/activate

If you don't have virutal-env on your machine then try to download it. **Please be aware that this is outdated
since new versions of virtualenv do not download and install pip and setuptools for security reasons**:

::

    $ wget https://raw.githubusercontent.com/pypa/virtualenv/1.9.X/virtualenv.py
    $ python virtualenv.py --no-site-packages sqmpy-env
    $ . sqmpy-env/bin/activate

If you clone from github then you can easily install the requirements with pip and then run the program directly:

::

    $ git clone git://github.com/simphony/sqmpy.git
    $ cd sqmpy
    $ pip install -r requirements.txt
    $ python run.py

**Make sure to change values inside config.py before running the program**
To install from git:

::

    $ git clone git://github.com/simphony/sqmpy.git
    $ cd sqmpy
    $ python setup install

To install sqmpy from pypi:

::

    $ pip install sqmpy

Please remember that installing from pypi will only install sqmpy package without config, database and run file. You have
to make them yourself for now.

Configuration
-------------
There are a few settings which sqmpy can read from a configuration file. There is a *default_config* python module
in sqmpy package that contains default configuration values. The same configurations can be read from a user defined
config file via **SQMPY_CONFIG** environment variable:

::

    $ export SQMPY_CONFIG = /path/to/config/file/config.py
    $ python run.py

Run With No Configuration
-------------------------
In this case sqmpy will user in-memory sqlite db, logging to stdout, and a temp folder for staging files. State
will lost after restarting the application.

Using sqmpy
-----------
sqmpy is a flask web application therefore it runs like any other flask applications. Put the following code in
a python file called run.py and run it:

::

    from sqmpy.factory import create_app
    app = create_app('path_to_config.py') # Config is optional
    app.run('0.0.0.0', port=5001, debug=True)

About Files and Folders, Local or Remote
----------------------------------------
sqmpy will create a *sqmpy.log* and *sqmpy.db* and a staging folder called *staging*. The path to these files are
being read from config values: ``LOG_FILE``, ``SQLALCHEMY_DATABASE_URI`` and ``STAGING_FOLDER``.
Staginf folder will contain uploaded files and script files created by sqmpy. Moreover on remote machiens
sqmpy will create another folder called *sqmpy* in user home directory and will upload files there before
running tasks. For each job one folder will be created and will be set as job working directory. This folder
will contain input and output files as well as script file and any other files being produced or consumed by
the remote job.

.. image:: https://www.herokucdn.com/deploy/button.png
    :target: https://heroku.com/deploy
