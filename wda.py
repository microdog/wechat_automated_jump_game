from __future__ import print_function

import json
import time
import random
import base64
import argparse

import requests
import requests.exceptions

CORRECTION_RATIO = 1.025

http = requests.Session()

server_url = None
remote = None
session_id = None

try:
    raw_input
except NameError:
    raw_input = input


def connect():
    global session_id
    print('Connecting...', server_url)
    try:
        status = http.get(server_url + '/status').json()
        session_id = status['sessionId']
        print('Connected', status)
    except requests.exceptions.RequestException:
        print('Failed')
        raise


def main():
    raw_input('Press enter to start')

    while True:
        print('Taking snapshot...')
        img_data = http.get(server_url + '/screenshot').json()['value']
        img_data = base64.b64decode(img_data)

        print('Requesting...', remote)

        try:
            res = http.post(
                url=remote,
                data=img_data,
                headers={
                    'Content-Type': 'application/octet-stream'
                })
        except requests.exceptions.RequestException:
            break

        press_time_raw = float(res.content) / 1000.0
        press_time = press_time_raw * CORRECTION_RATIO
        res.close()

        print('Long press: {}s (raw: {}s)'.format(press_time, press_time_raw))

        x, y = random.randint(400, 500), random.randint(400, 500)

        print('Will tap at {}'.format((x, y)))

        http.post(
            server_url + '/session/' + session_id + '/wda/touchAndHold',
            data=json.dumps({
                'x': x,
                'y': y,
                'duration': press_time
            }),
            headers={
                'Content-Type': 'application/json'
            })

        sleep = 1.75 + 0.75 * random.random()
        print('Sleep {}s'.format(sleep))
        time.sleep(sleep)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--jitter',
        type=float,
        default=None,
        help='if set, press time will be multiplied by a random '
        'value in range [1 - JITTER_FLOAT, 1 + JITTER_FLOAT]')
    parser.add_argument(
        'wda_url', type=str, help='server url of WebDriverAgent')
    parser.add_argument('remote_url', type=str, help='remote server url')

    args = parser.parse_args()
    server_url = args.wda_url
    remote = args.remote_url

    if args.jitter is not None:
        remote += '?' if '?' not in remote else '&'
        remote += 'jitter={}'.format(args.jitter)

    connect()
    main()
