#!/usr/bin/env python

import socket
import cherrypy
import json
from defines import *

udpFanPacket = {"system":{"update":{"fan":{"id":"unset","speed":"unset"}}}}
udpRelayPacket = {"system":{"update":{"relay":{"id":"unset","state":"unset"}}}}

@cherrypy.expose
class Fans(object):

    @cherrypy.tools.json_out()
    def GET(self, name):

        if not name in fanIds:
            raise cherrypy.HTTPError(404, "Fan not found.")
            return

        for fan in fans:
            if fan["id"] == name:
                return fan

    def POST(self, name, speed):

        if not name in fanIds:
            raise cherrypy.HTTPError(400, "Invalid fan name.")
            return

        if not int(speed) in range(0,256):
            raise cherrypy.HTTPError(400, "Invalid speed parameter.")
            return

        for fan in fans:
            if fan["id"] == name:
                fan["speed"] = speed

        udpFanPacket["system"]["update"]["fan"]["id"] = name
        udpFanPacket["system"]["update"]["fan"]["speed"] = speed

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        s.sendto(json.dumps(udpFanPacket).encode('utf-8'), (ip, port))

        cherrypy.response.status = 202
        return


@cherrypy.expose
class Relays(object):

    @cherrypy.tools.json_out()
    def GET(self, name):

        if not name in relayIds:
            raise cherrypy.HTTPError(404, "Relay not found.")
            return

        for relay in relays:
            if relay["id"] == name:
                return relay

    def POST(self, name, state):

        if not name in relayIds:
            raise cherrypy.HTTPError(400, "Invalid relay name.")
            return

        if not state in [ "on", "off" ]:
            raise cherrypy.HTTPError(400, "Invalid state parameter.")
            return

        for relay in relays:
            if relay["id"] == name:
                relay["state"] = state

        udpRelayPacket["system"]["update"]["relay"]["id"] = name
        udpRelayPacket["system"]["update"]["relay"]["state"] = state

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        s.sendto(json.dumps(udpRelayPacket).encode('utf-8'), (ip, port))

        cherrypy.response.status = 202
        return

