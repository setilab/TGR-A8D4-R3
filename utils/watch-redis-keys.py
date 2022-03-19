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

ds = redis.Redis(host=RHOST, port=RPORT, db=RDB, decode_responses=True)
ds.config_set('notify-keyspace-events', 'KEA')

def ks_event_handler(msg):
    print("{}::{}".format(dt.datetime.now(), msg))

def ke_event_handler(msg):
    print("{}::{}".format(dt.datetime.now(), msg))

pubsub = ds.pubsub()
pubsub.psubscribe(**{'__keyspace@0__:test.*': ks_event_handler})
#pubsub.psubscribe(**{'__keyevent@0__:*': ke_event_handler})
thread = pubsub.run_in_thread(sleep_time=0.01)
