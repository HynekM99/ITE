#!/usr/env/python
# -*- coding: utf-8 -*-
from tornado.web import StaticFileHandler, RequestHandler, Application
from tornado.websocket import WebSocketHandler
from os.path import dirname, join as join_path
from tornado.ioloop import IOLoop
from datetime import datetime
from threading import Timer

import websockets
import logging
import tornado
import asyncio
import os.path
import json
import time

logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.basicConfig(
    format='%(asctime)s: [%(levelname)s] - %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S',
    filename='./logs/server-log.log',
    level=logging.WARNING)

STATS_FILE = "./assets/data.json"
TEAM_NAMES = ["black", "blue", "green", "orange", "pink", "red", "yellow"]
dict_previous_time = {}
# Klíč -- název týmu.
# Hodnota -- čas zprávy, která přišla před minutou

connected_clients = set()
server_status_message = "server false"


def check_status(team, last_time):
    ''' Zkontroluje stav senzoru zadaneho tymu.

    Parameters:
        team (string): Nazev tymu
        last_time (string): Cas posledni namerene teploty

    Returns:
        bool: Stav senzoru
    '''
    global dict_previous_time
    previous_time = dict_previous_time[team]
    status = last_time != previous_time
    dict_previous_time[team] = last_time
    return status


def periodic_check():
    '''Pravidelne kontroluje stav senzoru vsech tymu.'''
    global TEAM_NAMES, STATS_FILE
    dict_data = read_from_json(STATS_FILE)

    if dict_data is not None:
        team_statuses = {}
        for team in TEAM_NAMES:
            last_time = dict_data[team]['cas']
            team_status = check_status(team, last_time)

            team_statuses[team] = {}
            team_statuses[team]["online"] = team_status
            dict_data[team]["online"] = team_status

        write_to_file(STATS_FILE, json.dumps(dict_data, indent=4))

        message = "statistics "+json.dumps(team_statuses)
        asyncio.new_event_loop().run_until_complete(
                async_broadcast(message))

    Timer(60.0, periodic_check).start()


def write_to_file(path, data):
    ''' Zapisuje data do souboru.

    Parameters:
        path (string): Cesta k souboru
        data (string): Data, ktera chci zapsat
    '''
    try:
        with open(path, "w+") as f:
            f.write(data)
            f.close()

    except Exception as e:
        logging.exception("Could not write data to file "+path)


def read_from_json(path):
    ''' Cte data ze souboru.

    Parametr:
        path (string): Cesta k souboru
    '''
    data = None
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
            f.close()
    except Exception as e:
        logging.exception("Could not read data from file "+path)

    return data


async def async_broadcast(message):
    '''Asynchronni metoda, slouzici k rozeslani zadane zpravy
    vsem pripojenym klientum.
    
    Parameters:
        message (string): Zprava k rozeslani
    '''

    global connected_clients
    for ws in connected_clients:
        await ws.write_message(message)


class MainHandler(RequestHandler):
    '''Event handler pro HTTP pozadavky.'''

    @tornado.gen.coroutine
    def get(self):
        self.render('./templates/index.html')


class MainWebSocketHandler(WebSocketHandler):
    '''Event handler pro websocket pripojeni'''
    
    @tornado.gen.coroutine
    def check_origin(self, origin):
        return True

    @tornado.gen.coroutine
    def open(self):
        connected_clients.add(self)

    async def on_message(self, message):
        global server_status_message, STATS_FILE
        logging.info('<- '+str(message))
        output = None

        if message[:9] == "broadcast":
            output = "statistics "+message[10:]
            logging.info('-> '+output)
            await async_broadcast(output)

        elif message == "request":
            stats = json.dumps(read_from_json(STATS_FILE), indent=4)
            output = "statistics "+stats
            self.write_message(output)

        elif message[:10] == "req_server":
            output = server_status_message
            self.write_message(output)

        elif message[:6] == "server":
            output = message
            server_status_message = message
            await async_broadcast(output)

        if output is not None:
            logging.info('-> '+output)

    @tornado.gen.coroutine
    def on_close(self):
        connected_clients.remove(self)


if __name__ == '__main__':
    app = Application([
        (r'/', MainHandler),
        (r'/websocket', MainWebSocketHandler),
        (r'/(.*)', StaticFileHandler, {
            'path': join_path(dirname(__file__), 'assets')}),
    ])

    dict_data = read_from_json(STATS_FILE)

    for team in TEAM_NAMES:
        dict_previous_time[team] = dict_data[team]["cas"]

    periodic_check()

    TORNADO_PORT = 8881
    app.listen(TORNADO_PORT)

    IOLoop.current().start()
