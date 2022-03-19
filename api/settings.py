#!/usr/bin/env python

import subprocess
import cherrypy
import json
import redis
import requests
from defines import *

def convert_f(f):
	c = (int(f) - 32) * 5.0/9.0
	return int(c)

def convert_c(c):
	f = (9.0/5.0 * int(c)) + 32
	return int(f + 0.5)

# /api/settings

@cherrypy.expose
class Settings(object):

    def __init__(self):
        self.alarm = AlmSetting()
        self.controller = ControllerSettings()
        self.environmental = EnvSetting()
        self.manual = ManualSetting()
        self.defaults = DefaultSettings()

    @cherrypy.tools.json_out()
    def GET(self):

        try:
            ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
        except:
            raise cherrypy.HTTPError(502, "Unable to connect to Redis service.")
            return

        env = ks.hgetall("settings.environmental")
        alarm = ks.hgetall("settings.alarm")
        controller = ks.hgetall("settings.controller")
        unit = ks.get("sensor.module.unit")
        controller["unit_standard"] = unit
        units = ks.hgetall("sensor.module.unit." + unit)
        controller["sensor_units"] = units
        data = {'environmental':env,'alarm':alarm,'controller':controller}

        result = {'data': data}
        return result


# /api/settings/manual

@cherrypy.expose
class ManualSetting(object):

    @cherrypy.tools.json_out()
    def GET(self):

        try:
            ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
        except:
            raise cherrypy.HTTPError(502, "Unable to connect to Redis service.")
            return

        if ks.exists("settings.controller"):
            manual = ks.hgetall("settings.controller")["manual"]

            result = {'data':{'manual':manual}}
            return result
        else:
            raise cherrypy.HTTPError(502, "Missing key.")
            return

    @cherrypy.tools.json_out()
    def PUT(self, state):

        if not state in ["on","off"]:
            raise cherrypy.HTTPError(400)
            return

        try:
            ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
        except:
            raise cherrypy.HTTPError(502, "Unable to connect to Redis service.")
            return

        jsonData = {'manual':state}
        ks.hset("settings.controller", mapping=jsonData)

        cherrypy.response.status = 202
        return


# /api/settings/environmental

@cherrypy.expose
class EnvSetting(object):

    @cherrypy.tools.json_out()
    def GET(self):

        try:
            ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
        except:
            raise cherrypy.HTTPError(502, "Unable to connect to Redis service.")
            return

        if not ks.exists("settings.environmental"):
            raise cherrypy.HTTPError(502, "Missing key.")
            return

        env = ks.hgetall("settings.environmental")

        result = {'data':env}
        return result

    @cherrypy.tools.json_in()
    def PUT(self):

        try:
            ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
        except:
            raise cherrypy.HTTPError(502, "Unable to connect to Redis service.")
            return

        if not ks.exists("settings.environmental"):
            raise cherrypy.HTTPError(502, "Missing key.")
            return

        envSettings = ks.hgetall("settings.environmental")
        jsonData = cherrypy.request.json

        for setting in jsonData.keys():
            if not setting in envSettings:
                raise cherrypy.HTTPError(400)
                return

        ks.hset("settings.environmental", mapping=jsonData)

        cherrypy.response.status = 202
        return


# /api/settings/alarm

@cherrypy.expose
class AlmSetting(object):

    @cherrypy.tools.json_out()
    def GET(self):

        try:
            ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
        except:
            raise cherrypy.HTTPError(502, "Unable to connect to Redis service.")
            return

        if not ks.exists("settings.alarm"):
            raise cherrypy.HTTPError(502, "Missing key.")
            return

        env = ks.hgetall("settings.alarm")

        result = {'data':env}
        return result

    @cherrypy.tools.json_in()
    def PUT(self):

        try:
            ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
        except:
            raise cherrypy.HTTPError(502, "Unable to connect to Redis service.")
            return

        if not ks.exists("settings.alarm"):
            raise cherrypy.HTTPError(502, "Missing key.")
            return

        almSettings = ks.hgetall("settings.alarm")
        jsonData = cherrypy.request.json

        for setting in jsonData.keys():
            if not setting in almSettings:
                raise cherrypy.HTTPError(400)
                return

        ks.hset("settings.alarm", mapping=jsonData)

        cherrypy.response.status = 202
        return


