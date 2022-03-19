#!/usr/bin/env python

from datetime import date,datetime,timedelta
import cherrypy
import json
import redis
import requests
from defines import *


# /api/sensors

@cherrypy.expose
class Sensors(object):

    def __init__(self):
        self.properties = Properties()
        self.ph = PHSensor()

    @cherrypy.tools.json_out()
    def GET(self):

        try:
            ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
        except:
            raise cherrypy.HTTPError(502, "Unable to connect to Redis service.")
            return

        if not ks.exists("sensor.data.internal"):
            raise cherrypy.HTTPError(502, "Missing datastore key.")
            return

        if not ks.exists("sensor.data.external"):
            raise cherrypy.HTTPError(502, "Missing datastore key.")
            return

        if not ks.exists("sensor.data.hydroponic"):
            raise cherrypy.HTTPError(502, "Missing datastore key.")
            return

        if not ks.exists("sensor.module.unit"):
            raise cherrypy.HTTPError(502, "Missing datastore key.")
            return

        intSensorVals = ks.hgetall("sensor.data.internal")
        extSensorVals = ks.hgetall("sensor.data.external")
        hydroSensorVals = ks.hgetall("sensor.data.hydroponic")
        unitStandard = ks.get("sensor.module.unit")
        sensorUnits = ks.hgetall("sensor.module.unit." + unitStandard)

        intemp = intSensorVals["temp"]
        inrh = intSensorVals["humidity"]
        extemp = extSensorVals["temp"]
        exrh = extSensorVals["humidity"]
        pres = extSensorVals["pressure"]
        esp = extSensorVals["esp"]
        dp = extSensorVals["dewpoint"]
        co2 = extSensorVals["co2"]
        lux = extSensorVals["lux"]
        wt = hydroSensorVals["temp"]
        ph = hydroSensorVals["ph"]

        data = {'internal':{'temp':intemp,'humidity':inrh},
                'external':{'temp':extemp,'humidity':exrh,
                            'dewpoint':dp,'pressure':pres,'esp':esp,
                            'co2':co2,'lux':lux},
              'hydroponic':{'temp':wt,'ph':ph},
                   'units':{'temp':sensorUnits["temp"],
                            'humidity':sensorUnits["humidity"],
                            'pressure':'Pa',
                            'esp':'Pa',
                            'dewpoint':sensorUnits["dewpoint"],
                            'co2':sensorUnits["co2"],
                            'lux':sensorUnits["lux"]}}

        result = {'data':data}
        return result


# /api/sensors/properties

@cherrypy.expose
class Properties(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "sensor.module.sensor."

        sensors = {}
        sensorKeys = ks.keys(keyNs + "*")
        for keyName in sensorKeys:
            sensorId = keyName.split(keyNs)[1]
            sensorProps = ks.hgetall(keyName)
            sensors[sensorId] = sensorProps

        result = {'data':sensors}
        return result


# /api/sensors/ph

@cherrypy.expose
class PHSensor(object):

    def __init__(self):
        self.calibration = PHCalibration()


# /api/sensors/ph

@cherrypy.expose
class PHCalibration(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "sensor.module.sensor."

        props = {}
        sensorKeys = ks.keys(keyNs + "*")
        for keyName in sensorKeys:
            sensorProps = ks.hgetall(keyName)
            if sensorProps["capability"] == "ph":
                if "last_calibration" in sensorProps:
                    props["last_calibration"] = sensorProps["last_calibration"]
                else:
                    props["last_calibration"] = "unknown"

                if "next_calibration" in sensorProps:
                    props["next_calibration"] = sensorProps["next_calibration"]
                else:
                    props["next_calibration"] = "unknown"

                return {'data':props}

        return {}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyName = "sensor.ph.calibration"

        modes = ["enter", "calibrate", "exit"]
        if not "mode" in cherrypy.request.json and not cherrypy.request.json["mode"] in modes:
            raise cherrypyHTTPError(400)
            return
        else:
            mode = cherrypy.request.json["mode"]

        ks.set(keyName, mode)

        if mode == "enter":
            return {'message':'Insert probe into standard buffer solution.'}
        elif mode == "calibrate":
            return {'message':'Wait for probe values to stabilize.'}
        elif mode == "exit":
            keyNs = "sensor.module.sensor."

            props = {}
            sensorKeys = ks.keys(keyNs + "*")
            for keyName in sensorKeys:
                sensorProps = ks.hgetall(keyName)
                if sensorProps["capability"] == "ph":
                    props["last_calibration"] = "{}".format(date.today())
                    props["next_calibration"] = "{}".format(date.today() + timedelta(days=30))
                    ks.hset(keyName, mapping=props)

            return {'message':'Return probe back in service.'}


