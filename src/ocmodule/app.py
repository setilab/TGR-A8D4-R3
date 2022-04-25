#!/usr/bin/env python

"""
Multi-threaded process to emulate an Arduino Mega 2560 Output Control Module

Thread #1 is the API server process that supports REST calls to turn a relay
on/off or set PWM fan speed from 0-255.

Thread #2 simulates the 10s heartbeat message with device states over UDP.

The main process, prior to launching the threads, simulates the boot & config
messages sent by the actual, physical module.

"""

import cherrypy
import socket
import threading
import time
from defines import *
from devices import *

@cherrypy.expose
class API(object):
    def __init__(self):
        self.fans = Fans()
        self.relays = Relays()

    def GET(self):
        return f"TGR Output Control Module {VERSION}"


def apiServer():

    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 80,
                           })

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'request.show_tracebacks': False,
            'tools.encode.on': True,
            'tools.encode.encoding': 'utf-8',
            'tools.encode.text_only': False,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')],
        }
    }
    cherrypy.quickstart(API(), '/', conf)


def udpHeartbeat():

    udpHeartbeatPacket = {"system":{"heartbeat":{"relays":[],"fans":[]}}}

    while True:
        udpHeartbeatPacket["system"]["heartbeat"]["relays"] = []
        udpHeartbeatPacket["system"]["heartbeat"]["fans"] = []

        for relay in relays:
            udpHeartbeatPacket["system"]["heartbeat"]["relays"].append({"id":relay["id"],"state":relay["state"]})

        for fan in fans:
            udpHeartbeatPacket["system"]["heartbeat"]["fans"].append({"id":fan["id"],"speed":fan["speed"]})

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        s.sendto(json.dumps(udpHeartbeatPacket).encode('utf-8'), (ip, port))

        time.sleep(10)


def udpBootmsg():

    udpBootmsgPacket = {"system":{"boot":{"board":"Arduino Mega 2650","code_version":VERSION}}}

    for i in range(0,3):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        s.sendto(json.dumps(udpBootmsgPacket).encode('utf-8'), (ip, port))
        time.sleep(2)


def udpConfigmsg():

    udpConfigmsgPacket = {"system":{"config":{"relays":[],"fans":[]}}}

    for relay in relays:
        udpConfigmsgPacket["system"]["config"]["relays"].append({"id":relay["id"],"label":relay["label"],"output":relay["output"]})

    for fan in fans:
        udpConfigmsgPacket["system"]["config"]["fans"].append({"id":fan["id"],"label":fan["label"]})

    for i in range(0,3):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        s.sendto(json.dumps(udpConfigmsgPacket).encode('utf-8'), (ip, port))
        time.sleep(2)


if __name__ == '__main__':

    udpBootmsg()
    udpConfigmsg()

    threading.Thread(name="apiServerThread", target=apiServer).start()
    threading.Thread(name="udpHeartbeatThread", target=udpHeartbeat).start()

