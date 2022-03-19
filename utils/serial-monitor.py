#!/usr/local/bin/python

from datetime import datetime,timedelta
import time
import os
import serial
import redis
import requests

# Current self
VERSION = "1.05"

# Serial device config
SERIAL_SPEED    = 115200
SERIAL_BYTESIZE = 8
SERIAL_PARITY   = 'N'
SERIAL_STOPBITS = 1

def serialRead(comPort):

    serialErrorCount = 0

    while True:
        try:
            data = comPort.readline().decode().strip()
        except KeyboardInterrupt:
            exit()
        except:
            serialErrorCount += 1
            print("Error with serial port.")

            if serialErrorCount > 10:
                return
        else:
            print("{}: {}".format(datetime.now(),data))


if __name__ == '__main__':

    port = "/dev/ttyACM1"
    try:
        comPort = serial.Serial(port)
    except:
        print("Error opening serial port: {}".format(port))
    else:
        comPort.baudrate = SERIAL_SPEED
        comPort.bytesize = SERIAL_BYTESIZE
        comPort.parity   = SERIAL_PARITY
        comPort.stopbits = SERIAL_STOPBITS

        print("Found microcontroller on serial port: {}".format(port))

    serialRead(comPort)
