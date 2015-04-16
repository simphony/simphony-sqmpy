from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from sqmpy import create_app

http_server = HTTPServer(WSGIContainer(create_app('../config.py')))
http_server.listen(3000)
IOLoop.instance().start()
