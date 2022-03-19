#!/usr/bin/env python

from datetime import date,datetime,timedelta
import cherrypy
import json
import redis
import psycopg
import random
import string
import subprocess
from defines import *

 
# /api/growing

@cherrypy.expose
class Growing(object):

    def __init__(self):
        self.growspaces = Growspaces()
        self.lighting = Lighting()
        self.mediums = Mediums()
        self.usages = Usages()

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "grow.resource."

        resources = []
        resourceKeys = ds.keys(keyNs + "*")
        for key in resourceKeys:
            resource = key.split(keyNs)[1]
            resources.append(resource)
        
        return {'data':{'resources':resources}}


# /api/growing/growspaces

@cherrypy.expose
class Growspaces(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("grow.resource.growspaces"):
            raise cherrypy.HTTPError(500)
            return

        return {'data':{'growspaces':list(ks.smembers("grow.resource.growspaces"))}}


# /api/growing/lighting

@cherrypy.expose
class Lighting(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("grow.resource.lighting"):
            raise cherrypy.HTTPError(500)
            return

        return {'data':{'lighting':list(ks.smembers("grow.resource.lighting"))}}


# /api/growing/mediums

@cherrypy.expose
class Mediums(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("grow.resource.mediums"):
            raise cherrypy.HTTPError(500)
            return

        return {'data':{'mediums':list(ks.smembers("grow.resource.mediums"))}}


# /api/growing/usages

@cherrypy.expose
class Usages(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("grow.resource.usages"):
            raise cherrypy.HTTPError(500)
            return

        return {'data':{'usages':list(ks.smembers("grow.resource.usages"))}}


# /api/grow

@cherrypy.expose
class Grow(object):

    def __init__(self):
        self.properties = GrowProperties()
        self.publish = GrowLogPublish()
        self.history = GrowLogHistory()

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if ks.exists("grow.properties"):
            return {'data':{'active':'yes'}}
        else:
            return {'data':{'active':'no'}}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if ks.exists("grow.properties"):
            raise cherrypy.HTTPError(409)
            return
        print(cherrypy.request.json)

        try:
            name = cherrypy.request.json["name"]
        except:
            print("name")
            raise cherrypy.HTTPError(400, "Invalid or missing 'name' parameter.")
            return

        try:
            startdate = cherrypy.request.json["startdate"]

            try:
                dt = datetime.fromisoformat(startdate)
            except:
                print("startdate")
                raise cherrypy.HTTPError(400, "Must supply a valid start date.")
                return
        except:
            startdate = "{}".format(date.today())

        try:
            veglen = cherrypy.request.json["veglen"]
            if not int(veglen) > 0 and not int(veglen) < 180:
                print("veglen")
                raise cherrypy.HTTPError(400, "Must supply veglen value between 1 and 180.")
                return
        except:
            veglen = 0

        try:
            flowerlen = cherrypy.request.json["flowerlen"]
            if not int(flowerlen) > 0 and not int(flowerlen) < 100:
                print("flowerlen")
                raise cherrypy.HTTPError(400, "Must supply flowerlen value between 1 and 100.")
                return
        except:
            raise cherrypy.HTTPError(400, "Must supply flowerlen parameter.")
            return

        try:
            phase = cherrypy.request.json["phase"]
            if not phase == "veg" and not phase == "flower":
                print("phase")
                raise cherrypy.HTTPError(400, "Invalid phase parameter.")
                return

            if phase == "veg" and veglen == "0":
                print("veglen2")
                raise cherrypy.HTTPError(400, "Veg phase requires veglen parameter.")
                return
        except:
            raise cherrypy.HTTPError(400, "Must supply phase parameter.")
            return

        try:
            strain = cherrypy.request.json["strain"]
        except:
            strain = "unknown"

        try:
            medium = cherrypy.request.json["medium"]
        except:
            medium = "unspecified"

        try:
            lighting = cherrypy.request.json["lighting"]
        except:
            lighting = "unspecified"

        try:
            started_from = cherrypy.request.json["started_from"]
        except:
            started_from = "unspecified"

        active = "yes"

        if phase == "veg":
            vdate = startdate
            fdate = 'none'
        else:
            vdate = 'none'
            veglen = 'none'
            fdate = startdate

        properties = {'startdate':vdate,'duration':veglen,
                      'enddate':'none'}

        key = "grow.veg.properties"
        ks.hset(key, mapping=properties)

        properties = {'startdate':fdate,'duration':flowerlen,
                      'enddate':'none'}

        key = "grow.flower.properties"
        ks.hset(key, mapping=properties)

        properties = {'name':name,'phase':phase,'strain':strain,
                      'medium':medium,'lighting':lighting,
                      'started_from':started_from,'active':active}

        ks.hset("grow.properties", mapping=properties)

        cherrypy.response.status = 202
        return

    @cherrypy.tools.json_out()
    def DELETE(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("grow.properties"):
            raise cherrypy.HTTPError(404)
            return

        try:
            qdConn = psycopg.connect(qdConnectStr)
        except:
            print("Unable to connect to QuestDB service at: {}".format(qdConnectStr))
            raise cherrypy.HTTPError(502)
            return
        else:
            qdCur = qdConn.cursor()

            try:
                qdCur.execute("TRUNCATE TABLE grow_sensors;")
                qdCur.execute("TRUNCATE TABLE grow_devices;")
                qdCur.execute("TRUNCATE TABLE grow_tasks;")
                qdCur.execute("TRUNCATE TABLE growroom_tasks;")
                qdCur.execute("TRUNCATE TABLE events;")
            except:
                qdCur.close()
                qdConn.close()
                print("ERROR: Unable to execute SQL query with QuestDB service.")
                #raise cherrypy.HTTPError(502)
                #return
            else:
                qdConn.commit()
                qdCur.close()
                qdConn.close()

        ks.delete("grow.properties")
        ks.delete("grow.veg.properties")
        ks.delete("grow.flower.properties")

        cherrypy.response.status = 202
        return

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("grow.properties"):
            raise cherrypy.HTTPError(404)
            return

        properties = ks.hgetall("grow.properties")
        vprops = ks.hgetall("grow.veg.properties")
        fprops = ks.hgetall("grow.flower.properties")

        try:
            active = cherrypy.request.json["active"]

            if not active == "no":
                raise cherrypy.HTTPError(400, "Only 'no' is allowed for active parameter.")
                return

            properties["active"] = active
        except:
            pass

        try:
            name = cherrypy.request.json["name"]
            properties["name"] = name
        except:
            pass

        try:
            strain = cherrypy.request.json["strain"]
            properties["strain"] = strain
        except:
            pass

        try:
            medium = cherrypy.request.json["medium"]
            properties["medium"] = medium
        except:
            pass

        try:
            lighting = cherrypy.request.json["lighting"]
            properties["lighting"] = lighting
        except:
            pass

        try:
            started_from = cherrypy.request.json["started_from"]
            properties["started_from"] = started_from
        except:
            pass

        try:
            myyield = cherrypy.request.json["yield"]
            properties["yield"] = myyield
        except:
            pass

        try:
            drytime = cherrypy.request.json["drytime"]
            properties["drytime"] = drytime
        except:
            pass

        try:
            curetime = cherrypy.request.json["curetime"]
            properties["curetime"] = curetime
        except:
            pass

        try:
            phase = cherrypy.request.json["phase"]
            if properties["phase"] == "flower" and phase == "veg":
                raise cherrypy.HTTPError(409, "Phases cannot go backwards.")
                return

            if properties["phase"] == "veg" and phase == "flower":
                properties["phase"] = phase
                fprops["startdate"] = "{}".format(date.today())
                vprops["enddate"]   = "{}".format(date.today())
            elif properties["phase"] == "flower" and phase == "harvest":
                properties["active"] = "no"
                properties["phase"]  = phase
                fprops["enddate"]    = "{}".format(date.today())
            elif properties["phase"] == "harvest" and phase == "publish":
                properties["phase"]  = phase
        except:
            pass

        try:
            harvest = cherrypy.request.json["harvest"]
        except:
            pass
        else:
            if harvest == "yes":
                fprops["enddate"] = "{}".format(date.today())
                properties["active"] = "no"
                properties["phase"] = "harvest"

        try:
            harvestdate = cherrypy.request.json["harvestdate"]
            try:
                dt = datetime.fromisoformat(harvestdate)
            except:
                raise cherrypy.HTTPError(400, "Must supply a valid harvest date.")
                return
            else:
                if properties["phase"] == "veg":
                    vprops["enddate"] = harvestdate
                else:
                    fprops["enddate"] = harvestdate

                properties["active"] = "no"
                properties["phase"] = "harvest"
        except:
            pass

        ks.hset("grow.veg.properties", mapping=vprops)
        ks.hset("grow.flower.properties", mapping=fprops)
        ks.hset("grow.properties", mapping=properties)

        cherrypy.response.status = 202
        return


# /api/grow/properties

@cherrypy.expose
class GrowProperties(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("grow.properties"):
            return {'data':{}}

        grow = ks.hgetall("grow.properties")

        phase = grow["phase"]
        veg = ks.hgetall("grow.veg.properties")
        flower = ks.hgetall("grow.flower.properties")

        if grow["active"] == "yes":
            if phase == "veg":
                sd = veg["startdate"]
                dur = veg["duration"]
            elif phase == "flower":
                sd = flower["startdate"]
                dur = flower["duration"]

            grow["veglen"] = veg["duration"]
            grow["flowerlen"] = flower["duration"]
            grow["startdate"] = sd
            grow["duration"] = dur

            start_d = date.fromisoformat(sd)
            end_d = start_d + timedelta(days=int(dur))

            current_d = date.today()
            duration = current_d - start_d
            remaining = end_d - current_d
            current_week = int(duration.days / 7) + 1
            current_day = int(duration.days % 7)
            grow["week"] = current_week
            grow["day"] = current_day
            grow["enddate"] = end_d.isoformat()
            grow["remaining"] = remaining.days
        else:
            sd = veg["startdate"]
            ed = veg["enddate"]
            dur = date.fromisoformat(ed) - date.fromisoformat(sd)
            veg["duration"] = dur.days

            sd = flower["startdate"]
            ed = flower["enddate"]
            dur = date.fromisoformat(ed) - date.fromisoformat(sd)
            flower["duration"] = dur.days

            grow["veg"] = veg
            grow["flower"] = flower

        return {'data':grow}


# /api/grow/publish

@cherrypy.expose
class GrowLogPublish(object):

    @cherrypy.tools.json_out()
    def POST(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if not ks.exists("grow.properties"):
            raise cherrypy.HTTPError(409, "Nothing to publish.") 
            return

        grow = ks.hgetall("grow.properties")
        if grow["active"] == "yes":
            raise cherrypy.HTTPError(409, "Can only publish inactive grows.") 
            return

        growId = ''.join(random.sample(string.hexdigits, 8))

        cmd = ['/home/pi/tgr/bin/growlog', growId]
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        url = "/static/doc/{}.pdf".format(growId)
        pub = "{}".format(date.today())
        ks.hset("grow.history." + growId, mapping={'name':grow["name"],'published':pub,'url':url})
        ks.hset("grow.properties", mapping={'phase':'published','publishdate':pub,'url':url})

        cherrypy.response.status = 202
        return

#    @cherrypy.tools.json_out()
#    def PUT(self):
#
#        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)
#
#        if not ks.exists("grow.properties"):
#            raise cherrypy.HTTPError(409, "Nothing to update.") 
#            return
#
#        grow = ks.hgetall("grow.properties")
#        if grow["active"] == "yes":
#            raise cherrypy.HTTPError(409, "Can only update an inactive grow.") 
#            return
#
#        for key in cherrypy.request.json:
#            if not key in [ "phase","yield","drytime","curetime","note" ]:
#                raise cherrypy.HTTPError(400, "Invalid grow property.") 
#                return
#            if key == "phase" and not cherrypy.request.json["phase"] == "publish":
#                raise cherrypy.HTTPError(400, "Invalid value for phase parameter.") 
#                return
#
#        ks.hset("grow.properties", mapping=cherrypy.request.json)
#
#        cherrypy.response.status = 202
#        return


# /api/grow/history

@cherrypy.expose
class GrowLogHistory(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "grow.history."
        keys  = ks.keys(keyNs + "*")

        grows = {}
        for key in keys:
            growid = key.split(keyNs)[1]
            grows[growid] = ks.hgetall(key)

        return {'data':grows}


