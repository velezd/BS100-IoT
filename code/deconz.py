import ujson
import usocket
import system
import time
import colors
from display import Display


class REST():
    """ Cut down urequests for the purposes of interacting with lights using deCONZ REST API """

    def __init__(self, method, url, data=None):
        self.data = data
        self.method = method
        self.s = None
        port = 80

        _, _, self.host, self.path = url.split("/", 3)

        ai = usocket.getaddrinfo(self.host, port, 0, usocket.SOCK_STREAM)
        self.ai = ai[0]

    def __enter__(self):
        self.s = usocket.socket(self.ai[0], usocket.SOCK_STREAM, self.ai[2])
        self.s.settimeout(2.0)
        self.s.connect(self.ai[-1])

        # Send headers
        self.s.write(b"%s /%s HTTP/1.0\r\n" % (self.method, self.path))
        self.s.write(b"Host: %s\r\n" % self.host)

        if self.data:
            self.data = ujson.dumps(self.data)
            self.s.write(b"Content-Type: application/json\r\n")
            self.s.write(b"Content-Length: %d\r\n" % len(self.data))
        self.s.write(b"Connection: close\r\n\r\n")

        # Send data
        if self.data:
            self.s.write(self.data)

        # Read response headers
        l = self.s.readline()
        l = l.split(None, 2)
        if len(l) < 2:
            # Invalid response
            raise ValueError("HTTP error: BadStatusLine:\n%s" % l)
        status = int(l[1])
        while True:
            l = self.s.readline()
            if not l or l == b"\r\n":
                break
            if l.startswith(b"Transfer-Encoding:"):
                if b"chunked" in l:
                    raise ValueError("Unsupported " + str(l, "utf-8"))

        # Read response data
        d = bytes()
        try:
            while True:
                d += self.s.read(1)
        except OSError as e:
            if e.errno != 116: # ETIMEDOUT
                raise
        d = ujson.loads(d)

        return (status, d)

    def __exit__(self, type, value, traceback):
        if self.s is not None:
            self.s.close()


class Light():
    def __init__(self, id, url, d):
        self.id = id
        self.url = f'{url}/{id}'
        self.name = d['name']
        self.color = d['hascolor']
        self.ct_range = None
        self.state = {} # Not the same as light state in deconz
        if 'ctmin' in d:
            self.ct_range = (d['ctmin'], d['ctmax'])
        self._update(d['state'])

    def set_state(self, d):
        """ Sends new state to deconz light and calls get_state to update local state """
        s = False
        with REST('PUT', f'{self.url}/state', d) as r:
            if r[0] == 200:
                self.get_state()
                s = True
            else:
                print(r)
        return s

    def get_state(self):
        """ Update state of light from deconz """
        try:
            with REST('GET', self.url) as response:
                self._update(response[1]['state'])
            return True
        except Exception as e:
            print(e)
            return False

    def set_ctemp(self):
        self.set_state({'on': True, 'ct': self.state['ct']})

    def set_color(self):
        xy = colors.hsv2xy(self.state['hue'], self.state['sat'], self.state['bri'])
        self.set_state({'on': True, 'xy': xy, 'bri': self.state['bri']})

    def _update(self, s):
        if 'xy' in s:
            h, s, v = colors.xyb2hsv(s['xy'][0], s['xy'][1], s['bri'])
        else:
            h, s, v = None, None, None
        self.state = {'on': s['on'],
                      'mode': s.get('colormode'),
                      'ct': s.get('ct'),
                      'bri': v,
                      'hue': h,
                      'sat': s}
                      #'xy': s.get('xy')}

#   def update_state(self, d):
#       s = False
#       with REST('PUT', f'{self.url}/state', d) as r:
#           if r[0] == 200:
#               self.get_state()
#               s = True
#           else:
#               print(r)
#       return s
#
#   def on(self):
#       return self.update_state({'on': True})
#
#   def off(self):
#       return self.update_state({'on': False})


class Deconz():
    def __init__(self):
        self._url = 'http://homeassistant.lan/api'
        self._user = '3CB8819D1B'
        self.url = f'{self._url}/{self._user}/lights'
        self.lights = []
        self.get_lights()

    def get_lights(self):
        self.lights = []
        try:
            with REST('GET', self.url) as r:
                d = r[1]
                for l in d.keys():
                    if 'on' not in d[l]['state'].keys():
                        continue
                    self.lights.append(Light(l, self.url, d[l]))

            return True
        except Exception as e:
            print(e)
            return False


d = Display()
#system.start_wifi(d)

import colors

print('Init deconz')
deconz = Deconz()

for l in deconz.lights:
    print(f'{l.id} - {l.name}')