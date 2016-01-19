=====
Sqmpy
=====

.. image:: https://travis-ci.org/simphony/sqmpy.svg?branch=master
        :target: https://travis-ci.org/simphony/sqmpy

.. image:: https://codecov.io/github/simphony/sqmpy/coverage.svg?branch=master
    :target: https://codecov.io/github/simphony/sqmpy?branch=master

Sqmpy is a web application based on `Flask miroframework <http://flask.pocoo.org/>`_
and `RADICAL-SAGA <http://radical-cybertools.github.io/saga-python/>`_ distributed computing access layer.
Sqmpy lets user to submit simple python or shell scripts on remote machines. Then user can monitor the running job in
job detail page. The notification system will send emails after status changes to the user. Moreover sqmpy lets user
to have a history of previous jobs and all files related to those jobs.


Repository
----------
Sqmpy is hosted on Github: https://github.com/simphony/sqmpy


Requirements
------------
Sqmpy has a few dependencies which will be installed while installing with *python setup* or *pip*:

- SAGA-python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- Flask-CSRF
- Flask-Uploads
- enum34
- py-bcrypt


Optional Requirements
---------------------
In order to use LDAP support, a few libraries and a python package should be installed on the system.
In an Ubuntu machine they could be installed this way:

    # apt-get install libldap2-dev libsasl2-dev libssl-dev

In OpenSUSE they could be installed this way:

    # zupper in openldap2-devel cyrus-sasl-devel

The following python package should be installed afterwards:

- python-ldap

Configuration
-------------
Sqmpy will locad configuration keys from a file called `config.py` inside the application directory.
Alternatively, configurations can be loaded from a user defined python file using **SQMPY_CONFIG**
environment variable:

::

    $ export SQMPY_CONFIG = /path/to/config/file/config.py

Even though Sqmpy will run with default configuration, for a proper installation certain settings inside `config.py`
 file must be changed. This will be explained shortly for server setup, here is a short overview:

::

    SECRET_KEY = 'This should be replaced with a long unique string in your setup'
    CSRF_SESSION_KEY = "Same for this one"

Above two keys *must* be changed. There are more configuration options which are explained in `config.py` file.


Local Installation
------------------
Sqmpy is meant to be installed on a web server and used as a multi-user website. However, in early stages and for
demonstration purposes one can run it on a local computer. I will explain further how to install it on a web server.
I suggest to install a virtaul environment to try Sqmpy when running it on your local machine:

::

    $ virtualenv --no-site-packages sqmpy-env
    $ source sqmpy-env/bin/activate

If you don't have virutalenv on your machine then try to download it. **Please be aware that this is outdated
since new versions of virtualenv do not download and install pip and setuptools for security reasons**.

::

    $ wget https://raw.githubusercontent.com/pypa/virtualenv/1.9.X/virtualenv.py
    $ python virtualenv.py --no-site-packages sqmpy-env
    $ source sqmpy-env/bin/activate

If you clone Sqmpy from Github then you can easily install the requirements with pip and then run the program directly:

::

    $ git clone git://github.com/simphony/sqmpy.git
    $ cd sqmpy
    $ pip install -r requirements.txt
    $ python run.py

Then browse to http://127.0.0.1:5000 to use the application. By default, Sqmpy uses user's SSH keys when accessing
 remote resources. Therefore, user must have passwordless SSH access to remote machines.

.. Note::
  The above setup uses a lightweight internal development web server which might be slow and problematic. It
  is only mentioned for demonstration and development purposes. Read on to `Gunicorn` section to learn more.



Running with Gunicorn
---------------------
Running with Gunicorn is the preferred way to use Sqmpy, either local or on a web server as a proxy.
First install its python package:

::

    $ pip install gunicorn

Inside Sqmpy's folder, there is a file called `gunicorn_cfg.py`. You can change that file to configure Gunicorn,
e.g. to change default port. To run Sqmpy with gunicorn run:

::

    $ gunicorn -c gunicorn_cfg.py run:app

In order to run Sqmpy as a daemon:

::

    $ gunicorn -c gunicorn_cfg.py run:app -D


Enabling LDAP Support
---------------------

If you use LDAP in your organization it is possible to configure Sqmpy to use it as authentication backend. The
following keys should be changed:

::

    LOGIN_DISABLED = False
    USE_LDAP_LOGIN = True
    LDAP_SERVER = 'ldap.example.com' # your ldap server here
    LDAP_BASEDN = 'ou=People,ou=IWM,o=Fraunhofer,c=DE' # your BASEDN here

We have only tested this inside IWM, so it might not work for you, hence experimental!
There is one point here. Sqmpy, by default, will use SSH keys of the current user to connect to remote machines in
order to run submitted jobs there. To force it to use the login information, e.g. in LDAP case, change the following
key::

    SSH_WITH_LOGIN_INFO = True


Enabling SSL Support
--------------------

In case of a multiuser setup, SSL must be enabled. Otherwise, users' information will be transferred in clear-text
throught the network. Here we generate a self-signed SSL certificate to use with Gunicorn::

    $ openssl genrsa -des3 -passout pass:x -out server.pass.key 2048
    $ openssl rsa -passin pass:x -in server.pass.key -out server.key
    $ rm server.pass.key
    $ openssl req -new -key server.key -out server.csr
    $ openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt

Now we have three files, called server.crt, server.csr and, server.key. Edit gunicorn_cfg.py and uncomment
 certificate lines::

    keyfile = 'server.key'
    certfile = 'server.crt'

    # And re-run Sqmpy
    $ gunicorn -c gunicorn_cfg.py run:app

Now you should be able to browse https://localhost:5000 which is SSL protected.

Deploying on a Web Server
-------------------------
As a Flask application, sqmpy can be deployed in multiple ways: http://flask.pocoo.org/docs/0.10/deploying/.
The best deployment scenario for Sqmpy is running it as a WSGI application and use nginx to forward requests
to it. It is beyond scope of this README to explain deployment WSGI application with web servers. There are many
good guides on the internet, however we will update this guide if users ask for it. We strongly recommend using
Sqmpy + Gunicorn + nginx.


About Files and Folders, Local or Remote
----------------------------------------
Sqmpy will create a *sqmpy.log* and *sqmpy.db* and a staging folder called *staging*. The path to these files are
read from config values: ``LOG_FILE``, ``SQLALCHEMY_DATABASE_URI`` and ``STAGING_FOLDER``.
Staging folder will contain uploaded files and script files created by Sqmpy. Moreover, on remote machines
Sqmpy will create another folder called *sqmpy* in user's home directory and will upload files there before
running tasks. For each job one folder will be created and will be set as job's working directory. This folder
will contain input and output files as well as script file and any other files being produced or consumed by
the remote job.
