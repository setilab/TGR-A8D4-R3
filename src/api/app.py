#!/usr/bin/env python

import cherrypy
from defines import *
from devices import *
from sensors import *
from settings import *
from system import *
from timers import *


@cherrypy.expose
class API(object):
    def __init__(self):
        self.devices = Devices()
        self.sensors = Sensors()
        self.settings = Settings()
        self.system = System()
        self.timers = Timers()

    def GET(self):
        return "TGR API Gateway"


if __name__ == '__main__':

    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 8080,
                           })

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'request.show_tracebacks': False,
            'tools.encode.on': True,
            'tools.encode.encoding': 'utf-8',
            'tools.encode.text_only': False,
            'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')],
        }
    }
    cherrypy.quickstart(API(), '/api', conf)


