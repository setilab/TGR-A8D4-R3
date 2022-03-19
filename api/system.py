#!/usr/bin/env python

import os
import subprocess
from datetime import date,datetime,timedelta
import time
#import sys
import cherrypy
import json
import redis
import requests
from defines import *


# /api/system

@cherrypy.expose
class System(object):

    def __init__(self):
        self.events = Events()
        self.health = Health()
        self.reboot = Reboot()
        self.shutdown = Shutdown()
        self.services = Services()
        self.status = Status()
        self.wifi = Wifi()

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)

        if ks.exists("sensor.module.properties"):
            sensor = ks.hgetall("sensor.module.properties")
        else:
            sensor = {}

        if ks.exists("output.module.properties"):
            output = ks.hgetall("output.module.properties")
        else:
            output = {}

        cmd = ['/home/pi/tgr/bin/cpuinfo']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        type = o.decode('ascii').strip('\n')

        tplconnect = {}
        try:
            resp = requests.get(TPLEP + "/system")
        except:
            print("ERROR: Unable to connect to TPL Module API.")
        else:
            if resp.ok:
                tplconnect = json.loads(resp.text)["data"]["tplconnect"]

        cntlrProps = {}
        if ks.exists("controller.properties"):
            cntlrProps = ks.hgetall("controller.properties")

        cntlrProps["type"] = type
        cntlrProps["api"] = VERSION
        cntlrProps["modules"] = {'sensor':sensor,'output':output,'tplconnect':tplconnect}

        data = {'controller':cntlrProps}

        if ks.exists("camera.properties"):
            cameraProps = ks.hgetall("camera.properties")

            camera = {'type':cameraProps["type"],
                      'ip':cameraProps["ip"],
                      'mac':cameraProps["mac"]
            }
            data["camera"] = camera

        result = {'data':data}
        return result

    @cherrypy.tools.json_in()
    def PUT(self):

        try:
            jsonData = cherrypy.request.json
        except:
            raise cherrypy.HTTPError(400, "Requires json input data.")
            return

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if ks.exists("controller.properties"):
            current = ks.hgetall("controller.properties")
            props = {**current, **jsonData}
            ks.hset("controller.properties", mapping=props)

            cherrypy.response.status = 202
            return
        else:
            print("Missing 'controller.properties' key.")
            cherrypy.HTTPError(500)
            return


# /api/system/health

