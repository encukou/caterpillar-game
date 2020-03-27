import pyglet
import contextlib
import colorsys
import random

UP = 0, +1
DOWN = 0, -1
LEFT = -1, 0
RIGHT = +1, 0


@contextlib.contextmanager
def pushed_matrix():
    pyglet.gl.glPushMatrix()
    try:
        yield
    finally:
        pyglet.gl.glPopMatrix()


def lerp(a, b, t):
    return a * (1-t) + b * t


def flip(direction):
    x, y = direction
    return -x, -y

def get_color(hue, saturation=0.9):
    hue = decode_hue(hue)
    if hue is None:
        hue = saturation = 0
    return tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue, saturation, 1))


def encode_hue(hue):
    if hue is None or hue < 0:
        return ' '
    elif hue > 1:
        return '~'
    else:
        return chr(int(hue * (126 - 33)) + 33)

def decode_hue(char):
    if char == ' ':
        return None
    result = (ord(char) - 33) / (126 - 33)
    if result < 0:
        return -1
    if result > 1:
        return 1
    return result

def random_hue():
    return chr(random.randrange(32, 127))
