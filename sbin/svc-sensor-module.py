#!/usr/bin/env python3

"""
Multi-threaded process to simulate a sensor module

Thread #1 simulates real-world environmental data written
to a serial port as if a sensor module were actually
connected.

Thread #2 reads the simulated data off a different serial
port.

"""

from datetime import datetime
import json
import random
import serial
import threading
import time

SPEED = 115200
BYTES = 8
PARITY = 'N'
STOP = 1

sendPort = "/dev/ttyS0"
recvPort = "/dev/ttyS1"

def readSerial(port):

    comPort = serial.Serial(port)
    comPort.baudrate = SPEED
    comPort.bytesize = BYTES
    comPort.parity = PARITY
    comPort.stopbits = STOP

    while True:
        if comPort.isOpen():
            while comPort.inWaiting() == 0: time.sleep(1)
            if comPort.inWaiting() > 0:
                buffer = comPort.readline().decode().strip()
                print(buffer)
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
        while True:
            # Using python's random module, we can simulate
            # (within reason) fluctuating sensor data.
            # TODO: Vary the uniform ranges based upon other
            # (simulated) conditions, such as heat/cold sources
            # or climate controls, etc.
            jsonData = {
                'timestamp':datetime.now().isoformat(timespec='seconds'),
                'climate':
                {
                    'temp':"{0:.1f}".format(random.uniform(72,73)),
                    'humidity':"{0:.1f}".format(random.uniform(39,41)),
                    'co2':"{0:.2f}".format(random.uniform(630,670))
                },
                'water':
                {
                    'temp':"{0:.1f}".format(random.uniform(68,69)),
                    'ph':"{0:.1f}".format(random.uniform(5.6,5.9))
                },
                'lux':f"{int(random.uniform(1682,1690))}"
            }
            # Convert our pseudo-data in Json format to a text
            # string, then into bytes using UTF-8 encoding, then
            # write out on our serial device.
            comPort.write(bytes(json.dumps(jsonData) + "\n", "utf-8"))
            time.sleep(3)


if __name__ == '__main__':

    print("Starting sensor module service.")

    threading.Thread(name="writeSerial", target=writeSerial, args=(sendPort,)).start()
    threading.Thread(name="readSerial", target=readSerial, args=(recvPort,)).start()