@cherrypy.expose
class Health(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if ks.exists("controller.health"):
            health = ks.hgetall("controller.health")
        else:
            print("Missing 'controller.health' key.")
            cherrypy.HTTPError(500)
            return

        return {'data':health}


# /api/system/services

@cherrypy.expose
class Services(object):

    @cherrypy.tools.json_out()
    def GET(self):

        tplconnect = {}
        try:
            response = requests.get(TPLEP + "/system/services")
        except:
            print("WARN: Unable to connect to tplconnect module.")
        else:
            if not response.ok:
                print("WARN: Unexpected response from tplconnect module.")
            else:
                tplconnect = json.loads(response.text)["data"]

        cmd = ['/home/pi/tgr/bin/services']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        svcs = o.decode('ascii').strip("\n").split('\n')

        return {'data':{'main':svcs,'tplconnect':tplconnect}}


# /api/system/reboot

@cherrypy.expose
class Reboot(object):

    @cherrypy.tools.json_out()
    def PUT(self):

        data = "name=all&state=off"

        try:
            response = requests.post(OCMEP + "/relays", data=data)
        except:
            print("WARN: Unable to connect to output module.")
        else:
            if not response.ok:
                print("WARN: Unexpected response from output module.")
            else:
                try:
                    response = requests.post(OCMEP + "/system", data="name=reset&setting=10")
                except:
                    print("WARN: Unable to connect to output module.")
                else:
                    if not response.ok:
                        print("WARN: Unexpected response from output module.")
        try:
            response = requests.put(TPLEP + "/system/reboot")
        except:
            print("WARN: Unable to connect to tplconnect module.")
        else:
            if not response.ok:
                print("WARN: Unexpected response from tplconnect module.")

        cmd = ['sudo','/bin/systemctl','restart', 'tgr.sensor.module']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()

        cmd = ['sudo','/bin/systemctl','reboot']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        return o.decode('ascii').strip('\n')


# /api/system/shutdown

@cherrypy.expose
class Shutdown(object):

    @cherrypy.tools.json_out()
    def PUT(self, delay="0"):

        if not int(delay) >= 0 and not int(delay) <= 60:
            raise cherrypy.HTTPError(400)
            return

        try:
            response = requests.post(OCMEP + "/relays", data="name=all&state=off")
        except:
            pass

        try:
            response = requests.put(TPLEP + "/system/shutdown")
        except:
            print("WARN: Unable to connect to tplconnect module.")
        else:
            if not response.ok:
                print("WARN: Unexpected response from tplconnect module.")

        cmd = ['sudo','/bin/systemctl','poweroff']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        return o.decode('ascii').strip('\n')


# /api/system/status

@cherrypy.expose
class Status(object):

    @cherrypy.tools.json_out()
    def GET(self, show=""):

        ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)

        if ks.exists("camera.properties"):
            cameraProps = ks.hgetall("camera.properties")
            connected = cameraProps["connected"]
            enable = cameraProps["enable"]
            camera = dict(connected=connected,enabled=enable)
        else:
            camera = dict(connected="no")

        tplconnect = {}
        try:
            response = requests.get(TPLEP + "/system/status")
        except:
            print("WARN: Unable to connect to tplconnect module.")
        else:
            if not response.ok:
                print("WARN: Unexpected response from tplconnect module.")
            else:
                tplconnect = json.loads(response.text)["data"]["tplconnect"]

        cmd = ['uptime', '-p']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        uptime = o.decode('ascii').strip('\n')

        cmd = ['cat', '/sys/class/thermal/thermal_zone0/temp']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        t = int(o.decode('ascii'))
        c = t / 1000
        cpuf = (1.8 * c) + 32.00

        main = {'uptime':uptime,
                'cputemp':"{}{}".format(cpuf,'F')
        }

        cmd = ['sudo','python','/home/pi/tgr/bin/pijuicestats.py']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        data = o.decode('ascii').strip('\n')
        try:
            battery = json.loads(data.replace("'", '"'))
        except:
            battery = {'status': 'UNKNOWN', 'charge': 'UNKNOWN'}

        cmd = ['/sbin/iwgetid']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        connection = o.decode('ascii').strip('\n')
        iface,essid = connection.split()
        k,ssid = essid.split(":")

        cmd = ['/home/pi/tgr/bin/wifi']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        data = o.decode('ascii').strip('\n')
        try:
            net = json.loads(data.replace("'", '"'))
        except:
            net = {'ip':'unknown','mac':'unknown'}

        wifi = {'interface':iface,'ssid':ssid.replace('"', ''),'ip':net["ip"],'mac':net["mac"]}

        dt = datetime.now().isoformat(sep=' ',timespec='seconds')
        
        if show == "all":
            main["datetime"] = dt
            main["battery"] = battery
            main["wifi"] = wifi
            myname = os.uname().nodename
            urls = {}
            urls["api"] = "http://{}.local:8080/api".format(myname)
            urls["console"] = "http://{}.local".format(myname)
            main["urls"] = urls
            result = {'data':{'main':main,'tplconnect':tplconnect,'camera':camera}}
        else:
            result = {'data':{'datetime':dt,'battery':battery,'camera':camera,'wifi':wifi}}

        return result


# /api/system/events

@cherrypy.expose
class Events(object):

    @cherrypy.tools.json_out()
    def GET(self):

        raise cherrypy.HTTPError(501)
        return


# /api/system/wifi

@cherrypy.expose
class Wifi(object):

    def __init__(self):
        self.connect = WifiConnect()
        self.networks = WifiNetworks()

    @cherrypy.tools.json_out()
    def GET(self):

        cmd = ['/home/pi/tgr/bin/wifi']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        wifi = json.loads(o.decode('ascii').strip('\n'))

        return {'data':{'wifi':wifi}}


# /api/system/wifi/connect

@cherrypy.expose
class WifiConnect(object):

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):

        ssid = cherrypy.request.json["ssid"]
        psk = cherrypy.request.json["psk"]

        cmd = ['/home/pi/tgr/bin/wificonnect', ssid, psk]
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        command = {'stdout':o,'stderr':e}

        return {'data':{'command':command}}


# /api/system/wifi/networks

@cherrypy.expose
class WifiNetworks(object):

    @cherrypy.tools.json_out()
    def GET(self):

        cmd = ['/home/pi/tgr/bin/wifinets']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        rawlist = o.decode('ascii').strip('\n')

        networks = list(rawlist.split("\n"))

        wifi = {'networks':networks}

        return {'data':{'wifi':wifi}}