# /api/settings/defaults

@cherrypy.expose
class DefaultSettings(object):

    @cherrypy.tools.json_out()
    def GET(self):

        try:
            ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
        except:
            raise cherrypy.HTTPError(502, "Unable to connect to Redis service.")
            return

        env = ks.hgetall("settings.environmental.defaults")
        alarm = ks.hgetall("settings.alarm.defaults")
        controller = ks.hgetall("settings.controller.defaults")
        data = {'environmental':env,'alarm':alarm,'controller':controller}

        result = {'data': data}
        return result

    @cherrypy.tools.json_out()
    def PUT(self):

        try:
            ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
        except:
            raise cherrypy.HTTPError(502, "Unable to connect to Redis service.")
            return

        env = ks.hgetall("settings.environmental.defaults")
        alarm = ks.hgetall("settings.alarm.defaults")
        controller = ks.hgetall("settings.controller.defaults")

        ks.hset("settings.environmental", mapping=env)
        ks.hset("settings.alarm", mapping=alarm)
        ks.hset("settings.controller", mapping=controller)

        cherrypy.response.status = 202
        return


# /api/settings/controller

@cherrypy.expose
class ControllerSettings(object):

    @cherrypy.tools.json_out()
    def GET(self):

        try:
            ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
        except:
            raise cherrypy.HTTPError(502, "Unable to connect to Redis service.")
            return

        if not ks.exists("settings.alarm"):
            raise cherrypy.HTTPError(502, "Missing key.")
            return

        controller = ks.hgetall("settings.controller")
        unit = ks.get("sensor.module.unit")
        controller["unit_standard"] = unit
        units = ks.hgetall("sensor.module.unit." + unit)
        controller["sensor_units"] = units

        result = {'data':controller}
        return result

    @cherrypy.tools.json_in()
    def PUT(self):

        try:
            ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
        except:
            raise cherrypy.HTTPError(502, "Unable to connect to Redis service.")
            return

        if not ks.exists("settings.controller"):
            raise cherrypy.HTTPError(502, "Missing key.")
            return

        controller = ks.hgetall("settings.controller")
        unit = ks.get("sensor.module.unit")
        controller["unit_standard"] = unit

        jsonData = cherrypy.request.json

        for setting in jsonData.keys():
            if not setting in controller:
                raise cherrypy.HTTPError(400)
                return

        if "unit_standard" in jsonData.keys():
            unit = jsonData["unit_standard"]
            if not unit == "us" and not unit == "intl":
                raise cherrypy.HTTPError(400)
                return
            if unit == controller["unit_standard"]:
                raise cherrypy.HTTPError(409)
                return

            env = ks.hgetall("settings.environmental")
            alm = ks.hgetall("settings.alarm")
            newEnv = {}
            newAlm = {}
            if unit == "us":
                for setting in env:
                    newEnv[setting] = "{}".format(convert_c(env[setting]))
                for setting in alm:
                    newAlm[setting] = "{}".format(convert_c(alm[setting]))
            else:
                for setting in env:
                    newEnv[setting] = "{}".format(convert_f(env[setting]))
                for setting in alm:
                    newAlm[setting] = "{}".format(convert_f(alm[setting]))

            ks.hset("settings.environmental", mapping=newEnv)
            ks.hset("settings.alarm", mapping=newAlm)
            ks.set("sensor.module.unit", unit)

            cmd = ['/home/pi/tgr/bin/set_measurement_units', unit]
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            o,e = proc.communicate()

        ks.hset("settings.controller", mapping=jsonData)

        cherrypy.response.status = 202
        return


