from __future__ import print_function

import json
import time
import random
import sys
import base64

import requests
import requests.exceptions

CORRECTION_RATIO = 1.025

http = requests.Session()

serverUrl = sys.argv[1]
remote = sys.argv[2]
sessionId = None

print('Connecting...', serverUrl)

try:
    status = http.get(serverUrl + '/status').json()
    sessionId = status['sessionId']
    print('Connected', status)
except requests.exceptions.RequestException:
    print('Failed')
    raise

raw_input('Press enter to start')

while True:
    print('Taking snapshot...')
    img_data = http.get(serverUrl + '/screenshot').json()['value']
    img_data = base64.b64decode(img_data)

    print('Requesting...', remote)

    try:
        res = http.post(url=remote, data=img_data, headers={
            'Content-Type': 'application/octet-stream'
        })
    except requests.exceptions.RequestException:
        break

    sleep = float(res.content) / 1000.0 * CORRECTION_RATIO
    res.close()

    print('Long press: %ss' % sleep)

    x, y = random.randint(400, 500), random.randint(400, 500)

    print('Will tap at (%s, %s)' % (x, y))

    http.post(serverUrl + '/session/' + sessionId + '/wda/touchAndHold', data=json.dumps({
        'x': x,
        'y': y,
        'duration': sleep
    }), headers={
        'Content-Type': 'application/json'
    })

    time.sleep(1.75)
