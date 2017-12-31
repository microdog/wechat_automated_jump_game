import random
import urllib2
import sys
import subprocess
import signal

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice, MonkeyView

if len(sys.argv) != 3:
    print 'usage: monkeyrunner %s deviceId remoteUri' % sys.argv[0]
    sys.exit(1)

deviceId = sys.argv[1]
remote = sys.argv[2]

print 'Connecting', deviceId

device = MonkeyRunner.waitForConnection(timeout=60, deviceId=deviceId)

print 'Connected'


def main():
    raw_input('Press enter to start')

    while True:
        print 'Taking snapshot...'
        snapshot = device.takeSnapshot()
        img_data = snapshot.convertToBytes('png')

        print 'Requesting...', remote
        req = urllib2.Request(remote, img_data)
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
            "adb -s %s shell kill -9 $(adb -s %s shell ps | grep monkey | awk '{print $2}')" % (deviceId, deviceId),
            shell=True)
    except Exception, e:
        print e
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_handler)
    main()
