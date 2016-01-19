"""
This file contains gunicorn settings.
To run sqmpy with gunicorn run the following command:

    gunicorn -c gunicorn_cfg.py run:app

In order to daemonize gunicorn add -D flag:

    gunicorn -c gunicorn_cfg.py run:app -D

"""
import multiprocessing


# Gunicorn will listen on the given host:port
bind = '0.0.0.0:5000'

# The only tested worker class is gevent
#worker_class = 'gevent'

# Set number of workers based on CPU count
workers = multiprocessing.cpu_count() * 2 + 1

# Uncomment for development
# reload = True

# Daemonize the application
daemon = False

# Comment only for development. Use your own certificates here.
keyfile = 'server.key'
certfile = 'server.crt'

# Application log level
loglevel = 'debug'
