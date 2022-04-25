#!/usr/bin/env python3
import redis

ks = redis.Redis(host="172.17.0.1",port=6379,db=0,decode_responses=True)

ks.hset('controller.properties', mapping={'serialnum': '00000000-0000-0000-0000-000000000000', 'modelnum': 'TGR-A8D4-R3'})

ks.sadd('device.pwm.icons', 'timed', 'spare', 'cooler', 'fan', 'dehumidifier')
ks.sadd('device.pwm.types', 'timed', 'spare', 'cooler', 'fan', 'dehumidifier')
ks.sadd('device.relay.icons', 'pump', 'timed', 'humidifier', 'spare', 'airpump', 'cooler', 'heater', 'chiller', 'fan', 'lamp', 'dehumidifier', 'co2')
ks.sadd('device.relay.types', 'pump', 'timed', 'humidifier', 'spare', 'cooler', 'heater', 'chiller', 'fan', 'lamp', 'dehumidifier', 'co2')

ks.hset('settings.controller', mapping={'manual': 'off'})
ks.hset('settings.environmental', mapping={'cool': '71', 'heat': '65', 'humidity': '40', 'co2': '1500', 'ph': '5.8', 'chill':'65'})
ks.hset('settings.controller.defaults', mapping={'manual': 'off'})
ks.hset('settings.environmental.defaults', mapping={'cool': '72', 'heat': '65', 'humidity': '40', 'co2': '1200', 'ph': '5.8', 'chill':'65'})

