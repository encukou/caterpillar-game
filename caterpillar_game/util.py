import pyglet
import contextlib
import colorsys

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
    return tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue, saturation, 1))

