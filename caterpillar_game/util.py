import pyglet
import contextlib

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
