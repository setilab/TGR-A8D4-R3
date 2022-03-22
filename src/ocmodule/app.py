#!/usr/bin/env python

import cherrypy
from defines import *
from devices import *

@cherrypy.expose
class API(object):
    def __init__(self):
        self.relays = Relays()

    def GET(self):
        return f"TGR Output Control Module {VERSION}"


if __name__ == '__main__':

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


