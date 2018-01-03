import random
import urllib2
import sys
import subprocess
import signal

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice, MonkeyView

device_id = None
remote_url = None


def connect():
    print 'Connecting', device_id
    device = MonkeyRunner.waitForConnection(timeout=60, deviceId=device_id)
    print 'Connected'
    return device


def main(device):
    raw_input('Press enter to start')

    while True:
        print 'Taking snapshot...'
        snapshot = device.takeSnapshot()
        img_data = snapshot.convertToBytes('png')

        print 'Requesting...', remote_url
        req = urllib2.Request(remote_url, img_data)
        req.add_header('Content-Length', str(len(img_data)))
        req.add_header('Content-Type', 'application/octet-stream')
        try:
            res = urllib2.urlopen(req)
        except urllib2.HTTPError:
            break
        sleep = float(res.read()) / 1000.0
        res.close()

        print 'Long press: %ss' % sleep

        start = (random.randint(400, 600), random.randint(400, 600))
        end = (random.randint(400, 600), random.randint(400, 600))

        print 'Will drag from %s to %s' % (start, end)

        device.drag(start, end, sleep, 2)

        MonkeyRunner.sleep(1.75)


def exit_handler(signum, frame):
    print 'Exiting...'
    try:
        subprocess.call(
            "adb -s %s shell kill -9 $(adb -s %s shell ps | grep monkey | awk '{print $2}')"
            % (device_id, device_id),
            shell=True)
    except Exception, e:
        print e
    sys.exit(0)


def parse_args():
    """Jython does not provide argparse package, parse arguments by hand."""

    def usage(error=None):
        if error is not None:
            print error
            print ''

        print 'usage: monkeyrunner monkeyrunner.py [-h] [--jitter JITTER_FLOAT]'
        print '                                    DEVICE_ID REMOTE_URL'
        print ''
        print 'arguments:'
        print '  DEVICE_ID     target device id'
        print '  REMOTE_URL    remote server url'
        print ''
        print 'optional arguments:'
        print '  -h, --help    show this help message and exit'
        print '  --jitter JITTER_FLOAT'
        print '                press time will be multiplied by a random value'
        print '                in range [1 - JITTER_FLOAT, 1 + JITTER_FLOAT]'

        sys.exit(1 if error is not None else 0)

    argv = sys.argv[1:]

    if '-h' in argv or '--help' in argv:
        usage()

    jitter = None
    if '--jitter' in argv:
        jitter_idx = argv.index('--jitter')
        if jitter_idx == len(argv) - 1:
            usage('--jitter expects a float number')
        try:
            jitter = float(argv[jitter_idx + 1])
        except ValueError:
            usage('--jitter expects a float number, %r got\n' %
                  (argv[jitter_idx + 1], ))
        del argv[jitter_idx:jitter_idx + 2]

    if len(argv) != 2:
        usage('missing arguments')

    device_id, remote_url = argv

    return {'jitter': jitter, 'device_id': device_id, 'remote_url': remote_url}


if __name__ == '__main__':
    args = parse_args()
    device_id = args['device_id']
    remote_url = args['remote_url']

    print 'Device id:', device_id
    print 'Remote url:', remote_url

    if args['jitter']:
        remote_url += '?' if '?' not in remote_url else '&'
        remote_url += 'jitter=%s' % (args['jitter'], )

    signal.signal(signal.SIGINT, exit_handler)

    device = connect()
    main(device)
