from base_menu import BaseMenu


def range(start, end, step=1):
    """ Custom range that works with floats """
    if start == end:
        return []

    dec = None
    if isinstance(step, float):
        dec = len(str(step).split('.')[1])

    res = [start]
    while start+step < end:
        start += step 
        if dec is not None:
            res.append(round(start, dec))
        else:
            res.append(start)

    return res


class LightsMenu(BaseMenu):
    def __init__(self, items, keypad, display, return_light=False):
        super().__init__(display, keypad, {}, True)
        self.return_light = return_light
        self.items = items
        for l in items:
            self.strings.append(l.name)
            self.item_toggles.append(l.state['on'])
        self.n_items = len(items)

    def run(self):
        if self.empty_menu(): return
        self.draw()

        while True:
            self.keypad.get_keys()
            if self.keypad.p_zrusit:
                return False
            # Enter Color Menu
            if self.keypad.p_potvrz:
                l = ColorMenu(self.items[self.selected], self.display, self.keypad).run()
                if l and self.return_light:
                    return l
                self.draw()
            # Turning light on / off
            if self.keypad.p_revize:
                print(self.items[self.selected].state['on'])
                if self.items[self.selected].state['on']:
                    if self.items[self.selected].off():
                        self.item_toggles[self.selected] = False
                else:
                    if self.items[self.selected].on():
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

class ColorMenu():
    def __init__(self, l, display, keypad):
        self.bar_char = bytearray([0x00,0x1F,0x1F,0x1F,0x1F,0x1F,0x00,0x00])
        self.display = display
        self.keypad = keypad
        self.selected = 0
        self.l = l # Light
        self.on_off = True if l.state['bri'] is None else False # On/off only mode
        self.s = l.state.copy() # State working copy
        self.org_s = l.state.copy() # Original state
        # State values, [min, max, step]
        self.sv = {'ct': (140, 650, 25),
                   'bri': (0, 255, 12),
                   'sat': (0.0, 1.0, 0.05), 
                   'hue': (0.0, 1.0, 0.05)}

    def draw_base(self):
        self.display.clear()
        if self.on_off:
            self.display.print('On/Off only', (5,1))
            return

        self.display.custom_char(0, self.bar_char)
        self.display.print('CT', (0,0))
        self.display.print('Bri', (0,1))
        self.display.print('Sat', (0,2))
        self.display.print('Hue', (0,3))

    def draw_slider(self, y, name):
        # Draw empty slider if it is irrelevant for the light mode
        if (name in ['hue', 'sat'] and self.s['mode'] == 'ctemp' or
            name == 'ct' and self.s['mode'] == 'color'):
            self.display.print('            ', (7,y))
            return

        mins = self.sv[name][0]
        maxs = self.sv[name][1]
        step = self.sv[name][2]*2
        curs = self.s[name]

        self.display.print('[', (7,y))
        # Draw blocks in the slider
        i = -1
        for i, _ in enumerate(range(mins, curs, step)):
            self.display.putchar(chr(0))

        # Workaround for values that are exactly divisible
        if curs == maxs and i == 9:
            self.display.putchar(chr(0))
            i = 10

        # draw the rest empty
        for _ in range(i, 10):
            self.display.putchar(' ')
        self.display.putchar(']')

    def draw(self):
        if self.on_off: return
        # Erase and draw selection indicator
        self.display.print(' ', (5, 0))
        self.display.print(' ', (5, 1))
        self.display.print(' ', (5, 2))
        self.display.print(' ', (5, 3))
        self.display.print('>', (5, self.selected))

        if self.l.state['mode'] == 'ctemp':
            self.draw_slider(0, 'ct')
        self.draw_slider(1, 'bri') # TODO: brightnes slider broken
        if self.l.state['mode'] == 'color':
            self.draw_slider(2, 'sat') # TODO: sat slider doesn't go to end
            self.draw_slider(3, 'hue') # TODO: hue doesn't go to end

    def run(self):
        self.draw_base()
        cd = True # Change display
        while True:
            if cd:
                self.draw()
            cd = False

            self.keypad.get_keys()
            ssel = ('ct', 'bri', 'sat', 'hue')[self.selected] # Selected state name
            sstep = self.sv[ssel]
            
            if self.keypad.p_zrusit:
                self.cancel_changes()
                return False

            if self.keypad.p_potvrz:
                # Apply change if they are not applied yet
                if self.l.state != self.s:
                    self.apply_changes()
                return self.l

            if self.keypad.p_up:
                if self.selected != 0:
                    self.selected -= 1
                cd = True
            if self.keypad.p_down:
                if self.selected != 3:
                    self.selected += 1
                cd = True
            if self.keypad.p_left and not self.on_off:
                if self.s[ssel] is None:
                    continue
                self.s[ssel] -= sstep[2]
                if self.s[ssel] < sstep[0]:
                    self.s[ssel] = sstep[0]
                cd = True
            if self.keypad.p_right and not self.on_off:
                if self.s[ssel] is None:
                    continue
                self.s[ssel] += sstep[2]
                if self.s[ssel] > sstep[1]:
                    self.s[ssel] = sstep[1]
                cd = True
            
            if self.keypad.p_zero:
                self.toggle()

            # Change colormode - colormode can't be changed directly,
            # it has to be done by changing color or color temperature.
            if self.keypad.p_revize and not self.on_off:
                self.draw_base()
                if self.l.state['mode'] == 'ctemp':
                    self.switch_to_color()
                else:
                    self.switch_to_ctemp()
                self.s = self.l.state.copy()
                cd = True

            # Update lights state
            if self.keypad.p_straight and not self.on_off:
                self.apply_changes()
                self.s = self.l.state.copy()
                cd = True

    def switch_to_color(self):
        # TODO: Switch to color temp is broken
        if self.s['hue'] <= self.sv['hue'][1] - self.sv['hue'][2]:
            self.s['hue'] += 0.01
        else:
            self.s['hue'] -= 0.01
        self.l.set_color(self.s['on'], self.s['hue'], self.s['sat'], self.s['bri'])

    def switch_to_ctemp(self):
        if self.s['ct'] < self.sv['ct'][1]:
            self.s['ct'] += 1
        else:
            self.s['ct']  -= 1
        self.l.set_ctemp(self.s['on'], self.s['ct'], self.s['bri'])

    def toggle(self):
        if self.s['on']:
            self.l.off()
            self.s['on'] = False
        else:
            self.l.on()
            self.s['on'] = True


    def cancel_changes(self):
        if self.on_off:
            return
        if self.org_s['mode'] == 'color':
            self.l.set_color(self.org_s['on'],
                             self.org_s['hue'],
                             self.org_s['sat'],
                             self.org_s['bri'])
        else:
            self.l.set_ctemp(self.org_s['on'],
                             self.org_s['ct'],
                             self.org_s['bri'])

    def apply_changes(self):
        if self.on_off:
            return
        if self.s['mode'] == 'color':
            self.l.set_color(self.s['on'],
                             self.s['hue'],
                             self.s['sat'],
                             self.s['bri'])
        else:
            self.l.set_ctemp(self.s['on'],
                             self.s['ct'],
                             self.s['bri'])


if __name__ == "__main__":
    # Testing
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

    LightsMenu(deconz.lights, keypad, display).run()