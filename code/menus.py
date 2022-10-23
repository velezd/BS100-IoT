import time


class ItemMenu():
    def __init__(self, items, keypad, display, lights=False):
        self.toggle_char_on = bytearray([0x00,0x1F,0x15,0x1F,0x15,0x1F,0x00,0x00])
        self.toggle_char_off = bytearray([0x00,0x1F,0x11,0x11,0x11,0x1F,0x00,0x00])
        self.keypad = keypad
        self.display = display
        self.selected = 0
        if lights:
            self.strings = []
            for l in items:
                self.strings.append(l.name)
            self.lights = items
        else:
            self.items = items
            self.strings = list(items.keys())
            self.lights = None
        self.n_items = len(items)

    def draw(self):
        self.display.custom_char(0, self.toggle_char_off)
        self.display.custom_char(1, self.toggle_char_on)
        self.display.clear()
        # line 1
        if self.selected != 0:
            self.draw_name(0)
            self.draw_toggle(self.lights[self.selected-1], 0)
        # line 2
        self.draw_name(1)
        self.draw_toggle(self.lights[self.selected], 1)
        # line 3
        if self.selected+1 < self.n_items: 
            self.draw_name(2)
            self.draw_toggle(self.lights[self.selected+1], 2)
        # line 4
        if self.selected+2 < self.n_items: 
            self.draw_name(3)
            self.draw_toggle(self.lights[self.selected+2], 3)

    def draw_name(self, y):
        n = self.strings[self.selected + y - 1]
        if len(n) > 16:
            n = n[0:16]
        if y == 1:
            self.display.print('> ' + n, (0,y))
        else:
            self.display.print('  ' + n, (0,y))

    def draw_toggle(self, l, y):
        if self.lights:
            if l.state['on']:
                self.display.print(chr(1), (19,y))
            else:
                self.display.print(chr(0), (19,y))

    def run(self):
        self.draw()
        while True:
            self.keypad.get_keys()
            
            if self.keypad.p_zrusit:
                break
            if self.keypad.p_potvrz:
                if self.lights:
                    ColorMenu(self.lights[self.selected], self.display, self.keypad).run()
                else:
                    self.items[self.strings[self.selected]]()
                self.draw()
            if self.keypad.p_revize and self.lights:
                if self.lights[self.selected].state['on']:
                    self.lights[self.selected].off()
                else:
                    self.lights[self.selected].on()
                self.draw_toggle(self.lights[self.selected], 1)
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
        self.l.get_state()
        self.s = l.state.copy() # State working copy
        print(self.s)
        self.org_s = l.state.copy() # Original state
        # State values: min, max, step
        #self.sv = ((140, 650, 25),
        #           (0, 255, 12),
        #           (0.0, 1.0, 0.05), 
        #           (0.0, 1.0, 0.05))
        self.sv = {'ct': (140, 650, 25),
                   'bri': (0, 255, 12),
                   'sat': (0.0, 1.0, 0.05), 
                   'hue': (0.0, 1.0, 0.05)}
        self.draw_base()

    def draw_base(self):
        self.display.clear()
        self.display.custom_char(0, self.bar_char)
        self.display.print('CT', (0,0))
        self.display.print('Bri', (0,1))
        self.display.print('Sat', (0,2))
        self.display.print('Hue', (0,3))

    def draw_slider(self, y, name):
        mins = self.sv[name][0]
        maxs = self.sv[name][1]
        step = self.sv[name][2]*2
        curs = self.s[name]

        self.display.print('[', (7,y))
        for i, _ in enumerate(range(mins, curs, step)):
            self.display.putchar(chr(0))
        if i != 10:
            for _ in range(curs, maxs, step):
                self.display.putchar(' ')
        self.display.putchar(']')

    def draw(self):
        # Erase and draw selection indicator
        self.display.print(' ', (5, 0))
        self.display.print(' ', (5, 1))
        self.display.print(' ', (5, 2))
        self.display.print(' ', (5, 3))
        self.display.print('>', (5, self.selected))

        if self.l.state['mode'] == 'ct':
            self.draw_slider(0, 'ct')
        self.draw_slider(1, 'bri')
        if self.l.state['mode'] in ['hs', 'xy']:
            self.draw_slider(2, 'sat')
            self.draw_slider(3, 'hue')

    def run(self):
        self.display.clear()
        c = False # Change happened
        cs = True # Change submited
        cd = True # Change display
        r = time.ticks_ms() 
        while True:
            if cd:
                self.draw()
            cd = False
            c = False
            self.keypad.get_keys()
            ssel = ('ct', 'bri', 'sat', 'hue')[self.selected] # Selected state name
            sstep = self.sv[ssel]
            
            if self.keypad.p_zrusit:
                # Cancel changes
                if self.l.state != self.org_s:
                    self.l.update_state(self.org_s)
                break
            if self.keypad.p_potvrz:
                # Apply change if they are not applied yet
                if self.l.state != self.s:
                    self.l.update_state(self.s)
                break
            if self.keypad.p_up:
                cd = True
                if self.selected != 0:
                    self.selected -= 1
            if self.keypad.p_down:
                cd = True
                if self.selected != 3:
                    self.selected += 1
            if self.keypad.p_left:
                if self.s[ssel] is None:
                    continue
                self.s[ssel] -= sstep[2]
                if self.s[ssel] < sstep[0]:
                    self.s[ssel] = sstep[0]
                c = True
                cd = True
            if self.keypad.p_right:
                if self.s[ssel] is None:
                    continue
                self.s[ssel] += sstep[2]
                if self.s[ssel] > sstep[1]:
                    self.s[ssel] = sstep[1]
                c = True
                cd = True
            
            # Change colormode - colormode can't be changed directly,
            # it has to be done by changing color or color temperature.
            if self.keypad.p_revize:
                if self.l.state['mode'] == 'ct':
                    self.s['xy'] = 
                    self.s['hue'] = self.s['hue']+1 if self.s['hue'] else 128
                    n = {'hue': self.s['hue'], 'sat': self.sv[ssel][1], 'colormode': 'xy'}
                    print(n)
                    print(self.l.update_state(n))
                else:
                    self.s['ct'] = self.s['ct']+1 if self.s['ct'] else 350
                    print(self.l.update_state({'ct': self.s['ct']}))
                self.draw_base()
                self.l.get_state()
                self.s = self.l.state.copy() # State working copy
                cd = True
            # Update lights state
            if self.keypad.p_straight:
                #changes = {}
                #for k in self.s.keys():
                #    if self.s[k] != self.l.state[k]:
                #        changes[k] = self.s[k]
                #print(changes)
                #self.l.update_state(changes)

# Testing

#from keypad import Keypad
#from display import Display
#import system
#from deconz import Deconz
#
#display = Display()
#keypad = Keypad()
##system.start_wifi(display)
#
#display.print('Init deCONZ', (4,1)) 
#deconz = Deconz()
#
#ItemMenu(deconz.lights, keypad, display, True).run()
