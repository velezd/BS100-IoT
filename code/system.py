import network as n
import time
import socket
import struct
from machine import RTC


def start_wifi(display, settings):
    try:
        ssid = settings.wifi_ssid
        passw = settings.wifi_pass
    except:
        display.print('WiFi config error', (0,1))
        time.sleep(3)
        return False

    display.print('Connecting to WiFi', (1,1))
    ok = False

    try:
        wlan = n.WLAN(n.STA_IF) # create station interface
        if wlan.status() == n.STAT_GOT_IP:
            ok = True
        wlan.active(True)       # activate the interface
        wlan.connect(ssid, passw) # connect to an AP

        display.print('Connecting to WiFi', (1,1))
        while not ok:
            s = wlan.status()
            if s == n.STAT_GOT_IP:
                ok = True
                break
            if s == n.STAT_NO_AP_FOUND:
                display.clear()
                display.print('Wrong SSID', (5,1))
                break
            if s == n.STAT_WRONG_PASSWORD:
                display.clear()
                display.print('Wrong password', (2,1))
                break
            if s in (n.STAT_ASSOC_FAIL, n.STAT_BEACON_TIMEOUT, n.STAT_HANDSHAKE_TIMEOUT):
                display.clear()
                break
            time.sleep(1)
    except:
        display.clear()
        display.print('Connection failed', (1,2))
        raise

    if ok:
        display.clear()
        display.print('Connected', (0,1))
        display.print(wlan.ifconfig()[0], (0,2))
        time.sleep(3)
        return True
    
    display.print('Connection failed', (1,2))
    time.sleep(3)
    return False

def ntptime():
    HOST = 'ntp.nic.cz'
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1b
    addr = socket.getaddrinfo(HOST, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1)
    res = s.sendto(NTP_QUERY, addr)
    msg = s.recv(48)
    s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    return int(val-3155673600)

def set_time(settings):
    try:
        summer = bool(settings.time_summer)
    except:
        summer = False

    t = ntptime()
    tm = time.localtime(t)
    h = tm[3]+2 if summer else tm[3]+1 # Timezone + summer time correction
    tm = tm[0:3] + (0,h) + tm[4:6] + (0,)
    RTC().datetime(tm)

def show_time(d):
    t = time.localtime()
    h = f' {t[3]}' if len(str(t[3])) == 1 else t[3]
    m = f'0{t[4]}' if len(str(t[4])) == 1 else t[4]
    d.print(f'{h}:{m}', (15,3))


class Settings():
    def __init__(self):
        self._cfg_file = 'system.cfg'
        self._settings = dict()

        with open(self._cfg_file, 'r') as fo:
            for line in fo.readlines():
                if line.startswith('#'):
                    continue
                try:
                    n, v = line.split('=', '1')    
                except:
                    continue
                self._settings[n.strip()] = v.strip()

    def __getattribute__(self, name):
        return self._settings[name]

    def update(self, name, value):
        self._settings[name] = value

        with open(self._cfg_file, 'w') as fo:
            for k,v in self._settings.items():
                fo.write(f'{k}={v}\n')