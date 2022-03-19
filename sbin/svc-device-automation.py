#!/usr/local/bin/python

import os
import time
import threading
import redis
import requests

# Current self
VERSION = "1.0"

# Redis
RHOST = os.getenv("TGR_REDIS_HOST", "172.17.0.1")
RPORT = int(os.getenv("TGR_REDIS_PORT", "6379"))

TGRAPI = os.getenv("TGR_API_ENDPOINT", "http://localhost:8080/api")
device_url = TGRAPI + "/devices/id/"

thread_pool = threading.BoundedSemaphore(value=1)
retries = 3

def setDeviceProp(device, property):

    ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)
    ks.hset("device.id." + device, mapping=property)


def setDeviceState(device, prop, state, tries, duration=None, delay=None):

    with thread_pool:

        jsonData = {prop:state}

        if not duration == None:
            jsonData["automation"] = "disabled"

        try:
            response = requests.post(device_url + device, json=jsonData)

            if response.ok:
                # TODO: Support proper event logging here.
                print("Automation triggered {} {}".format(device, state))
            else:
                print("Automation request task failed for {} with {}".format(device, response.status))
        except:
            if tries > 0:
                print("Unable to connect to controller API. Attempting {} more tries...".format(tries))
                tries = tries - 1
                threading.Thread(name="t-"+device, target=setDeviceState, args=(device,state,tries)).start()

        if not duration == None and duration > 0:
            print("Sleeping for {}s".format(duration))
            time.sleep(duration)
            while tries > 0:
                try:
                    response = requests.post(device_url + device, json={"state":"off"})

                    if response.ok:
                        if delay == None:
                            delay = 900
                        threading.Timer(delay, setDeviceProp, args=(device,{"automation":"enabled"})).start()

                        # TODO: Support proper event logging here.
                        print("Automation triggered {} off and delayed further automation for {}s.".format(device,delay))
                    else:
                        print("Automation request task failed for {} with {}".format(device, response.status))
                except:
                    print("Unable to connect to controller API. Attempting {} more tries...".format(tries))
                    tries = tries - 1
                else:
                    break
        elif prop == "speed":
            time.sleep(10)
        else:
            time.sleep(2)



