from gevent.wsgi import WSGIServer
from sqmpy.factory import create_app

app = create_app('../config.py')
http_server = WSGIServer(('127.0.0.1', 5000), app)
http_server.serve_forever()
