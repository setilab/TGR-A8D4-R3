import os

# Current self
VERSION = "2.01"

# Redis
RHOST = os.getenv("TGR_REDIS_HOST", "172.17.0.1")
RPORT = int(os.getenv("TGR_REDIS_PORT", "6379"))

OCMEP = os.getenv("TGR_OCM_ENDPOINT", "http://172.17.0.1")

STATE_KEY_EXPIRE = int(os.getenv("TGR_RELAY_STATE_KEY_EXPIRATION", "300"))