def AutomationServer(ks):

    if not ks.exists("sensor.data.external"):
        print("ERROR: Missing external sensor data key.")
        return

    if not ks.exists("sensor.data.hydroponic"):
        print("ERROR: Missing hydroponic sensor data key.")
        return

    if not ks.exists("settings.environmental"):
        print("ERROR: Missing settings data key.")
        return

    sensors = ks.hgetall("sensor.data.external")
    hydro   = ks.hgetall("sensor.data.hydroponic")
    settings = ks.hgetall("settings.environmental")

    keyNs = "device.id."
    deviceKeys = ks.keys(keyNs + "*")

    for keyName in deviceKeys:
        deviceId = keyName.split(keyNs)[1] 
        deviceProps = ks.hgetall(keyNs + deviceId)

        if deviceProps["automation"] == "disabled" or deviceProps["mode"] == "manual":
            continue

        if deviceProps["control"] == "relay":
            if deviceProps["type"] == "chiller":
                if int(float(hydro["temp"])) >= int(settings["chill"]) and deviceProps["state"] == "off":
                    print("Water temperature reached chill setting.")
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","on",retries)).start()

                elif int(float(hydro["temp"])) < int(settings["chill"]) and deviceProps["state"] == "on":
                    print("Water temperature dropped below chill setting.")
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","off",retries)).start()

            elif deviceProps["type"] == "cooler":
                if int(float(sensors["temp"])) > int(settings["cool"])+1 and deviceProps["state"] == "off":
                    print("Temperature exceeded cool setting.")
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","on",retries)).start()

                elif int(float(sensors["temp"])) < int(settings["cool"])-1 and deviceProps["state"] == "on":
                    print("Temperature dropped below cool setting.")
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","off",retries)).start()

            elif deviceProps["type"] == "heater":
                if int(float(sensors["temp"])) < int(settings["heat"])-1 and deviceProps["state"] == "off":
                    print("Temperature dropped below heat setting.")
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","on",retries)).start()

                elif int(float(sensors["temp"])) > int(settings["heat"])+1 and deviceProps["state"] == "on":
                    print("Temperature exceeded heat setting.")
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","off",retries)).start()

            elif deviceProps["type"] == "humidifier":
                if int(float(sensors["humidity"])) < int(settings["humidity"])-4 and deviceProps["state"] == "off":
                    print("RH dropped below humidity setting.")
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","on",retries)).start()

                elif int(float(sensors["humidity"])) > int(settings["humidity"])+1 and deviceProps["state"] == "on":
                    print("RH exceeded humidity setting.")
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","off",retries)).start()

            elif deviceProps["type"] == "dehumidifier":
                if int(float(sensors["humidity"])) > int(settings["humidity"])+4 and deviceProps["state"] == "off":
                    print("RH exceeded humidity setting.")
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","on",retries)).start()

                elif int(float(sensors["humidity"])) < int(settings["humidity"])-1 and deviceProps["state"] == "on":
                    print("RH dropped below humidity setting.")
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","off",retries)).start()

            elif deviceProps["type"] == "co2":
                if int(float(sensors["co2"])) < int(settings["co2"])-25 and deviceProps["state"] == "off":
                    print("Co2 dropped below setting.")
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","on",retries)).start()

                elif int(float(sensors["co2"])) > int(settings["co2"])+25 and deviceProps["state"] == "on":
                    print("Co2 exceeded setting.")
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","off",retries)).start()

            elif deviceProps["type"] == "phup":
                if float(hydro["ph"]) < float(settings["ph"])-0.3 and deviceProps["state"] == "off":
                    print("pH dropped below setting.")
                    duration = int(deviceProps.get("on_seconds"))
                    if float(hydro["ph"]) > float(settings["ph"])-0.8:
                        duration = duration/2
                    delay    = int(deviceProps.get("automation_delay"))
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","on",retries,duration,delay)).start()

            elif deviceProps["type"] == "phdown":
                if float(hydro["ph"]) > float(settings["ph"])+0.5 and deviceProps["state"] == "off":
                    print("pH exceeded setting.")
                    duration = int(deviceProps.get("on_seconds"))
                    if float(hydro["ph"]) < float(settings["ph"])+0.8:
                        duration = duration/2
                    delay    = int(deviceProps.get("automation_delay"))
                    threading.Thread(name="relay-"+deviceId, target=setDeviceState, args=(deviceId,"state","on",retries,duration,delay)).start()

        elif deviceProps["control"] == "pwm":
            if deviceProps["type"] == "chiller":
                if int(float(sensors["temp"])) > int(settings["cool"])+1 and int(deviceProps["speed"]) > 0:
                    if int(deviceProps["speed"]) - 25 < 0:
                        speed = 0
                    else:
                        speed = int(deviceProps["speed"]) - 25 

                    tNames = list()
                    for t in threading.enumerate():
                        tNames.append(t.getName())

                    if not "pwm-"+deviceId in tNames and int(deviceProps["speed"]) > 0:
                        print("Temperature exceeds cool setting.")
                        threading.Thread(name="pwm-"+deviceId, target=setDeviceState, args=(deviceId,"speed",speed,retries)).start()

                elif int(float(sensors["temp"])) < int(settings["cool"])-1 and int(deviceProps["speed"]) < 255:
                    if int(deviceProps["speed"]) + 25 > 255:
                        speed = 255
                    else:
                        speed = int(deviceProps["speed"]) + 25 

                    tNames = list()
                    for t in threading.enumerate():
                        tNames.append(t.getName())

                    if not "pwm-"+deviceId in tNames and int(deviceProps["speed"]) < 255:
                        print("Temperature below cool setting.")
                        threading.Thread(name="pwm-"+deviceId, target=setDeviceState, args=(deviceId,"speed",speed,retries)).start()

            elif deviceProps["type"] == "dehumidifier":
                if int(float(sensors["humidity"])) > int(settings["humidity"])+4 and int(deviceProps["speed"]) > 0:
                    if int(deviceProps["speed"]) - 25 < 0:
                        speed = 0
                    else:
                        speed = int(deviceProps["speed"]) - 25 

                    tNames = list()
                    for t in threading.enumerate():
                        tNames.append(t.getName())

                    if not "pwm-"+deviceId in tNames and int(deviceProps["speed"]) < 255:
                        print("RH exceeds humidity setting.")
                        threading.Thread(name="pwm-"+deviceId, target=setDeviceState, args=(deviceId,"speed",speed,retries)).start()

                elif int(float(sensors["humidity"])) < int(settings["humidity"])-1 and int(deviceProps["speed"]) < 255:
                    if int(deviceProps["speed"]) + 25 > 255:
                        speed = 255
                    else:
                        speed = int(deviceProps["speed"]) + 25 

                    tNames = list()
                    for t in threading.enumerate():
                        tNames.append(t.getName())

                    if not "pwm-"+deviceId in tNames and int(deviceProps["speed"]) < 255:
                        print("RH below humidity setting.")
                        threading.Thread(name="pwm-"+deviceId, target=setDeviceState, args=(deviceId,"speed",speed,retries)).start()


if __name__ == '__main__':

    try:
        ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)
    except:
        print("ERROR: Unable to connect to Redis service.")
        exit()

    while True:
        AutomationServer(ks)
        time.sleep(1)

