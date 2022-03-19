#!/usr/bin/env python

import cherrypy
import json
import redis
import random
import string
import psycopg
from datetime import datetime
from defines import *

# /api/tasks

@cherrypy.expose
class Tasks(object):

    def __init__(self):
        self.log = TaskLog()

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        growroom = ks.hgetall("tasks.types.growroom")
        grow = ks.hgetall("tasks.types.grow")
        return {'data':{'growroom':growroom,'grow':grow}}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        keyNs = "tasks.types."

        if "type" in cherrypy.request.json:
            type = cherrypy.request.json["type"]
            if not type in [ "growroom","grow" ]:
                raise cherrypy.HTTPError(400, "Invalid type property.")
                return
        else:
            raise cherrypy.HTTPError(400, "Missing type property.")
            return

        if "task" in cherrypy.request.json:
            taskid = ''.join(random.sample(string.hexdigits, 8))
            key = keyNs + type
            ks.hset(key, mapping={taskid:cherrypy.request.json["task"]})
            cherrypy.response.status = 202
        else:
            raise cherrypy.HTTPError(400, "Missing task property.")
        return


@cherrypy.expose
@cherrypy.popargs('type')
class TaskLog(object):

    @cherrypy.tools.json_out()
    def GET(self, type, filter=""):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        key = "tasks.types." + type
        taskTypes = ks.hgetall(key)
        data = list()

        if filter == "today":
            keyNs = "tasks.id."
            taskids = ks.keys(keyNs + "*")
            for key in taskids:
                taskid = key.split(keyNs)[1]
                if taskid in taskTypes:
                    data.append(taskid)
        else:
            table_name = type + "_tasks"

            try:
                qdConn = psycopg.connect(qdConnectStr)
            except:
                print("ERROR: Unable to connect to QuestDB service at: {}".format(qdConnectStr))
                raise cherrypy.HTTPError(502)
                return
            else:
                qdCur = qdConn.cursor()
                qdCur.execute("SELECT * FROM " + table_name)
                result = qdCur.fetchall()
                for row in result:
                    data.append({'ts':"{}".format(row[0]),'task':taskTypes[row[1]]})

                qdCur.close()
                qdConn.close()

        return {'data':data}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, type):

        if not type in [ "growroom","grow" ]:
            raise cherrypy.HTTPError(400, "Invalid 'type' parameter.")
            return

        try:
            taskid = cherrypy.request.json["taskid"]
        except:
            raise cherrypy.HTTPError(400, "Missing 'taskid' parameter.")
            return

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        key = "tasks.types." + type
        if not taskid in ks.hgetall(key):
            raise cherrypy.HTTPError(400, "Invalid task id.")
            return

        try:
            date = cherrypy.request.json["date"]
        except:
            ts = datetime.now()
        else:
            ts = datetime.fromisoformat(date)

        table_name = type + "_tasks"

        try:
            qdConn = psycopg.connect(qdConnectStr)
        except:
            print("ERROR: Unable to connect to QuestDB service at: {}".format(qdConnectStr))
            raise cherrypy.HTTPError(502)
            return
        else:
            qdCur = qdConn.cursor()

            qdCur.execute("INSERT INTO " + table_name +
                          " (ts, task) VALUES " +
                          "(%s, %s)", (ts, taskid))

            qdConn.commit()
            qdCur.close()
            qdConn.close()

        key = "tasks.id." + taskid
        ks.set(key, "{}".format(ts))
        midnite = datetime(ts.year, ts.month, ts.day+1)
        ks.expireat(key, midnite)

        cherrypy.response.status = 202
        return


