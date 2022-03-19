#!/usr/bin/env python

import os
import subprocess
import sys
import json
import cherrypy
from defines import *

# /api/images

@cherrypy.expose
class Images(object):

    @cherrypy.tools.json_out()
    def GET(self, fullpath=""):

        if fullpath == "yes":
            cmd = ['/home/pi/tgr/bin/images', '-ls', '-fp']
        else:
            cmd = ['/home/pi/tgr/bin/images', '-ls']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        images = o.decode('ascii').strip('\n').split('\n')

        return dict(data=images)

    @cherrypy.tools.json_out()
    def DELETE(self):

        cmd = ['/home/pi/tgr/bin/images', '-rm']
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        o, e = proc.communicate()
        response = o.decode('ascii').strip('\n')

        return dict(deleted=response)


