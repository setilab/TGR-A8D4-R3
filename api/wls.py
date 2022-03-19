#!/usr/bin/env python

import cherrypy
import json
import redis
from defines import *


# /api/wls

@cherrypy.expose
class WLSensors(object):

    def __init__(self):
        self.id = WLSensor()

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)

        keyNs = "wls.id."
        keys = ks.keys(keyNs + "*")

        wlss = {}
        for key in keys:
            wlsid = key.split(keyNs)[1]
            wlss[wlsid] = ks.hgetall(key)["name"]

        result = {'data':wlss}
        return result

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):

        params = [ "id","ip","mac","name","capability" ]
 
        for atr in cherrypy.request.json:
            if not atr in params:
                raise cherrypy.HTTPError(400)
                return

        for atr in params:
            if not atr in cherrypy.request.json:
                raise cherrypy.HTTPError(400)
                return

        ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)

        keyNs = "wls.id."

        if ks.exists(keyNs + cherrypy.request.json["id"]):
            raise cherrypy.HTTPError(409, "Device already exists.")
            return

        properties = cherrypy.request.json
        id = properties["id"]
        del properties["id"]

        key = keyNs + id
        ks.hset(key, mapping=properties)

        cherrypy.response.status = 202
        return


# /api/wls/id/{wlsid}

@cherrypy.expose
@cherrypy.popargs('wlsid')
class WLSensor(object):

    @cherrypy.tools.json_out()
    def GET(self, wlsid):

        ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)

        keyNs = "wls.id."
        if not ks.exists(keyNs + wlsid):
            raise cherrypy.HTTPError(404)
            return

        props = ks.hgetall(keyNs + wlsid)
        return {'data':props}

    @cherrypy.tools.json_out()
    def DELETE(self, wlsid):

        ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)

        keyNs = "wls.id."
        if not ks.exists(keyNs + wlsid):
            raise cherrypy.HTTPError(404)
            return

        ks.delete(keyNs + wlsid)

        cherrypy.response.status = 202
        return

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, wlsid):

        ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)

        keyNs = "wls.id."
        key = keyNs + wlsid

        if not ks.exists(keyNs + wlsid):
            raise cherrypy.HTTPError(404)
            return

        ks.hset(key, mapping=cherrypy.request.json)

        cherrypy.response.status = 202
        return


