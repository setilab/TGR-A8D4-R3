#!/usr/bin/env python

import json
import redis
import requests
import cherrypy
from defines import *


# /api/alarm

@cherrypy.expose
class Alarm(object):

    def __init__(self):
        self.silence = Silence()
        self.sound = Sound()
        self.sources = Sources()

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("alarm.state"):
            raise cherrypy.HTTPError(502, "Missing datastore key.")
            return

        alarm = ks.hgetall("alarm.state")

        result = {'data':alarm}
        return result


# /api/alarm/silence

@cherrypy.expose
class Silence(object):

    @cherrypy.tools.json_out()
    def PUT(self):

        try:
            response = requests.post(
                OCMEP + "/alarm",
                data="name=sound&setting=off"
            )
            if response.ok:
                ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
                ks.set("alarm.state.silence", "yes")
                ks.expire("alarm.state.silence", 300)
                ks.hset("alarm.state", mapping={'silence':'yes'})
                cherrypy.response.status = 202
                return
            else:
                raise cherrypy.HTTPError(502, "HTTP Error {}".format(response.status_code))
        except:
            raise cherrypy.HTTPError(502, "Unspecified error.")


# /api/alarm/sound

@cherrypy.expose
class Sound(object):

    @cherrypy.tools.json_out()
    def PUT(self, state):

        try:
            response = requests.post(
                OCMEP + "/alarm",
                data="name=sound&setting=" + state
            )
            if response.ok:
                cherrypy.response.status = 202
                return
            else:
                raise cherrypy.HTTPError(502, "HTTP Error {}".format(response.status_code))
        except:
            raise cherrypy.HTTPError(502, "Unspecified error.")


# /api/alarm/sources

@cherrypy.expose
class Sources(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "alarm.source."

        alarms = list()
        alarmKeys = ks.keys(keyNs + "*")
        for keyName in alarmKeys:
            alarm = keyName.split(keyNs)[1]
            state = ks.get(keyName)
            if state == "yes":
                alarms.append(alarm)

        alarms.sort()

        result = {'data':alarms}
        return result

