#!/usr/bin/env python3
#
# svc-udp-msg.py -- Message service for the controller. Listens on UDP port
# number 63000 by default.
#
import os
import socket
import sys
import json
import redis
import time

# Current self
VERSION = "1.01"

# Redis
RHOST = os.getenv("TGR_REDIS_HOST", "172.17.0.1")
RPORT = int(os.getenv("TGR_REDIS_PORT", "6379"))
RDB   = int(os.getenv("TGR_REDIS_DB", "0"))

# UDP
HOST = os.getenv("TGR_MSGSVC_UDP_ADDR", "192.168.254.3")
PORT = int(os.getenv("TGR_MSGSVC_UDP_PORT", "63000"))

def udpMsgServer():

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except:
        print("Failed to create socket.")
        sys.exit()

    while True:
        try:
            s.bind((HOST, PORT))
        except:
            print("Socket bind failed.")
            time.sleep(3)
        else:
            break

    while True:
        # receive data from client (data, addr)
        data,addr = s.recvfrom(1024)

        print(data.decode())
        #jsonData = json.loads(data.decode())
        #print(jsonData)
        jsonData = {}

        if "system" in jsonData:
            try:
                ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)
            except:
                print("ERROR: Unable to connect to Redis service.")
            else:
                if "boot" in jsonData["system"]:
                    if not ks.exists("output.module.properties"):
                        outputModuleProps = jsonData["system"]["boot"]
                        ks.hset("output.module.properties", mapping=outputModuleProps)

                elif "config" in jsonData["system"]:
                    relayIds = jsonData["system"]["config"]["relays"]
                    for relay in relayIds:
                        if not ks.exists("device.id." + relay["id"]):
                            relayProps = {}
                            relayProps["id"] = relay["id"]
                            relayProps["name"] = relay["label"]
                            relayProps["output"] = relay["output"]
                            relayProps["module"] = "ocmodule"
                            relayProps["control"] = "relay"
                            relayProps["type"] = "spare"
                            relayProps["icon"] = "spare"
                            relayProps["mode"] = "manual"
                            relayProps["state"] = "unknown"
                            relayProps["online"] = "no"
                            relayProps["automation"] = "enabled"
                            ks.hset("device.id." + relay["id"], mapping=relayProps)

                    fanIds = jsonData["system"]["config"]["fans"]
                    for fan in fanIds:
                        if not ks.exists("device.id." + fan["id"]):
                            fanProps = {}
                            fanProps["id"] = fan["id"]
                            fanProps["name"] = fan["label"]
                            fanProps["module"] = "ocmodule"
                            fanProps["control"] = "pwm"
                            fanProps["type"] = "spare"
                            fanProps["icon"] = "spare"
                            fanProps["mode"] = "manual"
                            fanProps["speed"] = "unknown"
                            fanProps["speed_max"] = "0"
                            fanProps["online"] = "no"
                            fanProps["automation"] = "enabled"
                            ks.hset("device.id." + fan["id"], mapping=fanProps)

                elif "heartbeat" in jsonData["system"]:
                    deviceStates = {}
                    relays = jsonData["system"]["heartbeat"]["relays"]
                    for relay in relays:
                        key = "device.id." + relay["id"]
                        ks.hset(key, mapping={'state':relay["state"]})
                        key = "device.state.id." + relay["id"]
                        ks.set(key, relay["state"])
                        ks.expire(key, 300)
                        deviceStates[relay["id"]] = relay["state"]

                    fans = jsonData["system"]["heartbeat"]["fans"]
                    for fan in fans:
                        key = "device.id." + fan["id"]
                        if int(fan["speed"]) < 255:
                            state = "on"
                        else:
                            state = "off"
                        ks.hset(key, mapping={'state':state,'speed':fan["speed"]})
                        key = "device.state.id." + fan["id"]
                        ks.set(key, state)
                        ks.expire(key, 300)
                        deviceStates[fan["id"]] = state

                    ks.hset("device.states", mapping=deviceStates)

                elif "update" in jsonData["system"]:
                    if "relay" in jsonData["system"]["update"]:
                        relay = jsonData["system"]["update"]["relay"]["id"]
                        state = jsonData["system"]["update"]["relay"]["state"]
                        key = "device.id." + relay
                        ks.hset(key, mapping={'state':state})
                        key = "device.state.id." + relay
                        ks.set(key, state)
                        ks.expire(key, 300)
                        ks.hset("device.states", mapping={relay:state})
                    elif "fan" in jsonData["system"]["update"]:
                        fan = jsonData["system"]["update"]["fan"]["id"]
                        speed = jsonData["system"]["update"]["fan"]["speed"]
                        if int(speed) < 255:
                            state = "on"
                        else:
                            state = "off"
                        key = "device.id." + fan
                        ks.hset(key, mapping={'state':state,'speed':speed})
                        key = "device.state.id." + fan
                        ks.set(key, state)
                        ks.expire(key, 300)
                        ks.hset("device.states", mapping={fan:state})


if __name__ == '__main__':

    while True:
        udpMsgServer()
        time.sleep(5)

    s.close()
