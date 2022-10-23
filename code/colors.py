from math import pow, floor


def hsv2rgb(h, s, v):
    """ HS 0.0-1.0, V 0-255 -> RGB 0-255 """
    if s == 0.0:
        return v, v, v

    i = int(h*6.0) # XXX assume int() truncates!
    f = (h*6.0) - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0-f))
    i = i%6

    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q


def rgb2hsv(r, g, b):
    """ RGB 0-255 -> HS 0.0-1.0, V 0-255"""
    maxc = max(r, g, b)
    minc = min(r, g, b)
    rangec = (maxc-minc)
    v = maxc

    if minc == maxc:
        return 0.0, 0.0, v

    s = rangec / maxc
    rc = (maxc-r) / rangec
    gc = (maxc-g) / rangec
    bc = (maxc-b) / rangec

    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0

    return h, s, v


def gamma_correction(value):
    if value > 0.04045:
        return pow((value + 0.055) / (1.0 + 0.055), 2.4)
    else:
        return value / 12.92


def rev_gamma_correction(value):
    if value <= 0.0031308:
        return 12.92 * value
    else:
        return (1.0 + 0.055) * pow(value, (1.0 / 2.4)) - 0.055


def rgb2xy(r, g, b):
    """ RGB 0-255 -> XY 0.0-1.0 """
    r = gamma_correction(r / 255)
    g = gamma_correction(g / 255)
    b = gamma_correction(b / 255)

    x = r * 0.649926 + g * 0.103455 + b * 0.197109
    y = r * 0.234327 + g * 0.743075 + b * 0.022598
    z = r * 0.0000000 + g * 0.053077 + b * 1.035763

    return (x / (x + y + z), y / (x + y + z))


def xyb2rgb(x, y, bri):
    """ XY 0.0-1.0, Bri 0-255 -> RGB 0-255 """
    z = 1.0 - x - y
    Y = bri / 255
    X = (Y / y) * x
    Z = (Y / y) * z
    r = X * 1.656492 - Y * 0.354851 - Z * 0.255038
    g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
    b =  X * 0.051713 - Y * 0.121364 + Z * 1.011530

    r = max(rev_gamma_correction(r), 0)
    g = max(rev_gamma_correction(g), 0)
    b = max(rev_gamma_correction(b), 0)

    # If one component is greater than 1, weight components by that value
    m = max(r, g, b)
    if (m > 1):
        r = r / m
        g = g / m
        b = b / m

    return (floor(r * 255), floor(g * 255), floor(b * 255))

def xyb2hsv(x, y, bri):
    """ XY 0.0-1.0, Bri 0-255 -> HS 0.0-1.0, V 0-255"""
    return rgb2hsv(*xyb2rgb(x, y, bri))

def hsv2xy(h, s, v):
    """ HS 0.0-1.0, V 0-255 -> XY 0.0-1.0 """
    return rgb2xy(*hsv2rgb(h, s, v))
