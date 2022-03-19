#!/usr/bin/env python
import os
import datetime as dt
import time
import redis
import requests

# Redis
RHOST   =     os.getenv("TGR_REDIS_HOST", "172.17.0.1")
RPORT   = int(os.getenv("TGR_REDIS_PORT", "6379"))
RDB     = int(os.getenv("TGR_REDIS_DB", "0"))

ks = redis.Redis(host=RHOST, port=RPORT, db=RDB, decode_responses=True)
ks.config_set('notify-keyspace-events', 'KEA')

def event_handler(msg):

    if msg["data"] == "expired":
        
        key = msg["channel"].split(":")[1]
        device = key.split("device.state.id.")[1]
        key = "device.id." + device
        if ks.hgetall(key)["online"] == "yes":
            print("{} has gone offline.".format(device))
            ks.hset(key, mapping={'online':'no'})
            ks.set("device.status.id." + device, 'offline')
            ks.hset("device.states", mapping={device:'unknown'})
 
    elif msg["data"] == "set":
        
        key = msg["channel"].split(":")[1]
        state = ks.get(key)
        device = key.split("device.state.id.")[1]
        key = "device.id." + device
        if ks.hgetall(key)["online"] == "no":
            print("{} is back online.".format(device))
            ks.hset(key, mapping={'online':'yes'})
            ks.hset("device.states", mapping={device:state})
            ks.set("device.status.id." + device, 'online')
 

pubsub = ks.pubsub()
pubsub.psubscribe(**{'__keyspace@0__:device.state.id.*': event_handler})
thread = pubsub.run_in_thread(sleep_time=0.01)
