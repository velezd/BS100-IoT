from machine import Pin


def check_key(pin, down, pressed):
    k = pin.value()
    if k != down:
        down = not down
        pressed = k
    else:
        pressed = False
    return down, pressed


class Keypad():
    def __init__(self):
        # Pins
        self.k_1 = Pin(36, Pin.IN)
        self.k_2 = Pin(39, Pin.IN)
        self.k_3 = Pin(34, Pin.IN)
        self.k_4 = Pin(35, Pin.IN)
        self.k_5 = Pin(32, Pin.IN)
        self.k_6 = Pin(33, Pin.IN)
        self.k_7 = Pin(25, Pin.IN)
        self.k_8 = Pin(26, Pin.IN)
        self.k_top = Pin(27, Pin.OUT)
        self.k_bottom = Pin(14, Pin.OUT)
        self.k_left = Pin(12, Pin.OUT)
        self.backlight = Pin(13, Pin.OUT)
        self.backlight_on()

        # Key pressed
        self.p_one = False
        self.p_two = False
        self.p_three = False
        self.p_four = False
        self.p_five = False
        self.p_six = False
        self.p_seven = False
        self.p_eight = False
        self.p_nine = False
        self.p_zero = False
        self.p_kzprava = False
        self.p_red = False
        self.p_revize = False
        self.p_potvrz = False
        self.p_zrusit = False
        self.p_up = False
        self.p_down = False
        self.p_left = False
        self.p_right = False
        self.p_straight = False
        # Key down
        self._one = False
        self._two = False
        self._three = False
        self._four = False
        self._five = False
        self._six = False
        self._seven = False
        self._eight = False
        self._nine = False
        self._zero = False
        self._kzprava = False
        self._red = False
        self._revize = False
        self._potvrz = False
        self._zrusit = False
        self._up = False
        self._down = False
        self._left = False
        self._right = False
        self._straight = False

    def any_pressed(self):
        return any((self.p_one, self.p_two, self.p_three, self.p_four, self.p_five, self.p_six, self.p_seven,
                   self.p_eight, self.p_nine, self.p_zero, self.p_kzprava, self.p_red, self.p_revize, 
                   self.p_potvrz, self.p_zrusit, self.p_up, self.p_down, self.p_left, self.p_right, self.p_straight))

    def backlight_on(self):
        self.backlight.on()

    def backlight_off(self):
        self.backlight.off()

    def get_keys(self):
        for n, p in enumerate((self.k_top, self.k_bottom, self.k_left)):
            p.value(True)
            if n == 0:
                self._three, self.p_three = check_key(self.k_1, self._three, self.p_three)
                self._two, self.p_two = check_key(self.k_2, self._two, self.p_two)
                self._one, self.p_one = check_key(self.k_3, self._one, self.p_one)
                self._red, self.p_red = check_key(self.k_4, self._red, self.p_red)
                self._kzprava, self.p_kzprava = check_key(self.k_5, self._kzprava, self.p_kzprava)
                self._four, self.p_four = check_key(self.k_6, self._four, self.p_four)
                self._five, self.p_five = check_key(self.k_7, self._five, self.p_five)
                self._six, self.p_six = check_key(self.k_8, self._six, self.p_six)
            if n == 1:
                self._nine, self.p_nine = check_key(self.k_1, self._nine, self.p_nine)
                self._eight, self.p_eight = check_key(self.k_2, self._eight, self.p_eight)
                self._seven, self.p_seven = check_key(self.k_3, self._seven, self.p_seven)
                self._revize, self.p_revize = check_key(self.k_4, self._revize, self.p_revize)
                self._up, self.p_up = check_key(self.k_5, self._up, self.p_up)
                self._zrusit, self.p_zrusit = check_key(self.k_6, self._zrusit, self.p_zrusit)
                self._zero, self.p_zero = check_key(self.k_7, self._zero, self.p_zero)
                self._potvrz, self.p_potvrz = check_key(self.k_8, self._potvrz, self.p_potvrz)
            if n == 2:
                self._down, self.p_down = check_key(self.k_5, self._down, self.p_down)
                self._right, self.p_right = check_key(self.k_6, self._right, self.p_right)
                self._straight, self.p_straight = check_key(self.k_7, self._straight, self.p_straight)
                self._left, self.p_left = check_key(self.k_8, self._left, self.p_left)
            p.value(False)