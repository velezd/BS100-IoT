import time


class BaseMenu():
    toggle_char_on = bytearray([0x00,0x1F,0x15,0x1F,0x15,0x1F,0x00,0x00])
    toggle_char_off = bytearray([0x00,0x1F,0x11,0x11,0x11,0x1F,0x00,0x00])

    def __init__(self, display, keypad, items, toggles=False):
        self.keypad = keypad
        self.display = display
        self.selected = 0
        self.toggles = toggles
        self.items = items
        self.strings = list(items.keys())
        self.n_items = len(items)
        self.item_toggles = [ None for _ in range(0, self.n_items) ]

    def draw(self):
        self.display.custom_char(0, self.toggle_char_off)
        self.display.custom_char(1, self.toggle_char_on)
        self.display.clear()
        # line 1
        if self.selected != 0:
            self.draw_name(0)
        # line 2
        self.draw_name(1)
        # line 3
        if self.selected+1 < self.n_items: 
            self.draw_name(2)
        # line 4
        if self.selected+2 < self.n_items: 
            self.draw_name(3)

    def draw_name(self, y):
        i = self.selected + y - 1
        n = self.strings[i]
        if len(n) > 16:
            n = n[0:16]
        if y == 1:
            self.display.print('> ' + n, (0,y))
        else:
            self.display.print('  ' + n, (0,y))

        if self.toggles and self.item_toggles[i] is not None:
            if self.item_toggles[i]:
                self.display.print(chr(1), (19,y))
            else:
                self.display.print(chr(0), (19,y))

    def empty_menu(self):
        if self.n_items == 0:
            self.display.clear()
            self.display.print('Empty menu')
            time.sleep(3)
            return True