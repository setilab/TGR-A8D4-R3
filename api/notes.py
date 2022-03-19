#!/usr/bin/env python

import cherrypy
import json
import redis
import random
import string
import psycopg
from datetime import datetime
from defines import *

# /api/notes

@cherrypy.expose
class Notes(object):

    @cherrypy.tools.json_out()
    def GET(self):

        data = list()

        try:
            qdConn = psycopg.connect(qdConnectStr)
        except:
            print("ERROR: Unable to connect to QuestDB service at: {}".format(qdConnectStr))
            raise cherrypy.HTTPError(502)
            return
        else:
            qdCur = qdConn.cursor()
            qdCur.execute("SELECT * FROM grow_notes")
            result = qdCur.fetchall()
            for row in result:
                data.append({'ts':"{}".format(row[0]),'note':row[1]})

            qdCur.close()
            qdConn.close()

        return {'data':data}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):

        try:
            note = cherrypy.request.json["note"]
        except:
            raise cherrypy.HTTPError(400, "Missing 'note' parameter.")
            return

        try:
            date = cherrypy.request.json["date"]
        except:
            ts = datetime.now()
        else:
            ts = datetime.fromisoformat(date)

        try:
            qdConn = psycopg.connect(qdConnectStr)
        except:
            print("ERROR: Unable to connect to QuestDB service at: {}".format(qdConnectStr))
            raise cherrypy.HTTPError(502)
            return
        else:
            qdCur = qdConn.cursor()

            qdCur.execute("INSERT INTO grow_notes" +
                          " (ts, note) VALUES " +
                          "(%s, %s)", (ts, note))

            qdConn.commit()
            qdCur.close()
            qdConn.close()

        cherrypy.response.status = 202
        return


