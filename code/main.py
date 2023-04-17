import system
import time
from lights_menu import LightsMenu
from hardware import Keypad, Display
from deconz import Deconz
from presets import PresetsActions


display = Display()
dash = system.BS100_dashboard(display)

keypad = Keypad()
dash.load_bar(2)

settings = system.Settings()
dash.load_bar(2)

ip = ""#system.start_wifi(display, settings, verbose=False)
dash.load_bar(4)

deconz = Deconz()
dash.load_bar(5)

system.set_time(settings)
dash.load_bar(2)

dash.get_calendar()
dash.load_bar(3)

preset_actions = PresetsActions(keypad, deconz, display)
dash.draw_dash()

t_backlight = time.time()+30
b_backlight = True
t_time = time.time()+60 # 1 minute
t_calendar = time.time()+7200 # 2 hours
while True:
    keypad.get_keys()

    if keypad.any_pressed():
        # Turn on backlight
        if b_backlight == False:
            b_backlight = True
            display.backlight_on()
            keypad.backlight_on()
        t_backlight = time.time()+30

        if preset_actions.key_pressed():
            dash.draw_dash()

    if keypad.p_potvrz:
        display.clear()
        display.print('Loading...', (5,1))
        deconz.get_lights()
        LightsMenu(deconz.lights, keypad, display, True).run()
        dash.draw_dash()

    if keypad.p_zero:
        system.ServiceMenu(ip, settings, display, keypad, deconz).run()
        dash.draw_dash()

    t = time.time()
    # Turn off backlight
    if t > t_backlight:
        if b_backlight == True:
            b_backlight = False
            display.backlight_off()
            keypad.backlight_off()
    # Update time
    if t > t_time:
        dash.show_time()
        t_time = time.time()+60
    # Update calendar
    if t > t_calendar:
        dash.get_calendar()
        t_calendar = time.time()+7200
