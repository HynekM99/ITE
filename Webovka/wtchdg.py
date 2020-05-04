#!/usr/env/python
# -*- coding: utf-8 -*-

import time
import asyncio
import websockets
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class OnMyWatch:
    # Set the directory on watch
    watchDirectory = "./assets/"
    observer = Observer()
    
    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.watchDirectory, recursive = True)
        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()

class Handler(FileSystemEventHandler):
    sendOnModified = True # Event modifikace souboru se spousti dvakrat

    def on_any_event(self, event):
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

    async def send_message(self):
        address = 'ws://localhost:8881/websocket'
        try:
            async with websockets.connect(address) as ws:
                string = ""
                with open("./assets/data.json", 'r') as f:
                    data = json.load(f)
                    string = json.dumps(data, separators=(',', ':'))
                await ws.send(string)
                received = await ws.recv()
                print("Data sent")
        except:
            print("Could not establish connection with address "+address)

if __name__ == '__main__':
    watch = OnMyWatch()
    asyncio.get_event_loop().run_until_complete(watch.run())
