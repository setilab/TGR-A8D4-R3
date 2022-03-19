#!/usr/bin/env python

import cherrypy
import json
import redis
import requests
import random
import string
from defines import *

# /api/presets

@cherrypy.expose
class Presets(object):

    def __init__(self):
        self.id = Preset()

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "preset.id."
        presets = {}
        presetKeys = ks.keys(keyNs + "*")
        for key in presetKeys:
            presetId = key.split(keyNs)[1]
            presetProps = ks.hgetall(keyNs + presetId)
            presets[presetId] = presetProps["name"]

        result = {'data':presets}
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

        keyNs = "preset.id."
        presets = {}
        presetKeys = ks.keys(keyNs + "*")
        for key in presetKeys:
            presetId = key.split(keyNs)[1]
            presetProps = ks.hgetall(keyNs + presetId)
            if presetProps["name"] == name:
                raise cherrypy.HTTPError(409, "Name {} already exists.".format(name))
                return

        presetId = ''.join(random.sample(string.hexdigits, 8))
        filename = presetId + ".conf"
        presetProps = {"name":name,'filename':filename}

        timers = []
        timerKeys = ks.keys("timer.properties.*")
        for key in timerKeys:
            timers.append(ks.hgetall(key))

        preset_file = os.path.normpath(
            os.path.join(PRESET_DIR, filename))

        with open(preset_file, 'w') as out:
            out.write("{\"settings\":{\"environmental\":" + "{},".format(json.dumps(ks.hgetall("settings.environmental"))))
            out.write("\"alarm\":" + "{}".format(json.dumps(ks.hgetall("settings.alarm"))))
            out.write("},\"timers\":" + "{}".format(json.dumps(timers)))
            out.write("}")

        ks.hset(keyNs + presetId, mapping=presetProps)

        result = {'data':{'id':presetId}}
        return result


# /api/presets/id/{preset}

@cherrypy.expose
@cherrypy.popargs('preset')
class Preset(object):

    def __init__(self):
        self.apply = PresetApply()

    @cherrypy.tools.json_out()
    def DELETE(self, preset):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "preset.id."

        if not ks.exists(keyNs + preset):
            raise cherrypy.HTTPError(404)
            return

        presetKeys = ks.keys(keyNs + "*")
        presetProps = ks.hgetall(keyNs + preset)
        filename = PRESET_DIR + presetProps["filename"]

        if os.path.exists(filename):
            os.remove(filename)
        else:
            print("Preset file not found.")
            raise cherrypy.HTTPError(500)
            return

        ks.delete(keyNs + preset)

        cherrypy.response.status = 202
        return

    @cherrypy.tools.json_out()
    def GET(self, preset):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "preset.id."
        print("hello!")

        if not ks.exists(keyNs + preset):
            raise cherrypy.HTTPError(404)
            return

        presetKeys = ks.keys(keyNs + "*")
        presetProps = ks.hgetall(keyNs + preset)
        filename = PRESET_DIR + presetProps["filename"]

        try:
            f = open(filename)
        except:
            print("Unable to open {} for reading.".format(filename))
            raise cherrypy.HTTPError(500)
            return

        presetProps["config"] = json.loads(f.read())

        return {'data':presetProps}


# /api/presets/id/{preset}/apply

@cherrypy.expose
class PresetApply(object):

    @cherrypy.tools.json_out()
    def PUT(self, preset):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "preset.id."

        if not ks.exists(keyNs + preset):
            raise cherrypy.HTTPError(404)
            return

        presetKeys = ks.keys(keyNs + "*")
        presetProps = ks.hgetall(keyNs + preset)
        filename = PRESET_DIR + presetProps["filename"]

        try:
            f = open(filename)
        except:
            print("Unable to open {} for reading.".format(filename))
            raise cherrypy.HTTPError(500)
            return

        presetProps = json.loads(f.read())
        settingsEnv = presetProps["settings"]["environmental"]
        settingsAlm = presetProps["settings"]["alarm"]
        timers      = presetProps["timers"]

        ks.hset("settings.environmental", mapping=settingsEnv)
        ks.hset("settings.alarm", mapping=settingsAlm)

        keyNs = "timer.properties."

        timerKeys = ks.keys(keyNs + "*")
        for key in timerKeys:
            ks.delete(key)

        for timer in timers:
            timerId = ''.join(random.sample(string.hexdigits, 8))
            ks.hset(keyNs + timerId, mapping=timer)

        cherrypy.response.status = 202
        return


