#!/usr/env/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import tornado
import asyncio
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from tornado.web import StaticFileHandler, RequestHandler, Application as TornadoApplication
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
from os.path import dirname, join as join_path

live_web_sockets = []
jsonDataBuffer = ""

async def send_messages(message):
    print("Broadcasting to "+str(len(live_web_sockets))+" clients")
    for ws in live_web_sockets:
        await ws.write_message(message)
    print("Finished broadcasting clients")

class MainHandler(RequestHandler):
    
    @tornado.gen.coroutine
    def get(self):
        self.render('./templates/index.html')

class MainWebSocketHandler(WebSocketHandler):

    @tornado.gen.coroutine
    def open(self):
        live_web_sockets.append(self)
        print("WebSocket opened")
        global jsonDataBuffer
        self.write_message(jsonDataBuffer)
        print("Data sent: "+jsonDataBuffer)

    async def on_message(self, message):
        print("Data received "+message)
        global jsonDataBuffer 
        jsonDataBuffer = message
        await send_messages(jsonDataBuffer)
        print("Data broadcasted: "+jsonDataBuffer)

    @tornado.gen.coroutine
    def on_close(self):
        live_web_sockets.remove(self)
        print("WebSocket closed")

if __name__ == '__main__':
    try:
        with open("./assets/data.json", 'r') as f:
            data = json.load(f)
            jsonDataBuffer = json.dumps(data, separators=(',', ':'))
    except:
        print("Could not find json file at server startup")
    
    # Handlers (access points)
    app = TornadoApplication([
        (r'/', MainHandler),
        (r'/websocket', MainWebSocketHandler),
        (r'/(.*)', StaticFileHandler, {
            'path': join_path(dirname(__file__), 'assets')}),
    ])

    # Port
    TORNADO_PORT = 8881
    app.listen(TORNADO_PORT)

    # Start the server
    IOLoop.current().start()
