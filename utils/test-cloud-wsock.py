#!/usr/bin/env python

import websocket
import requests

ws_url = "ws://cloud.thegreenroom.io:32003/controller/810f6d57-f45c-4377-92af-38cebb91b254/ws"
ws_request_url = "http://cloud.thegreenroom.io:32001/v1/controllers/id/810f6d57-f45c-4377-92af-38cebb91b254?websocket=open"

def ws_message(ws, message):
    print("websocket message: {}".format(message))


def ws_error(ws, error):
    print("websocket error: {}".format(error))


def ws_close(ws):
    print("websocket closed.")


def ws_open(ws):
    print("websocket opened...")


#response = requests.get(ws_request_url)

#if not response.ok:
#    print("Unable to request websocket.")
#    exit()

ws = websocket.WebSocketApp(ws_url,
                            on_message = ws_message,
                            on_error = ws_error,
                            on_close = ws_close)
ws.on_open = ws_open
ws.run_forever()


