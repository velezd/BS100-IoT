import system
from lights_menu import LightsMenu
from hardware import Keypad, Display
from deconz import Deconz
from presets import PresetsActions


display = Display()
keypad = Keypad()
dash = system.BS100_dashboard(display, keypad)
dash.load_bar(2)

settings = system.Settings()
dash.load_bar(2)

ip = system.start_wifi(display, settings, verbose=False)
dash.load_bar(4)

deconz = Deconz()
dash.load_bar(5)

system.set_time(settings)
dash.load_bar(2)

dash.get_calendar()
dash.load_bar(3)

preset_actions = PresetsActions(keypad, deconz, display)
dash.draw_dash()

while True:
    keypad.get_keys()

    if keypad.any_pressed():
        dash.backlight_on()
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

    dash.update()
