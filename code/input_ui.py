CHARS_MIN = ' abcdefghijklmnopqrstuvwxyz'
CHARS_ALL = ' abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,.;:-_=+!@#$%&*'


def text_input_ui(display, keypad, title, answer=' ', min_chars=True):
    """ Text input UI

    Max 20 characters, spaces at the start and end will be striped,
    returns None if input is canceled otherwise returns the answer string.

    title: string, Title or question displayed on screen
    answer: string, pre-filled answer
    min_chars: bool, selection of available characters min/all
    """
    display.clear()
    display.print(f'{title}:', (0,1))
    display.move_to(0,2)
    display.print(answer)
    display.move_to(0,2)
    display.show_cursor()
    display.blink_cursor_on()

    answer = [' '] if len(answer) == 0 else list(answer)
    chars = CHARS_MIN if min_chars else CHARS_ALL
    chars_len = len(chars)-1
    char_pos = 0
    pos = 0
    cancel = False

    while True:
        keypad.get_keys()

        if keypad.p_zrusit:
            cancel = True
            break
        if keypad.p_potvrz:
            break
        # Insert space / remove selected place in the answer
        if keypad.p_red:
            answer[pos] = ' '
            display.putchar(' ')
            if pos > 0:
                pos -= 1
            display.move_to(pos,2)

        # Move up and down in the character bank
        if keypad.p_up:
            if char_pos < chars_len:
                char_pos += 1
            else:
                char_pos = 0
            answer[pos] = chars[char_pos]
            # Print selected char to screen and move back
            display.putchar(chars[char_pos])
            display.move_to(pos,2)
        if keypad.p_down:
            if char_pos > 0:
                char_pos -= 1
            else:
                char_pos = chars_len
            answer[pos] = chars[char_pos]
            # Print selected char to screen and move back
            display.putchar(chars[char_pos])
            display.move_to(pos,2)

        # Move left and right in the answer string
        if keypad.p_right:
            # Add selected char if we go over the end
            if pos == len(answer)-1 and pos < 19:
                answer += ' '
            pos += 1
            display.move_to(pos,2)
        if keypad.p_left:
            if pos > 0:
                pos -= 1
            display.move_to(pos,2)


    display.blink_cursor_off()
    display.hide_cursor()

    if not cancel:
        return ''.join(answer).strip()

# Testing
if __name__ == "__main__":
    from hardware import Keypad, Display
    display = Display()
    keypad = Keypad()
    print(text_input_ui(display, keypad, 'Minimal'))
    print(text_input_ui(display, keypad, 'All', 'Testing', False))