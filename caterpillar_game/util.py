import pyglet
import contextlib


@contextlib.contextmanager
def pushed_matrix():
    pyglet.gl.glPushMatrix()
    try:
        yield
    finally:
        pyglet.gl.glPopMatrix()
