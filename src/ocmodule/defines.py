import os

# Current self
VERSION = "1.00"

ip   = os.getenv("TGR_MSGSVC_UDP_ADDR", "192.168.254.3")
port = int(os.getenv("TGR_MSGSVC_UDP_PORT", "63000"))

fans = [
    {"id":"fan1","label":"fan 1","speed":"255"},
    {"id":"fan2","label":"fan 2","speed":"255"}
]

fanIds = [
    "fan1",
    "fan2"
]

relays = [
    {"id":"acrl1","label":"outlet 1","output":"120VAC","state":"off"},
    {"id":"acrl2","label":"outlet 2","output":"120VAC","state":"off"},
    {"id":"acrl3","label":"outlet 3","output":"120VAC","state":"off"},
    {"id":"acrl4","label":"outlet 4","output":"120VAC","state":"off"},
    {"id":"acrl5","label":"outlet 5","output":"120VAC","state":"off"},
    {"id":"acrl6","label":"outlet 6","output":"120VAC","state":"off"},
    {"id":"acrl7","label":"outlet 7","output":"120VAC","state":"off"},
    {"id":"acrl8","label":"outlet 8","output":"120VAC","state":"off"},
    {"id":"dcrl1","label":"jack 1","output":"12VDC","state":"off"},
    {"id":"dcrl2","label":"jack 2","output":"12VDC","state":"off"},
    {"id":"dcrl3","label":"jack 3","output":"12VDC","state":"off"},
    {"id":"dcrl4","label":"jack 4","output":"12VDC","state":"off"}
]

relayIds = [
    "acrl1",
    "acrl2",
    "acrl3",
    "acrl4",
    "acrl5",
    "acrl6",
    "acrl7",
    "acrl8",
    "dcrl1",
    "dcrl2",
    "dcrl3",
    "dcrl4"
]
