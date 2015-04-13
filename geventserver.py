from gevent.wsgi import WSGIServer
from sqmpy.factory import create_app

app = create_app('../config.py')
http_server = WSGIServer(('localhost', 5000), app)
http_server.serve_forever()
