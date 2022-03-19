#!/usr/bin/env python
import redis

ks = redis.Redis(host="172.17.0.1",port=6379,db=0,decode_responses=True)

ks.set("alarm.source.lowtemp","no")
ks.set("alarm.source.hightemp","no")
ks.set("alarm.source.lowrh","no")
ks.set("alarm.source.highrh","no")
ks.set("alarm.source.lowco2","no")
ks.set("alarm.source.highco2","no")
ks.set("alarm.source.lowlux","no")
ks.set("alarm.source.highlux","no")
ks.hset("alarm.state", mapping={'active':'no','silence':'no'})

ks.hset('console.login.creds', mapping={'admin': 'thegreenroom'})

ks.hset('controller.properties', mapping={'serialnum': '371bcb55-61e0-492e-b40d-1292e0096352', 'modelnum': 'TGR-A8D4-TPL-R1', 'cloudsvcid': '52c6aa1e-a0ff-45e5-a875-66f1d642a2af', 'tftui': '1.25', 'name': '4x6 Grow Room', 'growspace': 'indoor', 'usage': 'combo'})

ks.sadd('device.pwm.icons', 'timed', 'spare', 'cooler', 'fan', 'dehumidifier')
ks.sadd('device.pwm.types', 'timed', 'spare', 'cooler', 'fan', 'dehumidifier')
ks.sadd('device.relay.icons', 'pump', 'timed', 'humidifier', 'spare', 'airpump', 'cooler', 'heater', 'chiller', 'fan', 'lamp', 'dehumidifier', 'co2')
ks.sadd('device.relay.types', 'pump', 'timed', 'humidifier', 'spare', 'cooler', 'heater', 'chiller', 'fan', 'lamp', 'dehumidifier', 'co2')

ks.sadd('grow.resource.growspaces', 'outdoor', 'indoor', 'greenhouse')
ks.sadd('grow.resource.usages', 'veg', 'mother', 'flower', 'clone', 'combo')
ks.sadd('grow.resource.lighting', 'ceramic metal halide (cmh/lec)', 'metal halide (mh)', 'double-ended metal halide (d-mh)', 'led', 'double-ended high pressure sodium (d-hps)', 'high pressure sodium (hps)', 'flourescent')
ks.sadd('grow.resource.mediums', 'clay pellets', 'vermiculite', 'aeroponic', 'coco coir', 'soil', 'hydroponic', 'soilless', 'dwc', 'perlite', 'rockwool')

ks.hset('preset.id.7Fea16fB', mapping={'name': 'Day Flower', 'filename': '7Fea16fB.conf'})
ks.hset('preset.id.acBb325f', mapping={'name': 'Night Veg', 'filename': 'acBb325f.conf'})
ks.hset('preset.id.A7Fb5C90', mapping={'name': 'Day Veg', 'filename': 'A7Fb5C90.conf'})
ks.hset('preset.id.1dcB8Cfb', mapping={'name': 'Farmer Night Veg', 'filename': '1dcB8Cfb.conf'})
ks.hset('preset.id.eb47CcEF', mapping={'name': 'Night Flower', 'filename': 'eb47CcEF.conf'})

ks.hset('settings.controller', mapping={'manual': 'off'})
ks.hset('settings.environmental', mapping={'cool': '71', 'heat': '65', 'humidity': '40', 'co2': '1500', 'ph': '5.8', 'chill':'65'})
ks.hset('settings.alarm', mapping={'lowtemp': '55', 'hightemp': '80', 'lowrh': '25', 'highrh': '65', 'lowco2': '300', 'highco2': '2000', 'lowlux': '1000', 'highlux': '10', 'lowph': '5.5', 'highph': '7.0', 'lowchill':'62','highchill':'72'})
ks.hset('settings.controller.defaults', mapping={'manual': 'off'})
ks.hset('settings.environmental.defaults', mapping={'cool': '72', 'heat': '65', 'humidity': '40', 'co2': '1200', 'ph': '5.8', 'chill':'65'})
ks.hset('settings.alarm.defaults', mapping={'lowtemp': '55', 'hightemp': '80', 'lowrh': '30', 'highrh': '60', 'lowco2': '600', 'highco2': '2000', 'lowlux': '2000', 'highlux': '10', 'lowph': '5.5', 'highph': '7.0', 'lowchill':'62','highchill':'72'})

ks.hset('tasks.types.grow', mapping={'3d1fcDF5': 'water change', 'FDE4a5e2': 'alter nutrients', 'BCA84750': 'prune', 'D174e23C': 'defoliate', 'F6AB2a53': 'treat insects', '6f2FE74B': 'treat algae', 'Dfcead92': 'fill pH down reservoir', '45b0e6dC': 'fill pH up reservoir', ' EDBf614c': 'fill top-off tank', '5da39AcC': 'fill humidifier tank'})
ks.hset('tasks.types.growroom', mapping={'aA754cEb': 'change bulb', 'eAaF5D62': 'change filter', '2d46cD57': 'replace carbon filter', '03Eb92BC': 'replace water pump', '6cF5fe9C': 'calibrate pH probe'})
