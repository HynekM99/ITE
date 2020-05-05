#!/usr/env/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import tornado
import asyncio
import json
import websockets

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from tornado.web import StaticFileHandler, RequestHandler, Application as TornadoApplication
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
from os.path import dirname, join as join_path

live_web_sockets = [] # Všichni klienti
jsonDataBuffer = "" # Buffer s daty, když se připojí nový klient

async def broadcast(message):
    print("Broadcasting to "+str(len(live_web_sockets))+" clients")
    for ws in live_web_sockets:
        await ws.write_message(message)
    print("Finished broadcasting clients\n")

class OnMyWatch:
    watchDirectory = "./assets/"
    observer = Observer()
    
    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.watchDirectory, recursive = True)
        self.observer.start()

class Handler(FileSystemEventHandler):
    sendOnModified = True # Event modifikace souboru se spousti dvakrat

    def on_any_event(self, event):
        if event.src_path != './assets/data.json':
            return None
        print("===========Watchdog===========")
        if event.event_type == 'created':
            print("File was created")
            asyncio.new_event_loop().run_until_complete(self.send_message())
        elif event.event_type == 'modified':
            print("File was modified")
            if self.sendOnModified:
                asyncio.new_event_loop().run_until_complete(self.send_message())
                self.sendOnModified = False
            else:
                self.sendOnModified = True
        print("")
    async def send_message(self):
        address = 'ws://localhost:8881/websocket'
        try:
            async with websockets.connect(address) as ws:
                string = ""
                try:
                    with open("./assets/data.json", 'r') as f:
                        data = json.load(f)
                        string = json.dumps(data, separators=(',', ':'))
                    await ws.send(string)
                    received = await ws.recv()
                    print("Data sent")
                except:
                    print("Could not find data.json file")
        except:
            print("Could not establish connection with address "+address)

class MainHandler(RequestHandler):
    
    @tornado.gen.coroutine
    def get(self):
        self.render('./templates/index.html')

class MainWebSocketHandler(WebSocketHandler):

    @tornado.gen.coroutine
    def open(self):
        print("===========Tornado===========")
        live_web_sockets.append(self)
        print("WebSocket opened")
        global jsonDataBuffer
        self.write_message(jsonDataBuffer)
        print("Data sent\n")

    async def on_message(self, message):
        print("===========Tornado===========")
        print("Data received")
        global jsonDataBuffer
        jsonDataBuffer = message
        await broadcast(jsonDataBuffer)

    @tornado.gen.coroutine
    def on_close(self):
        print("===========Tornado===========")
        live_web_sockets.remove(self)
        print("WebSocket closed\n")

if __name__ == '__main__':
    try:
        with open("./assets/data.json", 'r') as f:
            data = json.load(f)
            jsonDataBuffer = json.dumps(data, separators=(',', ':'))
    except:
        print("Could not find json file at server startup")
    
    watch = OnMyWatch()
    watch.run()
    
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
