#!/usr/bin/env python

import cherrypy
import json
import redis
import requests
import subprocess
import threading
import time
from datetime import datetime,timedelta
from defines import *

thread_pool = threading.BoundedSemaphore(value=1)
retries = 3

# /api/devices

@cherrypy.expose
class Devices(object):

    def __init__(self):
        self.id = Device()
        self.names = AllDeviceNames()
        self.properties = AllDeviceProperties()
        self.states = AllDeviceStates()
        self.types = DeviceTypes()
        self.icons = DeviceIcons()

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "device.id."

        deviceIds = list()
        deviceKeys = ks.keys(keyNs + "*")
        for keyName in deviceKeys:
            deviceId = keyName.split(keyNs)[1]
            deviceIds.append(deviceId)

        deviceIds.sort()
        return {'data': deviceIds}


# /api/devices/names

@cherrypy.expose
class AllDeviceNames(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "device.id."

        deviceIds = list()
        deviceKeys = ks.keys(keyNs + "*")
        for keyName in deviceKeys:
            deviceId = keyName.split(keyNs)[1]
            deviceIds.append(deviceId)

        deviceIds.sort()

        deviceNames = {}
        for deviceId in deviceIds:
            deviceProps = ks.hgetall(keyNs + deviceId)
            deviceNames[deviceId] = deviceProps["name"]

        result = {'data': deviceNames}
        return result


# /api/devices/properties

@cherrypy.expose
class AllDeviceProperties(object):

    @cherrypy.tools.json_out()
    def GET(self, property="", value=""):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "device.id."

        devicesDict = {}
        devicesList = []
        deviceKeys = ks.keys(keyNs + "*")
        for keyName in deviceKeys:
            deviceId = keyName.split(keyNs)[1]
            deviceProps = ks.hgetall(keyNs + deviceId)
            if len(property) > 0 and property in deviceProps and len(value) > 0 and value == deviceProps[property]:
                devicesList.append(deviceId)
            elif len(property) > 0 and property in deviceProps and len(value) == 0:
                devicesDict[deviceId] = deviceProps[property]
            elif len(property) == 0:
                del deviceProps["id"]
                if not "state" in deviceProps and "relay_state" in deviceProps:
                    rs = deviceProps["relay_state"]
                    if rs == "1":
                        state = "on"
                    else:
                        state = "off"
                    deviceProps["state"] = state
                    del deviceProps["relay_state"]
                timedBy = []
                if ks.exists("device.timers.id." + deviceId):
                    timers = ks.smembers("device.timers.id." + deviceId)
                    for t in timers:
                        timedBy.append(t)
                    deviceProps["timed"] = "yes"
                else:
                    deviceProps["timed"] = "no"
                deviceProps["timed_by"] = timedBy
                devicesDict[deviceId] = deviceProps

        if devicesDict:
            result = {'data':devicesDict}
        else:
            result = {'data':devicesList}

        return result


# /api/devices/states

@cherrypy.expose
class AllDeviceStates(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        deviceStates = ks.hgetall("device.states")

        result = {'data': deviceStates}
        return result

    @cherrypy.tools.json_in()
    def POST(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if "mode" in cherrypy.request.json:
            mode = cherrypy.request.json["mode"]
            if mode == "auto" or mode == "manual":
                setAllDeviceProps(ks, 'mode', mode)
            else:
                raise cherrypy.HTTPError(400)

        if "state" in cherrypy.request.json:
            state = cherrypy.request.json["state"]
            if state == "on" or state == "off":
                setAllDeviceStates(ks, state)
                return
            else:
                raise cherrypy.HTTPError(400)

        raise cherrypy.HTTPError(400)
        return


# /api/devices/id/{device}

@cherrypy.expose
@cherrypy.popargs('device')
class Device(object):

    def __init__(self):
        self.timers = DeviceTimers()

    @cherrypy.tools.json_out()
    def GET(self, device):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        key = "device.id." + device
        if not ks.exists(key):
            raise cherrypy.HTTPError(404)
            return

        deviceProps = ks.hgetall(key)
        del deviceProps["id"]
        if not "state" in deviceProps and "relay_state" in deviceProps:
            rs = deviceProps["relay_state"]
            if rs == "1":
                state = "on"
            else:
                state = "off"
            deviceProps["state"] = state
            del deviceProps["relay_state"]
        timedBy = []
        if ks.exists("device.timers.id." + device):
            timers = ks.smembers("device.timers.id." + device)
            for t in timers:
                timedBy.append(t)
            deviceProps["timed"] = "yes"
        else:
            deviceProps["timed"] = "no"
        deviceProps["timed_by"] = timedBy

        return {'data': deviceProps}

    @cherrypy.tools.json_in()
    def POST(self, device):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        key = "device.id." + device
        if not ks.exists(key):
            raise cherrypy.HTTPError(404)
            return

        if not "state" in cherrypy.request.json and not "speed" in cherrypy.request.json:
            raise cherrypy.HTTPError(400)
            return

        deviceProps = ks.hgetall(key)
        if deviceProps["online"] == "no":
            raise cherrypy.HTTPError(503)
            return

        if not "module" in deviceProps:
            print("ERROR: Missing 'module' property for device {}".format(device))
            raise cherrypy.HTTPError(500)
            return

        setProps = False
        props = {}

        if "mode" in cherrypy.request.json:
            mode = cherrypy.request.json["mode"]
            if mode == "auto" or mode == "manual":
                setProps = True
                props["mode"] = mode
            else:
                raise cherrypy.HTTPError(400)

        if "automation" in cherrypy.request.json:
            auto = cherrypy.request.json["automation"]
            if auto == "enabled" or auto == "disabled":
                setProps = True
                props["automation"] = auto
            else:
                raise cherrypy.HTTPError(400)

        if "speed_max" in cherrypy.request.json:
            speed_max = cherrypy.request.json["speed_max"]
            if int(speed_max) >= 0 and int(speed_max) < 255:
                setProps = True
                props["speed_max"] = speed_max
                deviceProps["speed_max"] = speed_max
            else:
                raise cherrypy.HTTPError(400)

        if "state" in cherrypy.request.json:
            state = cherrypy.request.json["state"]
            if state == "on" and deviceProps["control"] == "pwm":
                state = deviceProps["speed_max"]
            elif state == "off" and deviceProps["control"] == "pwm":
                state = 255
        elif "speed" in cherrypy.request.json:
            speed = cherrypy.request.json["speed"]
            if int(speed) >= 0 and int(speed) <= 255:
                state = cherrypy.request.json["speed"]
            else:
                raise cherrypy.HTTPError(400)
        else:
            raise cherrypy.HTTPError(400)

        threading.Thread(name="t-"+device, target=setDeviceState, args=(device,state)).start()

        if setProps == True:
            setDeviceProps(ks, device, props)

        cherrypy.response.status = 202
        return

    @cherrypy.tools.json_in()
    def PUT(self, device):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        key = "device.id." + device
        if not ks.exists(key):
            raise cherrypy.HTTPError(404)
            return

        setProps = False
        props = {}

        if "state" in cherrypy.request.json:
            state = cherrypy.request.json["state"]
            if state == "on" or state == "off":
                setProps = True
                props["state"] = state
            else:
                raise cherrypy.HTTPError(400)

        if "speed" in cherrypy.request.json:
            speed = int(cherrypy.request.json["speed"])
            if speed >= 0 and speed <= 255:
                setProps = True
                props["speed"] = state
            else:
                raise cherrypy.HTTPError(400)

        if "speed_max" in cherrypy.request.json and not cherrypy.request.json["speed_max"] == None:
            speed_max = int(cherrypy.request.json["speed_max"])
            if speed_max >= 0 and speed_max <= 255:
                setProps = True
                props["speed_max"] = speed_max
            else:
                raise cherrypy.HTTPError(400)

        if "mode" in cherrypy.request.json:
            mode = cherrypy.request.json["mode"]
            if mode == "auto" or mode == "manual":
                setProps = True
                props["mode"] = mode
            else:
                raise cherrypy.HTTPError(400)

        if "automation" in cherrypy.request.json:
            auto = cherrypy.request.json["automation"]
            if auto == "enabled" or auto == "disabled":
                setProps = True
                props["automation"] = auto
            else:
                raise cherrypy.HTTPError(400)

        if "type" in cherrypy.request.json:
            type = cherrypy.request.json["type"]
            if not type in ks.smembers("device.relay.types") and not type in ks.smembers("device.pwm.types"):
                raise cherrypy.HTTPError(400)
            else:
                setProps = True
                props["type"] = type
                if type in [ "phup", "phdown", "peristaltic" ]:
                    props["on_seconds"] = "1"
                    props["automation_delay"] = "900"

        if "name" in cherrypy.request.json:
            setProps = True
            props["name"] = cherrypy.request.json["name"]

        if "lastseen" in cherrypy.request.json:
            setProps = True
            props["lastseen"] = cherrypy.request.json["lastseen"]

        if "icon" in cherrypy.request.json:
            setProps = True
            props["icon"] = cherrypy.request.json["icon"]

        if "on_seconds" in cherrypy.request.json:
            setProps = True
            props["on_seconds"] = cherrypy.request.json["on_seconds"]

        if "automation_delay" in cherrypy.request.json:
            setProps = True
            props["automation_delay"] = cherrypy.request.json["automation_delay"]

        if setProps == True:
            setDeviceProps(ks, device, props)

        cherrypy.response.status = 202
        return


# /api/devices/id/{device}/timers

@cherrypy.expose
class DeviceTimers(object):

    @cherrypy.tools.json_out()
    def DELETE(self, device):

        cherrypy.response.status = 501
        return

    @cherrypy.tools.json_out()
    def GET(self, device):

        cherrypy.response.status = 501
        return

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, device):

        cherrypy.response.status = 501
        return


def setAllDeviceProps(ks, name, value):

    keyNs = "device.id."
    deviceKeys = ks.keys(keyNs + "*")

    for keyName in deviceKeys:
        ks.hset(keyName, mapping={name:value})

    return


def setDeviceProps(ks, device, props):

    if "state" in props or "speed" in props:
        if "state" in props:
            value = props["state"]
        else:
            value = props["speed"]
            if int(value) == 255:
                value = "off"
            elif int(value) < 255:
                value = "on"

            props["state"] = value

        key = "device.state.id." + device
        ks.set(key, value)
        ks.expire(key, STATE_KEY_EXPIRE)
        ks.hset("device.states", mapping={device:value})

    key = "device.id." + device
    ks.hset(key, mapping=props)

    return


def setAllDeviceStates(ks, state):

    keyNs = "device.id."
    deviceKeys = ks.keys(keyNs + "*")

    for key in deviceKeys:
        deviceId = key.split(keyNs)[1]
        deviceProps = ks.hgetall(key)
        if deviceProps["control"] == "pwm" and state == "on":
            _state = deviceProps["speed_max"]
        elif deviceProps["control"] == "pwm" and state == "off":
            _state = 255
        else:
            _state = state

        threading.Thread(name="t-"+deviceId, target=setDeviceState, args=(device,_state)).start()
        

def setDeviceState(device, state):

    with thread_pool:

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        key = "device.id." + device
        deviceProps = ks.hgetall(key)

        if deviceProps["module"] == "ocmodule":

            if deviceProps["control"] == "pwm":
                prop = "speed"
                url = "/fans"
            else:
                prop = "state"
                url = "/relays"

            data = "name={}&{}={}".format(device, prop, state)
            data = {"name":device,prop:state}

            try:
                response = requests.post(OCMEP + url, data=data)
            except:
                print("WARN: Unable to connect to {}".format(OCMEP))
                return
            else:
                if response.ok:
                    if prop == "speed" and int(state) == 255:
                        speed = state
                        state = "off"
                        mapping = {'state':state,'speed':speed}
                    elif prop == "speed" and int(state) < 255:
                        speed = state
                        state = "on"
                        mapping = {'state':state,'speed':speed}
                    else:
                        mapping = {'state':state}
                    key = "device.state.id." + device
                    ks.set(key, state)
                    ks.expire(key, STATE_KEY_EXPIRE)
                    ks.hset("device.id." + device, mapping=mapping)
                    ks.hset("device.states", mapping={device:state})
                else:
                    print(f"{OCMEP}{url} : {data}")
                    print(response.status_code)
                    print("WARN: Error response from ocmodule.")
                    return

        else:
            print("ERROR: Invalid 'module' key for device {}".format(device))
            return

        if deviceProps["type"] == "lamp" and state == "on":
            ks.hset("device.id." + device, mapping={'last_on':"{}".format(datetime.now().isoformat(timespec='seconds'))})

        elif deviceProps["type"] == "lamp" and state == "off":
            if "last_on" in deviceProps:
                last_on = datetime.fromisoformat(deviceProps["last_on"])
                last_off = datetime.now()
                elapsed = last_off - last_on
                secs = elapsed.total_seconds()
                if "usage" in deviceProps:
                    total_secs = int(float(deviceProps["usage"]))
                else:
                    total_secs = 0
                ks.hset("device.id." + device, mapping={"usage":"{}".format(int(total_secs+secs))})

        time.sleep(1)


# /api/devices/types

@cherrypy.expose
class DeviceTypes(object):

    @cherrypy.tools.json_out()
    def GET(self, control="relay"):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("device.{}.types".format(control)):
            raise cherrypy.HTTPError(502, "Missing datastore key.")
            return

        data = list(ks.smembers("device.{}.types".format(control)))

        return {'data':data}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):

        if not "control" in cherrypy.request.json:
            raise cherrypy.HTTPError(400, "Missing 'control' parameter.")
            return
        else:
            control = cherrypy.request.json["control"]

        if not control in [ "relay","pwm" ]:
            raise cherrypy.HTTPError(400, "Invalid 'control' parameter.")
            return

        if not "type" in cherrypy.request.json:
            raise cherrypy.HTTPError(400, "Missing 'type' parameter.")
            return
        else:
            type = cherrypy.request.json["type"]

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("device.{}.types".format(control)):
            raise cherrypy.HTTPError(502, "Missing datastore key.")
            return

        key = "device.{}.types".format(control)
        ks.sadd(key, type)

        cherrypy.response.status = 202
        return

 
# /api/devices/icons

@cherrypy.expose
class DeviceIcons(object):

    @cherrypy.tools.json_out()
    def GET(self, control="relay"):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("device.{}.icons".format(control)):
            raise cherrypy.HTTPError(502, "Missing datastore key.")
            return

        data = list(ks.smembers("device.{}.icons".format(control)))

        return {'data':data}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):

        if not "control" in cherrypy.request.json:
            raise cherrypy.HTTPError(400, "Missing 'control' parameter.")
            return
        else:
            control = cherrypy.request.json["control"]

        if not control in [ "relay","pwm" ]:
            raise cherrypy.HTTPError(400, "Invalid 'control' parameter.")
            return

        if not "icon" in cherrypy.request.json:
            raise cherrypy.HTTPError(400, "Missing 'icon' parameter.")
            return
        else:
            icon = cherrypy.request.json["icon"]

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("device.{}.icons".format(control)):
            raise cherrypy.HTTPError(502, "Missing datastore key.")
            return

        key = "device.{}.icons".format(control)
        ks.sadd(key, icon)

        cherrypy.response.status = 202
        return

 
