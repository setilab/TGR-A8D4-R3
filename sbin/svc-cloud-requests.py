#!/usr/bin/env python

from ws4py.client.threadedclient import WebSocketClient
from datetime import datetime
import requests
import threading
import json
import redis
import os
import time

RHOST = os.getenv("TGR_REDIS_HOST", "172.17.0.1")
RPORT = int(os.getenv("TGR_REDIS_PORT", "6379"))
CLIENT_URL = os.getenv("TGR_CLOUD_REQUESTS_URL", "http://cloud.thegreenroom.io:31001/v2")
WS_URL = os.getenv("TGR_CLOUD_WEBSOCKET_URL", "ws://cloud.thegreenroom.io:31003/controller/")
MY_URL = "http://localhost:8080/api/"
JOB_URL = CLIENT_URL + "/requests/"
POLL_RATE = int(os.getenv("TGR_CLOUD_REQUESTS_POLL_INTERVAL", "5"))


apicalls = {
    "system":"system",
    "health":"system/health",
    "sensors":"sensors",
    "devices":"devices/properties",
    "devicestates":"devices/states",
    "settings":"settings",
    "timers":"timers/properties",
    "tasks":"tasks",
    "taskids_grow":"tasks/log/grow?filter=today",
    "taskids_growroom":"tasks/log/growroom?filter=today",
    "presets":"presets",
    "alarm":"alarm",
    "alarmsources":"alarm/sources",
    "grow":"grow/properties"
}

def fetch_api_data():

    dataset = {}
    session = requests.Session()
    for call in apicalls:
        url = MY_URL + apicalls[call]
        try:
            response = session.get(url)
        except:
            print("Error connecting to local API.")
        else:
            if response.ok:
                dataset[call] = response.text
            else:
                print("Error response from local API.")

    return dataset


class RealTimeClient(WebSocketClient):
    def opened(self):
        def events(msg):
            if self.subscribe:
                chan = msg["channel"]
                k,e = chan.split(":")
                newkey = "{}.{}".format(msg["data"],self.id)
                if e == "set":
                    try:
                        self.send(json.dumps({newkey:self.ds.get(msg["data"])}))
                    except:
                        self.thread.stop()
                elif e == "hset":
                    if msg["data"].startswith("sensor.data."):
                        props = self.ds.hgetall(msg["data"])
                        ts = props["timestamp"]
                        dt = datetime.fromisoformat(ts)
                        if dt.second % 5 == 0:
                            try:
                                self.send(json.dumps({newkey:self.ds.hgetall(msg["data"])}))
                            except:
                                self.thread.stop()
                    else:
                        try:
                            self.send(json.dumps({newkey:self.ds.hgetall(msg["data"])}))
                        except:
                            self.thread.stop()
                elif e == "sadd":
                    try:
                        self.send(json.dumps({newkey:list(self.ds.smembers(msg["data"]))}))
                    except:
                        self.thread.stop()
                elif e == "del":
                    try:
                        self.send(json.dumps({newkey:"deleted"}))
                    except:
                        self.thread.stop()
                elif e == "expired":
                    try:
                        self.send(json.dumps({newkey:"expired"}))
                    except:
                        self.thread.stop()

        def data_provider():
            ds = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)
            ds.config_set('notify-keyspace-events', 'KEA')
            self.ds = ds
            self.id = ds.hget("controller.properties", "cloudsvcid")

            pubsub = ds.pubsub()
            pubsub.psubscribe(**{'__keyevent@0__:*': events})
            self.thread = pubsub.run_in_thread(sleep_time=0.01)

        self.send('{"msg":"ready"}')
        self.subscribe = False
        data_provider()

    def closed(self, code, reason=None):
        print(f"Closed down {code} {reason}")
        self.thread.stop()
        self.close(reason=reason)

    def received_message(self, m):
        req = json.loads(f"{m}")["request"]
        if req == "initialize":
            print("Fetch initial data and send.")
            dataset = fetch_api_data()
            for key in dataset:
                newkey = f"dataset.{key}.{self.id}"
                self.send(json.dumps({newkey:dataset[key]}))
            self.send('{"response":"done"}')
        elif req == "subscribe":
            print("Send subscription data.")
            self.subscribe = True
        elif req == "unsubscribe":
            print("Stop subscription data.")
            self.subscribe = False
        elif req == "close":
            print("Close connection.")
            self.thread.stop()
            self.close(reason="done")
        else:
            print(m)


def process_api_call(session, jobid, payload):

    method = payload["method"]
    url    = payload["url"]

    try:
        jsonData = payload["json"]
    except:
        jsonData = {}

    if method == "GET":
        r = requests.get(MY_URL + url)

    elif method == "POST":
        if any(jsonData):
            r = requests.post(MY_URL + url, json=jsonData)
        else:
            r = requests.post(MY_URL + url)

    elif method == "PUT":
        if any(jsonData):
            r = requests.put(MY_URL + url, json=jsonData)
        else:
            r = requests.put(MY_URL + url)

    elif method == "DELETE":
        if any(jsonData):
            r = requests.delete(MY_URL + url, json=jsonData)
        else:
            r = requests.delete(MY_URL + url)
    else:
        print("Unsupported method: {}.".format(method))

    myr = {"status_code":r.status_code}

    if r.ok and len(r.text) > 0:
        myr["body"] = json.loads(r.text)

    payload = {'jobid':jobid,'response':myr}

    try:
        response = session.put(JOB_URL + myId, json=payload)
    except:
        print("Unable to connect to request queue service.")


def start_ws(myId):

    try:
        ws = RealTimeClient(WS_URL + myId + "/ws", protocols=['http-only'])
    except:
        print("Unable to connect to websocket service.")
        return
    else:
        ws.connect()
        ws.run_forever()


def jobRunner(session, myId):

    try:
        r = session.put(CLIENT_URL + "/controller/" + myId)
    except:
        print("Unable to connect to controller api.")
        return
    else:
        if not r.ok:
            print("Unexpected response from controller api: {}".format(r.status_code))
            return

    try:
        r = session.get(JOB_URL + myId)
    except:
        print("Unable to connect to request queue service.")
    else:
        if r.ok:
            data = json.loads(r.text)
            try:
                jobId = data["jobid"]
                jobStatus = data["job"]
                type = data["request"].get("type")
            except:
                print(data)
            else:
                print("Handling request job {}.".format(jobId))
                if type == "api":
                    process_api_call(session, jobId, data["request"])
                elif type == "websocket":
                    threading.Thread(name="wsdata", target=start_ws, args=(myId,)).start()
                    myr = {"status_code":202}
                else:
                    print("Missing or invalid request type.")
                    myr = {"status_code":400}

                if type != "api":
                    payload = {'jobid':jobId,'response':myr}
                    try:
                        response = session.put(JOB_URL + myId, json=payload)
                    except:
                        print("Unable to connect to request queue service.")


if __name__ == '__main__':

    try:
        ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)
    except:
        print("Unable to connect to Redis service.")
        exit()

    try:
        myId = ks.hget("controller.properties", "cloudsvcid")
    except:
        print("Controller has not registered to cloud services.")
        exit()

    session  = requests.Session()

    while True:

        jobRun = False

        now = datetime.now()

        if now.second % POLL_RATE == 0:
            if jobRun == False:
                jobRun = True
                jobRunner(session, myId)
        else:
            jobRun = False

        time.sleep(1)

