#!/usr/bin/env python

import subprocess
import cherrypy
import redis
from defines import *


# /api/system

@cherrypy.expose
class System(object):

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

        cmd = ['cat', 'sysinfo']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        type = o.decode('ascii').strip('\n')

        cntlrProps = {}
        if ks.exists("controller.properties"):
            cntlrProps = ks.hgetall("controller.properties")

        cntlrProps["type"] = type
        cntlrProps["api"] = VERSION
        cntlrProps["modules"] = {'sensor':sensor,'output':output}

        data = {'controller':cntlrProps}

        return {'data':data}

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


