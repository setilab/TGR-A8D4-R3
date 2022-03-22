import os

# Current self
VERSION = "1.00"

ip   = os.getenv("TGR_MSGSVC_UDP_ADDR", "192.168.254.3")
port = int(os.getenv("TGR_MSGSVC_UDP_PORT", "63000"))


