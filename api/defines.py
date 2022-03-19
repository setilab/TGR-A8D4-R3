import os

# Current self
VERSION = "2.00"

# Redis
RHOST = os.getenv("TGR_REDIS_HOST", "172.17.0.1")
RPORT = int(os.getenv("TGR_REDIS_PORT", "6379"))

# QuestDB via Postgres Wire Protocol
PGHOST   =     os.getenv("TGR_QUESTDB_HOST", "localhost")
PGPORT   =     os.getenv("TGR_QUESTDB_PORT", "8812")
PGDBNAME =     os.getenv("TGR_QUESTDB_DBNAME", "qdb")
PGUSER   =     os.getenv("TGR_QUESTDB_USER", "admin")
PGPWD    =     os.getenv("TGR_QUESTDB_PASSWORD", "quest")

qdConnectStr = "host=" + PGHOST + " port=" + PGPORT + " dbname=" + PGDBNAME + " user=" + PGUSER + " password=" + PGPWD

OCMEP = os.getenv("TGR_OCM_ENDPOINT", "http://ocmodule")
TPLEP = os.getenv("TGR_TPL_ENDPOINT", "http://tplconnect:8080")

IMAGE_UPLOAD_DIR = os.getenv("TGR_IMAGE_UPLOAD_DIR", "/home/pi/tgr/www/upload/")
PRESET_DIR       = os.getenv("TGR_PRESETS_DIR", "/home/pi/tgr/data/")
STATE_KEY_EXPIRE = int(os.getenv("TGR_RELAY_STATE_KEY_EXPIRATION", "300"))
