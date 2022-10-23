import system
import time
import requests
from menus import ItemMenu
from keypad import Keypad
from display import Display
from deconz import Deconz


def get_calendar():
    url = ''
    r = requests.get(url)
    t = r.text
    r.close()
    return t

def print_calendar(cal, d):
    for i, line in enumerate(cal):
        d.print(line, (0,i))

display = Display()
keypad = Keypad()
settings = system.Settings()

system.start_wifi(display, settings)

display.print('Init deCONZ', (4,1)) 
deconz = Deconz()

display.clear()
display.print('Init time', (5,1))
system.set_time(settings)

display.clear()
display.print('Init calendar', (3,1))
calendar = get_calendar().splitlines()

display.clear()
print_calendar(calendar, display)

system.show_time(display)

t_backlight = time.time()+30
b_backlight = True
t_time = time.time()+60

while True:
    keypad.get_keys()
    if keypad.any_pressed():
        # Turn on backlight
        if b_backlight == False:
            b_backlight = True
            display.backlight_on()
            keypad.backlight_on()
        t_backlight = time.time()+30

    if keypad.p_potvrz:
        display.clear()
        display.print('Loading...', (5,1))
        deconz.get_lights()
        ItemMenu(deconz.lights, keypad, display, True).run()
        display.clear()
        print_calendar(calendar, display)
        system.show_time(display)

    t = time.time()
    # Turn off backlight
    if t > t_backlight:
        if b_backlight == True:
            b_backlight = False
            display.backlight_off()
            keypad.backlight_off()
    if t > t_time:
        system.show_time(display)
        t_time = time.time()+60
