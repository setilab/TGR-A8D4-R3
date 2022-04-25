#!/usr/bin/env python3

"""
Multi-threaded process to simulate a sensor module

Thread #1 simulates real-world environmental data written
to a serial port as if a sensor module were actually
connected.

Thread #2 reads the simulated data off a different serial
port, then populates Redis keys.

"""

from datetime import datetime
import json
import os
import random
import redis
import serial
import threading
import time

# Redis
RHOST = os.getenv("TGR_REDIS_HOST", "172.17.0.1")
RPORT = int(os.getenv("TGR_REDIS_PORT", "6379"))
RDB   = int(os.getenv("TGR_REDIS_DB", "0"))

SPEED = 115200
BYTES = 8
PARITY = 'N'
STOP = 1

sendPort = "/dev/ttyS0"
recvPort = "/dev/ttyS1"

def readSerial(port):

    try:
        ks = redis.Redis(host=RHOST, port=RPORT, db=RDB, decode_responses=True)
    except:
        print("Error connecting to Redis server.")
        return

    comPort = serial.Serial(port)
    comPort.baudrate = SPEED
    comPort.bytesize = BYTES
    comPort.parity = PARITY
    comPort.stopbits = STOP

    while True:
        if comPort.isOpen():
            while comPort.inWaiting() == 0: time.sleep(1)
            if comPort.inWaiting() > 0:
                data = comPort.readline().decode().strip()
                try:
                    jsonData = json.loads(data)
                except:
                    print(f"Malformed json data: {data}")
                else:
                    #print("Received: {}".format(jsonData))
                    if "system" in jsonData:
                        systemData = jsonData["system"]
                        if "boot" in systemData:
                            bootData = systemData["boot"]
                            bootData["serialport"] = comPort.port
                            ks.hset("sensor.module.properties", mapping=bootData)
                        elif "sensor" in systemData:
                            if "type" in systemData["sensor"]:
                                if not ks.sismember("sensor.module.sensors", systemData["sensor"]["type"]):
                                    ks.sadd("sensor.module.sensors", systemData["sensor"]["type"])
                                    key = "sensor.module.sensor." + systemData["sensor"]["type"]
                                    del systemData["sensor"]["type"]
                                    ks.hset(key, mapping=systemData["sensor"])
                            elif "units" in systemData["sensor"]:
                                standard = systemData["sensor"]["units"]["standard"]
                                del systemData["sensor"]["units"]["standard"]
                                ks.set("sensor.module.unit", standard)
                                ks.hset("sensor.module.unit." + standard, mapping=systemData["sensor"]["units"])

                        elif "error" in systemData:
                            print("Sensor module error: " + systemData["error"])

                    elif "sensors" in jsonData:
                        ts = datetime.now().isoformat(timespec='seconds')

                        rawData = jsonData["sensors"]["internal"]
                        sensorData = {}
                        sensorData["timestamp"] = ts
                        sensorData["temp"] = int(float(rawData["temp"]))
                        sensorData["humidity"] = int(float(rawData["humidity"]))
                        ks.hset("sensor.data.internal", mapping=sensorData)

                        rawData = jsonData["sensors"]["external"]
                        sensorData = {}
                        sensorData["timestamp"] = ts
                        sensorData["temp"] = int(float(rawData["temp"]))
                        sensorData["humidity"] = int(float(rawData["humidity"]))
                        sensorData["co2"] = int(float(rawData["co2"]))
                        sensorData["lux"] = int(float(rawData["lux"]))
                        ks.hset("sensor.data.external", mapping=sensorData)

                        rawData = jsonData["sensors"]["hydroponic"]
                        sensorData = {}
                        sensorData["timestamp"] = ts
                        sensorData["temp"] = int(float(rawData["temp"]))
                        sensorData["ph"] = int(float(rawData["ph"]))
                        ks.hset("sensor.data.hydroponic", mapping=sensorData)

        else:
            print("Waiting on com port...")
            time.sleep(1)


