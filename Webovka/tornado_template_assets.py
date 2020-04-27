#!/usr/env/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from tornado.web import StaticFileHandler, Application as TornadoApplication
import tornado.ioloop
from os.path import dirname, join as join_path


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.render('./templates/index.html')


if __name__ == '__main__':
    
    # Handlers (access points)
    app = TornadoApplication([
        (r'/', MainHandler),
        (r'/(.*)', StaticFileHandler, {
            'path': join_path(dirname(__file__), 'assets')}),
    ])
    
    # Port
    TORNADO_PORT = 8881
    app.listen(TORNADO_PORT)
    
    # Start the server
    tornado.ioloop.IOLoop.current().start()
