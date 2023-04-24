import ujson
import time
from ucollections import OrderedDict
from base_menu import BaseMenu
from lights_menu import LightsMenu, ColorMenu
from input_ui import text_input_ui


class PresetsActions():
    def __init__(self, keypad, deconz, display):
        self.deconz = deconz
        self.keypad = keypad
        self.display = display
        self.load()

    def load(self):
        """ Load presets """
        with open('presets.json', 'r') as po:
            self.presets = ujson.load(po)

    def key_pressed(self):
        """ Handle key press """
        if self.keypad.p_red: # If RED button is pressed wait 5 sec for another key
            tout = time.time() + 5
            while tout > time.time():
                self.keypad.get_keys()
                if self._preset_keys(True):
                    return True

        return self._preset_keys(False)

    def _preset_keys(self, off):
        """ Check keys assigned to presets """
        if self.keypad.p_one:
            self.do_preset('1', off)
        elif self.keypad.p_two:
            self.do_preset('2', off)
        elif self.keypad.p_three:
            self.do_preset('3', off)
        elif self.keypad.p_four:
            self.do_preset('4', off)
        elif self.keypad.p_five:
            self.do_preset('5', off)
        elif self.keypad.p_six:
            self.do_preset('6', off)
        elif self.keypad.p_seven:
            self.do_preset('7', off)
        elif self.keypad.p_eight:
            self.do_preset('8', off)
        elif self.keypad.p_nine:
            self.do_preset('9', off)
        else:
            return False # Return False if not preset key was pressed
        return True

    def do_preset(self, preset, off):
        """ Send preset state to all lights in preset """
        self.display.clear()      
        self.display.print('Applying...', (5,1))

        for light_id, state in self.presets[preset][1].items():
            if off: # If 'off' is True, turn off all lights in preset
                self.deconz.get_light_by_id(light_id).off()
                continue
            l = self.deconz.get_light_by_id(light_id)
            if state['mode'] == 'color':
                l.set_color(state['on'], state['hue'], state['sat'], state['bri'])
            elif state['mode'] == 'ctemp':
                l.set_ctemp(state['on'], state['ct'], state['bri'])
            else:
                l._set_remote_state(state)


class PresetsListMenu(BaseMenu):
    """ Select preset to edit """
    def __init__(self, keypad, display, deconz):
        with open('presets.json', 'r') as po:
            self.presets = ujson.load(po)

        items = OrderedDict()
        for id, preset in sorted(self.presets.items()):
            items[f'{id}: {preset[0]}'] = PresetMenu(keypad, display, preset[1], deconz)

        super().__init__(display, keypad, items)

    def run(self):
        if self.empty_menu(): return

        self.draw()
        while True:
            self.keypad.get_keys()
            
            if self.keypad.p_zrusit:
                return False
            if self.keypad.p_potvrz:
                selected_item = self.strings[self.selected]
                preset_id = selected_item.split(':')[0]
                preset_name = self.presets[preset_id][0]
                new_preset = self.items[selected_item].run() # Run preset menu
                # if preset was changed
                if new_preset:
                    new_name = text_input_ui(self.display, self.keypad, 'Name', preset_name)
                    preset_name = new_name if new_name else preset_name
                    self.presets[preset_id] = [preset_name, new_preset]
                    with open('presets.json', 'w') as po: # Save presets
                        ujson.dump(self.presets, po)
                    return True
                self.draw()
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


class PresetMenu(BaseMenu):
    """ Change preset light state, add and remove lights """
    def __init__(self, keypad, display, preset, deconz):
        self.deconz = deconz
        self.preset = preset
        items = OrderedDict()
        # Get lights used in preset
        for light_id in preset.keys():
            light = deconz.get_light_by_id(light_id)
            items[light.name] = light

        # Get list of lights not in preset
        self.unused_lights = []
        for light in deconz.lights:
            if light.id not in preset.keys():
                self.unused_lights.append(light)

        # Add special items to the menu
        items['[ ADD ]'] = None
        items['[ SAVE ]'] = None

        super().__init__(display, keypad, items)

    def run(self):
        if self.empty_menu(): return

        self.draw()
        while True:
            self.keypad.get_keys()
            
            if self.keypad.p_zrusit:
                return
            if self.keypad.p_potvrz:
                item_name = self.strings[self.selected]
                # Save preset
                if item_name == '[ SAVE ]':
                    return self.preset

                # Add light to preset
                if item_name == '[ ADD ]':
                    self.display.clear()
                    self.display.print('Loading...', (5,1))
                    self.deconz.get_lights()
                    l = LightsMenu(self.unused_lights, self.keypad, self.display, return_light=True).run()
                    if l:
                        self.preset[l.id] = l.state
                    # If new light was addedd re-init the menu
                    self.__init__(self.keypad, self.display, self.preset, self.deconz)
                    self.draw()
                    continue

                # Change light settings in preset
                l = ColorMenu(self.items[item_name], self.display, self.keypad).run()
                if l:
                    self.preset[l.id] = l.state
                self.draw()

            if self.keypad.p_red:
                light = self.items[self.strings[self.selected]]
                if light is None: # Not a light
                    continue
                # Get id of selected light, remove it from preset and re-init menu
                del self.preset[light.id]
                self.__init__(self.keypad, self.display, self.preset, self.deconz)
                self.draw()
                continue

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


# Testing
if __name__ == "__main__":
    from hardware import Keypad, Display
    import system
    from deconz import Deconz

    display = Display()
    keypad = Keypad()
    settings = system.Settings()
    #system.start_wifi(display, settings)

    display.clear()
    display.print('Init deCONZ', (4,1)) 
    deconz = Deconz()

    PresetsListMenu(keypad, display, deconz).run()