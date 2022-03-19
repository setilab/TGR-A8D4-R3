#!/usr/bin/env python
import os
import requests
import json

# QuestDB
QDBEP   = os.getenv("TGR_QDB_ENDPOINT", "http://localhost:9002")
qdb_url = QDBEP + "/exec"

qtd = {}

query = """CREATE TABLE grow_sensors
(ts TIMESTAMP, intemp SHORT, inrh SHORT, extemp SHORT, 
 exrh SHORT, exco2 LONG, exlux SHORT, exdp SHORT, 
 exprs LONG, exesp LONG, wtemp SHORT, wph FLOAT) 
timestamp(ts) 
PARTITION BY day;"""

qtd["grow_sensors"] = query

query = """CREATE TABLE grow_devices
(ts TIMESTAMP,
 deviceid SYMBOL,
 name SYMBOL,
 state SYMBOL,
 mode SYMBOL)
timestamp(ts) 
PARTITION BY day;"""

qtd["grow_devices"] = query

query = """CREATE TABLE grow_tasks
(ts TIMESTAMP,
task SYMBOL)
timestamp(ts) 
PARTITION BY month;"""

qtd["grow_tasks"] = query

query = """CREATE TABLE growroom_tasks
(ts TIMESTAMP,
task SYMBOL)
timestamp(ts) 
PARTITION BY month;"""

qtd["growroom_tasks"] = query

query = """CREATE TABLE grow_notes
(ts TIMESTAMP, note STRING)
timestamp(ts)
PARTITION BY month;"""

qtd["grow_notes"] = query

query = """CREATE TABLE events
(ts TIMESTAMP,
evtype SYMBOL,
evsource SYMBOL,
event STRING)
timestamp(ts) 
PARTITION BY day;"""

qtd["events"] = query

for t in qtd:
    data = "?query=" + qtd[t]
    resp = requests.get(qdb_url + data)

    if not resp.ok:
        print("ERROR: Cannot create {} table within QuestDB service.".format(t))
    else:
        jsonData = json.loads(resp.text.strip('\n'))
        if not jsonData["ddl"] == "OK":
            print("ERROR: {}".format(jsonData))

