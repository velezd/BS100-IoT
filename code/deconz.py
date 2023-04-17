import ujson
import usocket
from math import pow, floor


def hsv2rgb(h, s, v):
    """ HS 0.0-1.0, V 0-255 -> RGB 0-255 """
    if s == 0.0:
        return v, v, v

    i = int(h*6.0) # XXX assume int() truncates!
    f = (h*6.0) - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0-f))
    i = i%6

    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q


def rgb2hsv(r, g, b):
    """ RGB 0-255 -> HS 0.0-1.0, V 0-255"""
    maxc = max(r, g, b)
    minc = min(r, g, b)
    rangec = (maxc-minc)
    v = maxc

    if minc == maxc:
        return 0.0, 0.0, v

    s = rangec / maxc
    rc = (maxc-r) / rangec
    gc = (maxc-g) / rangec
    bc = (maxc-b) / rangec

    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0

    return h, s, v


def gamma_correction(value):
    if value > 0.04045:
        return pow((value + 0.055) / (1.0 + 0.055), 2.4)
    else:
        return value / 12.92


def rev_gamma_correction(value):
    if value <= 0.0031308:
        return 12.92 * value
    else:
        return (1.0 + 0.055) * pow(value, (1.0 / 2.4)) - 0.055


def rgb2xy(r, g, b):
    """ RGB 0-255 -> XY 0.0-1.0 """
    r = gamma_correction(r / 255)
    g = gamma_correction(g / 255)
    b = gamma_correction(b / 255)

    x = r * 0.649926 + g * 0.103455 + b * 0.197109
    y = r * 0.234327 + g * 0.743075 + b * 0.022598
    z = r * 0.0000000 + g * 0.053077 + b * 1.035763

    return (x / (x + y + z), y / (x + y + z))


def xyb2rgb(x, y, bri):
    """ XY 0.0-1.0, Bri 0-255 -> RGB 0-255 """
    z = 1.0 - x - y
    Y = bri / 255
    X = (Y / y) * x
    Z = (Y / y) * z
    r = X * 1.656492 - Y * 0.354851 - Z * 0.255038
    g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
    b =  X * 0.051713 - Y * 0.121364 + Z * 1.011530

    r = max(rev_gamma_correction(r), 0)
    g = max(rev_gamma_correction(g), 0)
    b = max(rev_gamma_correction(b), 0)

    # If one component is greater than 1, weight components by that value
    m = max(r, g, b)
    if (m > 1):
        r = r / m
        g = g / m
        b = b / m

    return (floor(r * 255), floor(g * 255), floor(b * 255))


def xyb2hsv(x, y, bri):
    """ XY 0.0-1.0, Bri 0-255 -> HS 0.0-1.0, V 0-255"""
    return rgb2hsv(*xyb2rgb(x, y, bri))


def hsv2xy(h, s, v):
    """ HS 0.0-1.0, V 0-255 -> XY 0.0-1.0 """
    return rgb2xy(*hsv2rgb(h, s, v))


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
        self.state = {} # Not the same as light state in deconz
        self._update_local_state(d['state'])

    def _set_remote_state(self, d):
        """ Sends new state to deconz light and calls get_state to update local state """
        with REST('PUT', f'{self.url}/state', d) as r:
            if r[0] == 200:
                # TODO: There is an issue where some lights report
                # wildly different values than what they were set to, so
                # as a workaround I expect the state to be set exactly,
                # which isn't always true.
                #self.get_state()
                return True
            else:
                print('set_state', r)
                return False

    def get_state(self):
        """ Update state of light from deconz """
        try:
            with REST('GET', self.url) as response:
                self._update_local_state(response[1]['state'])
            return True
        except Exception as e:
            print('get_state', e)
            return False

    def on(self):
        self._update_state(on=True)
        return self._set_remote_state({'on': True})

    def off(self):
        self._update_state(on=False)
        return self._set_remote_state({'on': False})

    def set_ctemp(self, on, ct, b):
        self._update_state(on=on, ct=ct, bri=b, mode='ctemp')
        return self._set_remote_state({'on': on, 'ct': ct, 'bri': b})

    def set_color(self, on, h, s, b):
        xy = hsv2xy(h, s, b)
        self._update_state(on=on, bri=b, hue=h, sat=s, mode='color')
        return self._set_remote_state({'on': on, 'xy': xy, 'bri': b})

    def _update_state(self, on=None, ct=None, bri=None, hue=None, sat=None, mode=None):
        if on is not None:
            self.state['on'] = on
        if ct is not None:
            self.state['ct'] = ct
        if bri is not None:
            self.state['bri'] = bri
        if hue is not None:
            self.state['hue'] = hue
        if sat is not None:
            self.state['sat'] = sat
        if mode:
            self.state['mode'] = mode

    def _update_local_state(self, state):
        """ Updates local light state from remote state data """
        if 'hue' in state:
            h, s, v = state['hue']/65535, state['sat']/255, state['bri']
        elif 'xy' in state:
            h, s, v = xyb2hsv(state['xy'][0], state['xy'][1], state['bri'])
        else:
            h, s, v = None, None, None
        self.state = {'on': state['on'],
                      'ct': state.get('ct'),
                      'bri': state.get('bri'),
                      'hue': h,
                      'sat': s}
        if state.get('colormode') in ['hs', 'xy']:
            self.state['mode'] = 'color'
        if state.get('colormode') == 'ct':
            self.state['mode'] = 'ctemp'


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
            raise e
            #print('get_lights', e)
            return False

    def get_light_by_id(self, id):
        for light in self.lights:
            if light.id == id:
                return light

#d = Display()
#system.start_wifi(d)

#import colors

#print('Init deconz')
#deconz = Deconz()

#for l in deconz.lights:
#    print(f'{l.id} - {l.name}')