#!/usr/bin/env python

import requests
import os

infile     = "dashboard.js"
outfile    = "dashboard.min.js"
script_dir = "/home/pi/tgr/console/public/js/"
url        = "https://closure-compiler.appspot.com/compile"
headers    = {"Content-type":"application/x-www-form-urlencoded"}

try:
    f = open(script_dir + infile)
except:
    print("Unable to open {} for reading.".format(filename))
    exit()

js = f.read()

data  = {"compilation_level":"SIMPLE_OPTIMIZATIONS",
         #"output_file_name":"dashboard.js",
         "output_format":"text",
         "output_info":"compiled_code",
         #"output_info":"errors",
         #"output_info":"warnings",
         #"output_info":"statistics",
         "js_code":js
        }

try:
    resp = requests.post(url, data=data, headers=headers)
except:
    print("Unable to connect to compiler service: {}".format(url))
    exit()
else:
    if resp.ok:
        script_file = os.path.normpath(os.path.join(script_dir, outfile))

        with open(script_file, 'w') as out:
            out.write(resp.text)

