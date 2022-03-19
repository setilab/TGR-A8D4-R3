#!/usr/bin/env python

import cherrypy
import json
import redis
import random
import string
from defines import *


# /api/timers

@cherrypy.expose
class Timers(object):

    def __init__(self):
        self.id = Timer()
        self.properties = TimersProperties()

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "timer.properties."

        timers = {}
        timerKeys = ks.keys(keyNs + "*")
        for keyName in timerKeys:
            timerId = keyName.split(keyNs)[1]
            timerProps = ks.hgetall(keyNs + timerId)
            timers[timerId] = timerProps["name"]

        result = {'data':timers}
        return result

    def DELETE(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "timer.properties."

        timerKeys = ks.keys(keyNs + "*")
        for keyName in timerKeys:
            ks.delete(keyName)

        cherrypy.response.status = 202
        return

    @cherrypy.tools.json_in()
    def POST(self):

        if not "name" in cherrypy.request.json:
            raise cherrypy.HTTPError(400, "Missing name parameter.")
            return

        if not "devices" in cherrypy.request.json:
            raise cherrypy.HTTPError(400, "Missing devices parameter.")
            return

        if not "hour" in cherrypy.request.json:
            raise cherrypy.HTTPError(400, "Missing hour parameter.")
            return

        if not "min" in cherrypy.request.json:
            raise cherrypy.HTTPError(400, "Missing min parameter.")
            return

        if not "state" in cherrypy.request.json:
            raise cherrypy.HTTPError(400, "Missing state parameter.")
            return

        if "blocking" in cherrypy.request.json:
            blocking = cherrypy.request.json["blocking"]
        else:
            blocking = "when_off"

        name = cherrypy.request.json["name"]
        devices = "{}".format(cherrypy.request.json["devices"])
        hour = cherrypy.request.json["hour"]
        min = cherrypy.request.json["min"]
        state = cherrypy.request.json["state"]

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "timer.properties."

        timerId = ''.join(random.sample(string.hexdigits, 8))

        jsonData = {'name':name,'devices':devices,'hour':hour,'min':min,'state':state,'enabled':'yes','blocking':blocking}

        ks.hset(keyNs + timerId, mapping=jsonData)

        keyNs = "device.timers.id."
        for device in devices.split(","):
            ks.sadd(keyNs + device, timerId)

        cherrypy.response.status = 202
        return


# /api/timers/properties

@cherrypy.expose
class TimersProperties(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "timer.properties."

        timers = {}
        timerKeys = ks.keys(keyNs + "*")
        for keyName in timerKeys:
            timerId = keyName.split(keyNs)[1]
            timerProps = ks.hgetall(keyNs + timerId)
            timers[timerId] = timerProps

        result = {'data':timers}
        return result


# /api/timers/id/{timer}

@cherrypy.expose
@cherrypy.popargs('timer')
class Timer(object):

    @cherrypy.tools.json_out()
    def GET(self, timer):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        key = "timer.properties." + timer

        if ks.exists(key):
            timerProps = ks.hgetall(key)
        else:
            raise cherrypy.HTTPError(404)
            return

        result = {'data':timerProps}
        return result

    @cherrypy.tools.json_out()
    def DELETE(self, timer):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        key = "timer.properties." + timer

        if ks.exists(key):
            timerProps = ks.hgetall(key)
            for device in timerProps["devices"].split(","):
                k = "device.timers.id." + device
                ks.srem(k, timer)
                if ks.scard(k) == 0:
                    ks.delete(k)
            ks.delete(key)
        else:
            raise cherrypy.HTTPError(404)
            return

        cherrypy.response.status = 202
        return

    @cherrypy.tools.json_in()
    def PUT(self, timer):

        jsonData = {}
        if "name" in cherrypy.request.json:
            jsonData["name"] = cherrypy.request.json["name"]

        if "devices" in cherrypy.request.json:
            jsonData["devices"] = cherrypy.request.json["devices"]

        if "hour" in cherrypy.request.json:
            jsonData["hour"] = cherrypy.request.json["hour"]

        if "min" in cherrypy.request.json:
            jsonData["min"] = cherrypy.request.json["min"]

        if "state" in cherrypy.request.json:
            jsonData["state"] = cherrypy.request.json["state"]

        if "enabled" in cherrypy.request.json:
            jsonData["enabled"] = cherrypy.request.json["enabled"]

        if "blocking" in cherrypy.request.json:
            jsonData["blocking"] = cherrypy.request.json["blocking"]

        if not jsonData:
            raise cherrypy.HTTPError(400)
            return

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        key = "timer.properties." + timer
        keyNs = "device.timers.id."

        if not ks.exists(key):
            raise cherrypy.HTTPError(404)
            return

        oldProps = ks.hgetall(key)
        ks.hset(key, mapping=jsonData)

        if "devices" in jsonData:
            for device in oldProps["devices"].split(","):
                if not device in jsonData["devices"].split(","):
                    k = "device.timers.id." + device
                    ks.srem(k, timer)
                    if ks.scard(k) == 0:
                        ks.delete(k)

            for device in jsonData["devices"].split(","):
                k = keyNs + device
                if not ks.exists(k) or not timer in ks.smembers(k):
                    ks.sadd(k, timer)

        cherrypy.response.status = 202
        return


