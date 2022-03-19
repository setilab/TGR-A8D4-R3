#!/usr/local/bin/python

import os
import time
from datetime import datetime
import threading
import redis
import requests
import random
import string
import re

# Current self
VERSION = "2.0"

# Redis
RHOST = os.getenv("TGR_REDIS_HOST", "172.17.0.1")
RPORT = int(os.getenv("TGR_REDIS_PORT", "6379"))

TGRAPI = os.getenv("TGR_API_ENDPOINT", "http://localhost:8080/api")
device_url = TGRAPI + "/devices/id/"

ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)
ks.config_set('notify-keyspace-events', 'KEA')

timedThreads = {}
thread_pool  = threading.BoundedSemaphore(value=1)

def setDeviceState(name, device, state, blocking, tries):

    with thread_pool:

        if blocking == "no":
            automation = "enabled"
        elif blocking == "yes":
            automation = "disabled"

        if state == None:
            try:
                jsonData = {'automation':automation}
                response = requests.put(device_url + device, json=jsonData)
            except:
                if tries > 0:
                    print("Unable to connect to controller API. Attempting {} more tries...".format(tries))
                    tries = tries - 1
                    threading.Thread(name="t-"+device, target=setDeviceState, args=(name,device,state,blocking,tries)).start()
            else:
                if response.ok:
                    # TODO: Support proper event logging here.
                    print("{} timer enabled automation for {}".format(name, device))
                else:
                    print("{} timer failed request with {}".format(name, response.status))
        else:
            try:
                jsonData = {'state':state,'automation':automation}
                response = requests.post(device_url + device, json=jsonData)
            except:
                if tries > 0:
                    print("Unable to connect to controller API. Attempting {} more tries...".format(tries))
                    tries = tries - 1
                    threading.Thread(name="t-"+device, target=setDeviceState, args=(name,device,state,blocking,tries)).start()
            else:
                if response.ok:
                    # TODO: Support proper event logging here.
                    print("{} timer triggered {} {}".format(name, device, state))
                else:
                    print("{} timer failed request with {}".format(name, response.status))

        time.sleep(2)


def event_handler(msg):

    timer   = msg["channel"].split(":")[1]
    timerId = timer.split("timer.properties.")[1]

    if timerId in timedThreads:
        for device in timedThreads[timerId]:
            print("Cancelling timed thread for {}:{}".format(timerId,device))
            timedThreads[timerId][device].cancel()


