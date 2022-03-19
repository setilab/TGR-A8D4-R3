#!/usr/bin/env python

import cherrypy
import json
import redis
import requests
from defines import *

# /api/weather

@cherrypy.expose
class Weather(object):

    def __init__(self):
        self.current = WeatherCurrent()
        self.forecast = WeatherForecast()

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        if ks.exists("weather.properties"):
            weather = ks.hgetall("weather.properties")
            return {'data':{'config':weather}}
        else:
            return {'data':{'service':'unconfigured'}}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):

        if "longitude" in cherrypy.request.json:
            long = cherrypy.request.json["longitude"]
        else:
            raise cherrypy.HTTPError(400, "Missing 'longitude' parameter.")
            return

        if "latitude" in cherrypy.request.json:
            lat = cherrypy.request.json["latitude"]
        else:
            raise cherrypy.HTTPError(400, "Missing 'latitude' parameter.")
            return

        resp = requests.get("https://api.weather.gov/points/{},{}".format(long,lat))
        if resp.ok:
            data = json.loads(resp.text)
            city     = data["properties"]["relativeLocation"]["properties"].get("city")
            state    = data["properties"]["relativeLocation"]["properties"].get("state")
            location = "{}, {}".format(city,state)
            forecast = data["properties"]["forecast"]
            stations = data["properties"]["observationStations"]

        resp = requests.get(stations)
        if resp.ok:
            data = json.loads(resp.text)
            stationid = data["features"][0]["properties"]["stationIdentifier"]

        current = "https://api.weather.gov/stations/{}/observations/latest".format(stationid)

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        ks.hset("weather.properties",mapping={"location":location,"forecast":forecast,"current":current})

        cherrypy.response.status = 202
        return


@cherrypy.expose
class WeatherCurrent(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        resp = requests.get(ks.hgetall("weather.properties")["current"])
        if resp.ok:
            data = json.loads(resp.text)["properties"]

        return {'data':data}


@cherrypy.expose
class WeatherForecast(object):

    @cherrypy.tools.json_out()
    def GET(self):

        ks = redis.Redis(host=RHOST,port=RPORT,db=0,decode_responses=True)

        resp = requests.get(ks.hgetall("weather.properties")["forecast"])
        if resp.ok:
            data = json.loads(resp.text)["properties"]

        return {'data':data}

