#!/usr/bin/env python

import cherrypy
import json
import redis
import requests
import random
import string
from defines import *

# /api/growroom

@cherrypy.expose
class Growroom(object):

    def __init__(self):
        self.equipment = Equipment()


# /api/growroom/equipment

@cherrypy.expose
class Equipment(object):

    def __init__(self):
        self.id = EquipID()

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "growroom.equipment.id."
        equipment = {}
        equipKeys = ks.keys(keyNs + "*")
        for key in equipKeys:
            equipId = key.split(keyNs)[1]
            equipProps = ks.hgetall(keyNs + equipId)
            equipment[equipId] = equipProps["name"]

        result = {'data':equipment}
        return result

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):

        try:
            name = cherrypy.request.json["name"]
        except:
            raise cherrypy.HTTPError(400, "Invalid or missing 'name' parameter.")
            return

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "growroom.equipment.id."
        equipment = {}
        equipKeys = ks.keys(keyNs + "*")
        for key in equipKeys:
            equipId = key.split(keyNs)[1]
            equipProps = ks.hgetall(keyNs + equipId)
            if equipProps["name"] == name:
                raise cherrypy.HTTPError(409, "Name {} already exists.".format(name))
                return

        equipId = ''.join(random.sample(string.hexdigits, 8))
        equipProps = cherrypy.request.json

        ks.hset(keyNs + equipId, mapping=equipProps)

        return {'data':{'id':equipId}}


# /api/growroom/equipment/id/{equipid}

@cherrypy.expose
@cherrypy.popargs('equipid')
class EquipID(object):

    @cherrypy.tools.json_out()
    def DELETE(self, equipid):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "growroom.equipment.id."

        if not ks.exists(keyNs + equipid):
            raise cherrypy.HTTPError(404)
            return

        ks.delete(keyNs + equipid)

        cherrypy.response.status = 202
        return

    @cherrypy.tools.json_out()
    def GET(self, equipid):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "growroom.equipment.id."

        if not ks.exists(keyNs + equipid):
            raise cherrypy.HTTPError(404)
            return

        equipProps = ks.hgetall(keyNs + equipid)

        return {'data':equipProps}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, equipid):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "growroom.equipment.id."

        if not ks.exists(keyNs + equipid):
            raise cherrypy.HTTPError(404)
            return

        ks.hset(keyNs + equipid, mapping=cherrypy.request.json)

        cherrypy.response.status = 202
        return