def MasterTimer(init):

    if init == 0:
        t = time.localtime()
        newStart = 60 - t.tm_sec
        print(time.ctime())
        print("Synchronizing main timer thread for {}s...".format(newStart))
        t1 = threading.Timer(newStart, MasterTimer, [1])
        t1.start()
        return

    start = time.time()
    
    #ks = redis.Redis(host=RHOST, port=RPORT, db=0, decode_responses=True)

    timers = ks.keys("timer.properties.*")

    if len(timers) == 0:
        #print("No timers are defined.")
        done = time.time()
        newStart = (60 - (done - start))
        t1 = threading.Timer(newStart, MasterTimer, [1])
        t1.start()
        return

    for timer in timers:

        timerProps = ks.hgetall(timer)
        timerId    = timer.split("timer.properties.")[1]

        name     = timerProps["name"]
        devices  = timerProps["devices"]
        hour     = timerProps["hour"]
        min      = timerProps["min"]
        state    = timerProps["state"]
        enabled  = timerProps["enabled"]
        blocking = timerProps["blocking"]

        if enabled == "no":
            continue;

        deviceList = devices.split(",")

        now = time.localtime()

        runNow = False
        runAbort = False
        runDuration = 0

        #
        # Rule 1: Parse formats
        #         hour: */n
        #                 ^- number from set 2,3,4,6,8,12
        #          min: */n
        #                 ^- number from set 2,3,4,5,6,8,10,12,15,20,30
        #
        if re.search("^\*/\d+$", hour) and re.search("^\*/\d+$", min):
            x = re.search("\d+", hour).group()
            y = re.search("\d+", min).group()

            if not int(x) in [ 2,3,4,6,8,12 ]:
                print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(1.0,hour,min,name))
                runAbort = True
                break
            if not int(y) in [ 2,3,4,5,6,8,10,12,15,20,30 ]:
                print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(1.1,hour,min,name))
                runAbort = True
                break

            x = int(x)
            y = int(y)

            if (now.tm_hour / x) % 2 == 0 and now.tm_min % y == 0 and (now.tm_min / y) % 2 == 0:
                runNow = True
            elif (now.tm_hour / x) % 2 == 0 and now.tm_min % y == 0 and (now.tm_min / y) % 2 == 1:
                runNow = True
                if state == "on":
                    state = "off"
                else:
                    state = "on"
            else:
                runAbort = True

        #
        # Rule 2: Parse formats
        #         hour: n-n
        #               ^-^- numbers from range 0-23
        #          min: */n
        #                 ^- number from set 2,3,4,5,6,8,10,12,15,20,30
        #
        if runNow == False and runAbort == False:
            if re.search("^\d+-\d+$", hour) and re.search("^\*/\d+$", min):
                h1,h2 = re.split("-", hour)
                y = re.search("\d+", min).group()

                if not int(h1) in range(0,23) or not int(h2) in range(0,23):
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(2.0,hour,min,name))
                    runAbort = True
                    break
                if not int(y) in [ 2,3,4,5,6,8,10,12,15,20,30 ]:
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(2.1,hour,min,name))
                    runAbort = True
                    break

                h1 = int(h1)
                h2 = int(h2)
                y = int(y)
 
                if h1 < h2:
                    myrange = range(h1,h2)
                elif h1 > h2:
                    l1 = list(range(h1,24))
                    l2 = list(range(0,h2))
                    myrange = l1 + l2
                else:
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(2.2,hour,min,name))
                    runAbort = True
                    break

                if now.tm_hour in myrange and now.tm_min % y == 0 and (now.tm_min / y) % 2 == 0:
                    runNow = True
                elif now.tm_hour in myrange and now.tm_min % y == 0 and (now.tm_min / y) % 2 == 1:
                    runNow = True
                    if state == "on":
                        state = "off"
                    else:
                        state = "on"
                else:
                    runAbort = True

        #
        # Rule 3: Parse formats
        #         hour: */n
        #                 ^- number from set 2,3,4,6,8,12
        #          min: n
        #               ^- number from range 0-59
        #
        if runNow == False and runAbort == False:
            if re.search("^\*/\d+$", hour) and re.search("^\d+$", min):
                x = re.search("\d+", hour).group()

                if not int(x) in [ 2,3,4,6,8,12 ]:
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(3.0,hour,min,name))
                    runAbort = True
                    break
                if not int(min) in range(0,59):
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(3.1,hour,min,name))
                    runAbort = True
                    break

                x = int(x)
                min = int(min)

                if min == now.tm_min:
                    if now.tm_hour % x == 0 and (now.tm_hour / x) % 2 == 0:
                        runNow = True
                    elif now.tm_hour % x == 0 and (now.tm_hour / x) % 2 == 1:
                        runNow = True
                        if state == "on":
                            state = "off"
                        else:
                            state = "on"
                    else:
                        runAbort = True
                else:
                    runAbort = True

        #
        # Rule 4: Parse formats
        #         hour: */n
        #                 ^- number from set 2,3,4,6,8,12
        #          min: n,n
        #               ^- number from range 0-59
        #                 ^- number from range 1-59
        #
        if runNow == False and runAbort == False:
            if re.search("^\*/\d+$", hour) and re.search("^\d+,\d+$", min):
                x = re.search("\d+", hour).group()
                m1,m2 = re.findall("\d+", min)

                if not int(x) in [ 2,3,4,6,8,12 ]:
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(4.0,hour,min,name))
                    runAbort = True
                    break
                if not int(m1) in range(0,59) or not int(m2) in range(1,59):
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(4.1,hour,min,name))
                    runAbort = True
                    break

                x = int(x)
                m1 = int(m1)
                m2 = int(m2)

                if now.tm_hour % x == 0 and m1 == now.tm_min:
                    runNow = True
                    state = "on"
                    runDuration = m2*60
                else:
                    runAbort = True

        #
        # Rule 5: Parse formats
        #         hour: n-n
        #               ^-^- numbers from range 0-23
        #          min: n
        #               ^- number from range 0-59
        #
        if runNow == False and runAbort == False:
            if re.search("^\d+-\d+$", hour) and re.search("^\d+$", min):
                h1,h2 = re.split("-", hour)

                if not int(min) in range(0,59):
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(5.0,hour,min,name))
                    runAbort = True
                    break

                h1  = int(h1)
                h2  = int(h2)
                min = int(min)

                if h1 == h2:
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(5.1,hour,min,name))
                    runAbort = True
                    break

                if (now.tm_hour == h1 or now.tm_hour == h2) and min == now.tm_min:
                    runNow = True
                    if now.tm_hour == h2:
                        if state == "on":
                            state = "off"
                        else:
                            state = "on"
                else:
                    runAbort = True

        # Rule 6: Parse formats
        #         hour: n-n
        #               ^-^- numbers from range 0-23
        #          min: n,n
        #               ^- number from range 0-59
        #                 ^- number from range 1-59
        #
        if runNow == False and runAbort == False:
            if re.search("^\d+-\d+$", hour) and re.search("^\d+,\d+$", min):
                h1,h2 = re.split("-", hour)
                m1,m2 = re.findall("\d+", min)

                if not int(h1) in range(0,23) or not int(h2) in range(0,23):
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(6.0,hour,min,name))
                    runAbort = True
                    break
                if not int(m1) in range(0,59) or not int(m2) in range(1,59):
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(6.1,hour,min,name))
                    runAbort = True
                    break

                h1 = int(h1)
                h2 = int(h2)
                m1 = int(m1)
                m2 = int(m2)

                if h1 < h2:
                    myrange = range(h1,h2)
                elif h1 > h2:
                    l1 = list(range(h1,24))
                    l2 = list(range(0,h2))
                    myrange = l1 + l2
                else:
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(6.2,hour,min,name))
                    runAbort = True
                    break

                if now.tm_hour in myrange and m1 == now.tm_min:
                    runNow = True
                    state = "on"
                    runDuration = m2*60
                else:
                    runAbort = True

        # Rule 7: Parse formats
        #         hour: n-n,*/n
        #               ^-^- numbers from range 0-23
        #                     ^- number from set 2,3,4,6,8,12
        #          min: n,n
        #               ^- number from range 0-59
        #                 ^- number from range 1-59
        #
        if runNow == False and runAbort == False:
            if re.search("^\d+-\d+,\*/\d+$", hour) and re.search("^\d+,\d+$", min):
                h1,h2,x = re.findall("\d+", hour)
                m1,m2   = re.findall("\d+", min)

                if not int(h1) in range(0,23) or not int(h2) in range(0,23):
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(7.0,hour,min,name))
                    runAbort = True
                    break
                if not int(x) in [ 2,3,4,6,8,12 ]:
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(7.1,hour,min,name))
                    runAbort = True
                    break
                if not int(m1) in range(0,59) or not int(m2) in range(1,59):
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(7.2,hour,min,name))
                    runAbort = True
                    break

                h1 = int(h1)
                h2 = int(h2)
                x  = int(x)
                m1 = int(m1)
                m2 = int(m2)

                if h1 < h2:
                    myrange = range(h1,h2)
                elif h1 > h2:
                    l1 = list(range(h1,24))
                    l2 = list(range(0,h2))
                    myrange = l1 + l2
                else:
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(7.3,hour,min,name))
                    runAbort = True
                    break

                if now.tm_hour in myrange and now.tm_hour % x == 0 and m1 == now.tm_min:
                    runNow = True
                    state = "on"
                    runDuration = m2*60
                else:
                    runAbort = True

        #
        #
        # Rule 8: Parse formats
        #         hour: n-n
        #               ^-^- numbers from range 0-23
        #          min: *
        #
        if runNow == False and runAbort == False:
            if re.search("^\d+-\d+$", hour) and re.search("^\*$", min):
                h1,h2 = re.split("-", hour)

                h1 = int(h1)
                h2 = int(h2)

                if h1 < h2:
                    myrange = range(h1,h2)
                elif h1 > h2:
                    l1 = list(range(h1,24))
                    l2 = list(range(0,h2))
                    myrange = l1 + l2
                else:
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(8.0,hour,min,name))
                    runAbort = True
                    break

                if now.tm_hour in myrange and now.tm_min % 2 == 0:
                    runNow = True
                elif now.tm_hour in myrange and now.tm_min % 2 == 1:
                    runNow = True
                    if state == "on":
                        state = "off"
                    else:
                        state = "on"
                else:
                    runAbort = True

        #
        # Rule 9: Parse formats
        #         hour: * or n
        #                    ^- number from range 0-23
        #          min: */n
        #                 ^- number from set 2,3,4,5,6,8,10,12,15,20,30
        #
        if runNow == False and runAbort == False:
            if (re.search("^\*$", hour) or re.search("^\d+$", hour)) and re.search("^\*/\d+$", min):
                y = re.search("\d+", min).group()

                if not hour == "*" and (hour.isdigit() and not int(hour) in range(0,23)):
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(9.0,hour,min,name))
                    runAbort = True
                    break

                y = int(y)

                if hour == "*" or int(hour) == now.tm_hour:
                    if now.tm_min % y == 0 and (now.tm_min / y) % 2 == 0:
                        runNow = True
                    elif now.tm_min % y == 0 and (now.tm_min / y) % 2 == 1:
                        runNow = True
                        if state == "on":
                            state = "off"
                        else:
                            state = "on"
                    else:
                        runAbort = True
                else:
                    runAbort = True

        #
        # Rule 10: Parse formats
        #          hour: * or n
        #                    ^- number from range 0-23
        #           min: *
        #
        if runNow == False and runAbort == False:
            if (re.search("^\*$", hour) or re.search("^\d+$", hour)) and re.search("^\*$", min):

                if not hour == "*" and (hour.isdigit() and not int(hour) in range(0,23)):
                    print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(10.0,hour,min,name))
                    runAbort = True
                    break

                if hour == "*" or int(hour) == now.tm_hour:
                    if now.tm_min % 2 == 0:
                        runNow = True
                    elif now.tm_min % 2 == 1:
                        runNow = True
                        if state == "on":
                            state = "off"
                        else:
                            state = "on"
                    else:
                        runAbort = True
                else:
                    runAbort = True

        #
        # Rule 11: Parse formats
        #          hour: * or n
        #                     ^- number from range 0-23
        #           min: n
        #                ^- number from range 0-59
        #
        if runNow == False and runAbort == False:

            if hour.isdigit() and min.isdigit():
                if int(hour) == int(now.tm_hour) and int(min) == int(now.tm_min):
                    runNow = True
            elif hour == "*" and min.isdigit():
                if int(min) == int(now.tm_min):
                    runNow = True
            else:
                print("Matching rule {}: Invalid specification of {}|{} in timer {}".format(11.0,hour,min,name))


        if runNow == True:

            tries = 3
            for device in deviceList:
                deviceProps = ks.hgetall("device.id." + device)
                if deviceProps["type"] in ["lamp", "timed"] and deviceProps["mode"] == "auto":
                    if deviceProps["control"] == "pwm" and state == "on":
                        _state = deviceProps["speed_max"]
                    elif deviceProps["control"] == "pwm" and state == "off":
                        _state = 255
                    else:
                        _state = state
                    threading.Thread(name="t-"+device, target=setDeviceState, args=(name,device,_state,"yes",tries)).start()
                    if runDuration > 0 and (state == "on" or state == deviceProps["speed_max"]):
                        if state == "on":
                            _state = "off"
                        else:
                            _state = 255
                        if not timerId in timedThreads:
                            timedThreads[timerId] = {}
                        timedThreads[timerId][device] = threading.Timer(runDuration, setDeviceState, args=(name,device,_state,"yes",tries))
                        timedThreads[timerId][device].start()
                else:
                    if state == "on" and deviceProps["mode"] == "auto" and blocking == "when_off":
                        deviceProp = {'automation':'enabled'}
                        ks.hset("device.id." + device, mapping=deviceProp)
                        print("{} timer enabled automation for {}".format(name, device))

                    elif state == "on" and deviceProps["mode"] == "auto" and blocking == "when_on":
                        if deviceProps["control"] == "pwm":
                            _state = deviceProps["speed_max"]
                        else:
                            _state = state
                        threading.Thread(name="t-"+device, target=setDeviceState, args=(name,device,_state,"yes",tries)).start()
                        if runDuration > 0:
                            if not timerId in timedThreads:
                                timedThreads[timerId] = {}
                            timedThreads[timerId][device] = threading.Timer(runDuration, setDeviceState, args=(name,device,None,"no",tries))
                            timedThreads[timerId][device].start()

                    elif state == "off" and deviceProps["mode"] == "auto" and blocking == "when_on":
                        deviceProp = {'automation':'enabled'}
                        ks.hset("device.id." + device, mapping=deviceProp)
                        print("{} timer enabled automation for {}".format(name, device))

                    elif state == "off" and deviceProps["mode"] == "auto" and blocking == "when_off":
                        if deviceProps["control"] == "pwm":
                            _state = 255
                        else:
                            _state = state
                        threading.Thread(name="t-"+device, target=setDeviceState, args=(name,device,_state,"yes",tries)).start()

            runDuration = 0


    done = time.time()
    newStart = (60 - (done - start))
    threading.Timer(newStart, MasterTimer, [1]).start()


if __name__ == '__main__':

    print("Starting timer service.")
    threading.Timer(0.1, MasterTimer, [0]).start()

    pubsub = ks.pubsub()
    pubsub.psubscribe(**{'__keyspace@0__:timer.properties.*': event_handler})
    thread = pubsub.run_in_thread(sleep_time=0.01)

