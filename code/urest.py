import usocket
import ujson


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
        print(status)
        while True:
            l = self.s.readline()
            print(l)
            if not l or l == b"\r\n":
                break
            if l.startswith(b"Transfer-Encoding:"):
                if b"chunked" in l:
                    raise ValueError("Unsupported " + str(l, "utf-8"))

        # Read response data
        d = bytes()
        print('reading')
        try:
            while True:
                d += self.s.read(1)
        except OSError as e:
            if e.errno != 116: # ETIMEDOUT
                raise
        print('done reding')
        d = ujson.loads(d)

        return (status, d)

    def __exit__(self, type, value, traceback):
        if self.s is not None:
            self.s.close()


from display import Display
from system import start_wifi

d = Display()
#start_wifi(d)

print('starting')
url = ''

import requests
r = requests.get(url)
d.print(r.text, (0,0))
r.close()

#with REST('GET', url) as r:
#    print(r)

print('end')