def writeSerial(port):

    comPort = serial.Serial(port)
    comPort.baudrate = SPEED
    comPort.bytesize = BYTES
    comPort.parity = PARITY
    comPort.stopbits = STOP

    if comPort.isOpen():

        jsonData = {
            'system':
            {
                'boot':
                {
                    'board': 'Arduino Uno',
                    'code_version': '1.01',
                    'ide': '10607',
                    'build': '7.3.0',
                    'date': 'Jan 24 2022 07:17:48'
                }
            }
        }
        comPort.write(bytes(json.dumps(jsonData) + "\n", "utf-8"))
        time.sleep(1)

        jsonData = {
            'system':
            {
                'sensor':
                {
                    'zone': 'internal',
                    'type': 'DHT22',
                    'capability': 'temp,humidity'
                }
            }
        }
        comPort.write(bytes(json.dumps(jsonData) + "\n", "utf-8"))
        time.sleep(1)

        jsonData = {
            'system':
            {
                'sensor':
                {
                    'zone': 'external',
                    'type': 'BME280',
                    'capability': 'temp,humidity,pressure'
                }
            }
        }
        comPort.write(bytes(json.dumps(jsonData) + "\n", "utf-8"))
        time.sleep(1)

        jsonData = {
            'system':
            {
                'sensor':
                {
                    'zone': 'external',
                    'type': 'VEML7700',
                    'capability': 'ambient light'
                }
            }
        }
        comPort.write(bytes(json.dumps(jsonData) + "\n", "utf-8"))
        time.sleep(1)

        jsonData = {
            'system':
            {
                'sensor':
                {
                    'zone': 'external',
                    'type': 'SEN0219',
                    'capability': 'co2'
                }
            }
        }
        comPort.write(bytes(json.dumps(jsonData) + "\n", "utf-8"))
        time.sleep(1)

        jsonData = {
            'system':
            {
                'sensor':
                {
                    'zone': 'hydroponic',
                    'type': 'DS18S20',
                    'capability': 'temp'
                }
            }
        }
        comPort.write(bytes(json.dumps(jsonData) + "\n", "utf-8"))
        time.sleep(1)

        jsonData = {
            'system':
            {
                'sensor':
                {
                    'zone': 'hydroponic',
                    'type': 'SEN0161-V2',
                    'capability': 'ph'
                }
            }
        }
        comPort.write(bytes(json.dumps(jsonData) + "\n", "utf-8"))
        time.sleep(1)

        jsonData = {
            'system':
            {
                'sensor':
                {
                    'units':
                    {
                        'standard': 'us',
                        'temp': 'F',
                        'humidity': '%',
                        'dewpoint': 'F',
                        'altitude': 'ft',
                        'co2': 'ppm',
                        'lux': 'lux'
                    }
                }
            }
        }
        comPort.write(bytes(json.dumps(jsonData) + "\n", "utf-8"))
        time.sleep(1)

        extTRange = ['72','73']
        extRHRange = ['39','41']
        extCo2Range = ['630','670']
        extLuxRange = ['10','13']
        h2oTRange = ['72','73']
        h2oPHRange = ['39','41']

        try:
            ks = redis.Redis(host=RHOST, port=RPORT, db=RDB, decode_responses=True)
        except:
            pass

        while True:
            # Using python's random module, we can simulate
            # (within reason) fluctuating sensor data.

            # Vary the uniform ranges based upon other
            # (simulated) conditions, such as heat/cold sources
            # or climate controls, etc.
            try:
                if ks.exists("sensor.sim.ext.temp"):
                    extTRange = list(ks.smembers("sensor.sim.ext.temp"))
            except:
                pass

            try:
                if ks.exists("sensor.sim.ext.humidity"):
                    extRHRange = list(ks.smembers("sensor.sim.ext.humidity"))
            except:
                pass

            try:
                if ks.exists("sensor.sim.ext.co2"):
                    extCo2Range = list(ks.smembers("sensor.sim.ext.co2"))
            except:
                pass

            try:
                if ks.exists("sensor.sim.ext.lux"):
                    extLuxRange = list(ks.smembers("sensor.sim.ext.lux"))
            except:
                pass

            try:
                if ks.exists("sensor.sim.hydro.temp"):
                    h2oTRange = list(ks.smembers("sensor.sim.hydro.temp"))
            except:
                pass

            try:
                if ks.exists("sensor.sim.hydro.ph"):
                    h2oPHRange = list(ks.smembers("sensor.sim.hydro.ph"))
            except:
                pass

            jsonData = {
                'sensors':
                {
                    'internal':
                    {
                        'temp':"{0:.1f}".format(random.uniform(72,73)),
                        'humidity':"{0:.1f}".format(random.uniform(39,41))
                    },
                    'external':
                    {
                        'temp':"{0:.1f}".format(random.uniform(int(extTRange[0]),int(extTRange[1]))),
                        'humidity':"{0:.1f}".format(random.uniform(int(extRHRange[0]),int(extRHRange[1]))),
                        'co2':"{0:.2f}".format(random.uniform(int(extCo2Range[0]),int(extCo2Range[1]))),
                        'lux':f"{int(random.uniform(int(extLuxRange[0]),int(extLuxRange[1])))}"
                    },
                    'hydroponic':
                    {
                        'temp':"{0:.1f}".format(random.uniform(int(h2oTRange[0]),int(h2oTRange[1]))),
                        'ph':"{0:.1f}".format(random.uniform(int(h2oPHRange[0]),int(h2oPHRange[1])))
                    }
                }
            }
            # Convert our pseudo-data in Json format to a text
            # string, then into bytes using UTF-8 encoding, then
            # write out on our serial device.
            comPort.write(bytes(json.dumps(jsonData) + "\n", "utf-8"))
            time.sleep(5)


if __name__ == '__main__':

    print("Starting sensor module service.")

    threading.Thread(name="readSerial", target=readSerial, args=(recvPort,)).start()
    threading.Thread(name="writeSerial", target=writeSerial, args=(sendPort,)).start()


