#!/usr/bin/env python

import cherrypy
import json
import redis
import requests
from defines import *


# /api/camera

@cherrypy.expose
class Camera(object):

    def __init__(self):
        self.connect = CameraConnect()
        self.interval = CameraInterval()
        self.settings = CameraSettings()
        self.start = CameraStart()
        self.upload = CameraUpload()

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if ks.exists("camera.properties"):
            cameraProps = ks.hgetall("camera.properties")
            connected = cameraProps["connected"]
            data = dict(connected=connected)
        else:
            raise cherrypy.HTTPError(502, "Missing datastore key.")
            return

        result = {'data':data}
        return result


# /api/camera/connect

@cherrypy.expose
class CameraConnect(object):

    @cherrypy.tools.json_out()
    def PUT(self, lastseen, type, ip, mac, uptime):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        cameraProps = dict(
            lastseen=lastseen,
            connected="yes",
            type=type,
            ip=ip,
            mac=mac,
            uptime=uptime
        )
        ks.hset("camera.properties", mapping=cameraProps)

        cherrypy.response.status = 202
        return


# /api/camera/interval

@cherrypy.expose
class CameraInterval(object):

    @cherrypy.tools.json_out()
    def PUT(self, value):

        interval = int(value)

        if not interval > 0 and not interval < 60:
            raise cherrypy.HTTPError(400)
            return

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("camera.properties"):
            raise cherrypy.HTTPError(500)
            return

        cameraProps = dict(interval=interval)
        ks.hset("camera.properties", mapping=cameraProps)

        cherrypy.response.status = 202
        return


# /api/camera/settings

@cherrypy.expose
class CameraSettings(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis( host=RHOST,port=RPORT,db=0,decode_responses=True)

        if ks.exists("camera.properties"):
            cameraProps = ks.hgetall("camera.properties")
            enabled = cameraProps["enabled"]
            interval = cameraProps["interval"]
        else:
            raise cherrypy.HTTPError(500)
            return

        data = dict(enabled=enabled,interval=interval)
        result = {'data':data}
        return result


# /api/camera/start

@cherrypy.expose
class CameraStart(object):

    @cherrypy.tools.json_out()
    def PUT(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("camera.properties"):
            raise cherrypy.HTTPError(500)
            return

        cameraProps = dict(enabled="yes")
        ks.hset("camera.properties", mapping=cameraProps)

        cherrypy.response.status = 202
        return


# /api/camera/stop

@cherrypy.expose
class CameraStop(object):

    @cherrypy.tools.json_out()
    def PUT(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("camera.properties"):
            raise cherrypy.HTTPError(500)
            return

        cameraProps = dict(enabled="no")
        ks.hset("camera.properties", mapping=cameraProps)

        cherrypy.response.status = 202
        return


# /api/camera/upload

@cherrypy.expose
class CameraUpload(object):

    @cherrypy.tools.json_out()
    def POST(self, file):

        upload_path = image_upload_dir
        upload_filename = file.filename

        upload_file = os.path.normpath(
            os.path.join(IMAGE_UPLOAD_DIR, upload_filename))

        with open(upload_file, 'wb') as out:
            while True:
                data = file.file.read(8192)
                if not data:
                    break
                out.write(data)

        cherrypy.response.status = 202
        return


