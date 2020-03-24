import png
import importlib.resources
import colorsys
import array

import pyglet
import numpy

from . import resources


def get_wing_matrix():
    """Return white wing matrix with axes (width, height, plane, channel)"""
    wing_matrix = numpy.frombuffer(
        importlib.resources.read_binary(resources, f'wings.dat'),
        dtype='uint8',
    )
    wing_matrix = wing_matrix.reshape(
        (-1, resources.BUTTERFLY_HEIGHT, resources.BUTTERFLY_HEIGHT),
    )
    wing_matrix = numpy.stack([wing_matrix] * 4, -1)
    wing_matrix = wing_matrix.transpose((1, 2, 0, 3))[::-1, ...]
    return wing_matrix

wing_matrix = get_wing_matrix()


def get_wing_image(hues):
    hues = list(hues)
    while len(hues) < resources.WING_COUNT:
        hues.append(0)
    colors = numpy.array([
        tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue, 0.9, 1)) + (255,)
        for i, hue in zip(range(resources.WING_COUNT), hues)
    ], dtype='uint8')
    plain = get_wing_matrix()
    size = plain.shape[0]
    colored = numpy.multiply(plain, colors, dtype='uint16')
    result = colored.sum(axis=2) // plain.sum(axis=2)
    result = numpy.nan_to_num(result, 0)
    result = result.reshape(size, size * 4)
    result = result.astype('uint8')
    image = pyglet.image.ImageData(
        size, size, 'RGBA',
        (pyglet.gl.GLubyte * result.size)(*result.tobytes()),
    )
    image.anchor_y = int((1-resources.BUTTERFLY_ANCHORS['wing']) * size)
    image.anchor_x = int((resources.BUTTERFLY_ANCHORS['x-wing']) * size)
    return image
