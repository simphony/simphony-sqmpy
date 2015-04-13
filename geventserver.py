#from gevent import monkey; monkey.patch_all()
from gevent.wsgi import WSGIServer
from sqmpy import create_app

app = create_app('../config.py')
http_server = WSGIServer(('localhost', 5000), app)
http_server.serve_forever()
