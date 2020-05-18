#!/usr/env/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import tornado
import asyncio
import json
import websockets

from tornado.web import StaticFileHandler, RequestHandler, Application as TornadoApplication
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
from os.path import dirname, join as join_path

connectedClients = []
jsonDataBuffer = "" # Buffer s daty, když se připojí nový klient

async def broadcast(message):
    print("Broadcasting to "+str(len(connectedClients))+" clients")
    for ws in connectedClients:
        await ws.write_message("statistics "+message)
    print("Finished broadcasting to clients\n")

class MainHandler(RequestHandler):
    
    @tornado.gen.coroutine
    def get(self):
        self.render('./templates/index.html')

class MainWebSocketHandler(WebSocketHandler):

    @tornado.gen.coroutine
    def check_origin(self, origin):
        return True

    @tornado.gen.coroutine
    def open(self):
        print("===========Tornado===========")
        connectedClients.append(self)
        print("WebSocket opened")

    async def on_message(self, message):
        print("===========Tornado===========")
        print("Message received: "+message[:9])
        global jsonDataBuffer

        if message[:9] == "broadcast":
            jsonDataBuffer = message[10:]
            await broadcast(jsonDataBuffer)
        elif message == "request":
            self.write_message("statistics "+jsonDataBuffer)
            print("Request answered")

    @tornado.gen.coroutine
    def on_close(self):
        print("===========Tornado===========")
        connectedClients.remove(self)
        print("WebSocket closed\n")

if __name__ == '__main__':
    try:
        with open("./assets/data.json", 'r') as f:
            data = json.load(f)
            jsonDataBuffer = json.dumps(data)
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
