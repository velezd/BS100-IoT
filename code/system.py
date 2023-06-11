import network as n
import time
import socket
import struct
import requests
from machine import RTC
from base_menu import BaseMenu
from presets import PresetsListMenu
from temperature import TempSensor


def start_wifi(display, settings, verbose=True):
    try:
        ssid = settings.g('wifi_ssid')
        passw = settings.g('wifi_pass')
    except:
        display.print('WiFi config error', (0,1))
        time.sleep(3)
        return False

    if verbose:
        display.print('Connecting to WiFi', (1,1))
    ok = False

    try:
        wlan = n.WLAN(n.STA_IF) # create station interface
        if wlan.status() == n.STAT_GOT_IP:
            ok = True
        wlan.active(True)       # activate the interface
        wlan.connect(ssid, passw) # connect to an AP

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
        if verbose:
            display.clear()
            display.print('Connected', (0,1))
            display.print(wlan.ifconfig()[0], (0,2))
            time.sleep(3)
        return wlan.ifconfig()[0]
    
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
        summer = bool(settings.g('time_summer'))
    except:
        summer = False

    t = ntptime()
    tm = time.localtime(t)
    h = tm[3]+2 if summer else tm[3]+1 # Timezone + summer time correction
    tm = tm[0:3] + (0,h) + tm[4:6] + (0,)
    RTC().datetime(tm)


class Settings():
    def __init__(self):
        self._cfg_file = 'system.cfg'
        self._settings = dict()

        with open(self._cfg_file, 'r') as fo:
            for line in fo.readlines():
                if line.startswith('#'):
                    continue
                try:
                    n, v = line.split('=', 1)
                except:
                    continue
                self._settings[n.strip()] = v.strip()

    def g(self, n):
        return self._settings.get(n)

    def update(self, name, value):
        self._settings[name] = value

        with open(self._cfg_file, 'w') as fo:
            for k,v in self._settings.items():
                fo.write(f'{k}={v}\n')


class ServiceMenu(BaseMenu):
    def __init__(self, ip, settings, display, keypad, deconz, preset_actions):
        self.settings = settings
        items = {0: None,
                 1: 'time_summer',
                 2: preset_actions.configure()}
        super().__init__(display, keypad, items, True)
        self.strings = ['IP: ' + ip, 'Summer time', 'Presets']
        self.item_toggles[1] = self.settings.g('time_summer')

    def run(self):
        self.draw()

        while True:
            self.keypad.get_keys()
            if self.keypad.p_zrusit:
                return False
            # Enter submenu item
            if self.keypad.p_potvrz:
                if 'run' in dir(self.items[self.selected]):
                    self.items[self.selected].run()
                self.draw()
            # Change toggle settings
            if self.keypad.p_revize:
                if isinstance(self.items[self.selected], str):
                    if self.item_toggles[self.selected]:
                        self.settings.update(self.items[self.selected], False)
                        self.item_toggles[self.selected] = False
                    else:
                        self.settings.update(self.items[self.selected], True)
                        self.item_toggles[self.selected] = True
                    self.draw_name(1)
            # Menu item selection
            if self.keypad.p_up:
                self.selected -= 1
                if self.selected == -1:
                    self.selected = self.n_items-1
                self.draw()
            if self.keypad.p_down:
                self.selected += 1
                if self.selected == self.n_items:
                    self.selected = 0
                self.draw()


class BS100_dashboard():
    def __init__(self, display, keypad):
        self.keypad = keypad
        self.display = display
        self.display.print('Initialization', (3,1))
        self.display.move_to(0,3)
        self.backlight = True
        self.temp_sensor = TempSensor()
        self.temp = '----'
        self.deg_char = bytearray([0x02,0x05,0x02,0x00,0x00,0x00,0x00,0x00]) # degree character
        self.calendar_url = ''

        self._timers_full = {
            'time': 60, # 1 minute
            'calendar': 7200, # 2 hours
            'backlight': 30, # 0.5 minute
            'temp': 5
        }
        self._timers = {}
        for timer in self._timers_full.keys():
            self.reset_timer(timer)

        self.load_bar(2)

    def set_calendar_url(self, settings):
        self.calendar_url = settings.g('calendar')

    def get_calendar(self):
        # Get current calendar data
        url = self.calendar_url
        r = requests.get(url)
        t = r.text
        r.close()
        self.calendar = t.splitlines()

    def print_calendar(self):
        # Clear old calendar
        for i in range(3):
            self.display.print(' '*20, (0,i))
        # Show calendar
        for i, line in enumerate(self.calendar):
            self.display.print(line, (0,i))

    def load_bar(self, n):
        # Show part of the loading progress bar
        for _ in range(n):
            self.display.putchar(chr(255))

    def show_time(self):
        # Show time
        t = time.localtime()
        h = f' {t[3]}' if len(str(t[3])) == 1 else t[3]
        m = f'0{t[4]}' if len(str(t[4])) == 1 else t[4]
        self.display.print(f'{h}:{m}', (15,3))

    def show_temp(self):
        self.display.print(self.temp + chr(0) + 'C', (0,3))

    def draw_dash(self):
        # Draw dashboard UI
        self.display.custom_char(0, self.deg_char)
        self.backlight_on()
        self.display.clear()
        self.print_calendar()
        self.show_temp()
        self.show_time()

    def reset_timer(self, name):
        # Check if the time in timer has passed
        self._timers[name] = time.time() + self._timers_full[name]

    def timer_passed(self, name):
        # Reset specified timer
        return time.time() > self._timers[name]

    def backlight_on(self):
        # Turn on backlight
        self.reset_timer('backlight')
        if self.backlight == False:
            self.backlight = True
            self.display.backlight_on()
            self.keypad.backlight_on()

    def update(self):
        # Turn off backlight
        if self.timer_passed('backlight'):
            if self.backlight == True:
                self.backlight = False
                self.display.backlight_off()
                self.keypad.backlight_off()
        # Update time
        if self.timer_passed('time'):
            self.show_time()
            self.reset_timer('time')
        # Update calendar
        if self.timer_passed('calendar'):
            self.get_calendar()
            self.print_calendar()
            self.reset_timer('calendar')
        # Update temperature
        if self.timer_passed('temp'):
            self.temp = self.temp_sensor.read()
            self.show_temp()
            self.reset_timer('temp')