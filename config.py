"""
    config
    ~~~~~
    This module contains configuration keys for the application.
    See http://flask.pocoo.org/docs/config/ for more information.
"""
import os
_basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """
    Base config class for application
    """
    DEBUG = False

    # Server host and port. Supports subdomains myapp.dev:5000
    #SERVER_NAME = '0.0.0.0:5001'

    ADMINS = frozenset(['sade@iwm.fraunhofer.de'])
    SECRET_KEY = "This string will be replaced with a proper key in production."

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'sqmpy.db')
    DATABASE_CONNECT_OPTIONS = {}

    THREADS_PER_PAGE = 8

    CSRF_ENABLED = True
    CSRF_SESSION_KEY = "somethingimpossibletoguess"

    # Recaptcha for localhost
    RECAPTCHA_USE_SSL = False
    RECAPTCHA_PUBLIC_KEY = '6LeYIbsSAAAAACRPIllxA7wvXjIE411PfdB2gt2J'
    RECAPTCHA_PRIVATE_KEY = '6LeYIbsSAAAAAJezaIq3Ft_hSTo0YtyeFG-JgRtu'
    RECAPTCHA_OPTIONS = {'theme': 'white'}


    # Logging options
    LOG_FILE = os.path.join(_basedir, 'sqmpy.log')

    # Staging options
    STAGING_FOLDER = os.path.join(_basedir, 'staging')

    # SMTP Configs, uncomment any line to add it
    #TODO Right now only MAIL_SERVER is being read, fix others.
    MAIL_SERVER = 'iwmcas.iwm.fraunhofer.de'
    DEFAULT_MAIL_SENDER = 'sade@iwm.fraunhofer.de'

    PER_PAGE = 5


class DevelopmentConfig(Config):
    """
    Development configuration
    """
    DEBUG = True


class ProductionConfig(Config):
    """
    Development configuration
    """
    SECRET_KEY = '\x94\xb2\xf2</6\xd7+Op\xc5\x97v)\x83\xda\xff)\xd0UD\xd4NB'