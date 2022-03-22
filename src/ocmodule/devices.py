#!/usr/bin/env python

import socket
import cherrypy
import json
from defines import *

relays = {
    "acrl1":"off",
    "acrl2":"off",
    "acrl3":"off",
    "acrl4":"off",
    "acrl5":"off",
    "acrl6":"off",
    "acrl7":"off",
    "acrl8":"off",
    "dcrl1":"off",
    "dcrl2":"off",
    "dcrl3":"off",
    "dcrl4":"off"
}

udpRelayPacket = {"system":{"update":{"relay":{"id":"unset","state":"unset"}}}}

@cherrypy.expose
class Relays(object):

    def POST(self, name, state):

        if not name in relays.keys():
            raise cherrypy.HTTPError(400, "Invalid relay name.")
            return

        if not state in [ "on", "off" ]:
            raise cherrypy.HTTPError(400, "Invalid state parameter.")
            return

        relays[name] = state

        udpRelayPacket["system"]["update"]["relay"]["id"] = name
        udpRelayPacket["system"]["update"]["relay"]["state"] = state

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        s.sendto(json.dumps(udpRelayPacket).encode('utf-8'), (ip, port))

        cherrypy.response.status = 202
        return

