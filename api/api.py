#!/usr/bin/env python

import cherrypy
from defines import *
from alarm import *
from camera import *
from devices import *
from grows import *
from growroom import *
from images import *
from notes import *
from presets import *
from sensors import *
from settings import *
from system import *
from tasks import *
from timers import *
from weather import *
from wls import *


@cherrypy.expose
class API(object):
    def __init__(self):
        self.alarm = Alarm()
        self.camera = Camera()
        self.devices = Devices()
        self.growing = Growing()
        self.grow = Grow()
        self.growroom = Growroom()
        self.images = Images()
        self.notes = Notes()
        self.presets = Presets()
        self.sensors = Sensors()
        self.settings = Settings()
        self.system = System()
        self.tasks = Tasks()
        self.timers = Timers()
        self.weather = Weather()
        self.wls = WLSensors()

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


