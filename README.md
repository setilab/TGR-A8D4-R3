# TGR-A8D4-R3

The Greenroom Control System 

Model Number TGR-A8D4-R3

This repo contains the code for simulating an IoT controller system which is part of an entire platform that automates controlling greenroom or greenhouse equipment. The platform is comprised of one or more hardware devices (controllers) connected to a cloud-based management service.

Hardware controllers can be multiple main units, with additional add-on units to expand functionality (not implemented yet).

Model TGR-A8D4-R3 consists of the following (some emulated) hardware:

Main Controller
- Raspberry Pi Model 3/4 B+
- Sensor Module (emulated)
  Sensors
  -- Temp/Humidity
  -- Co2
  -- Ambient Light Sensor
- Output/Relay Module (emulated)
  Outputs
  -- 8 120VAC/15A outlets
  -- 4 12VDC output jacks

Software Requirements:

Main Controller
- Raspberry Pi
  -- Raspian Buster or later 64bit
     Packages (not all-inclusive)
     -- Docker
        Container Images
        -- Redis
     -- Cherrypy
