import png
import importlib.resources
import colorsys
import array
import concurrent.futures
import time
import multiprocessing

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
    return wing_matrix.astype('uint16')

wing_matrix = get_wing_matrix()
wing_alpha = wing_matrix.sum(axis=2)
wing_where = wing_alpha > 0

wing_size = wing_matrix.shape[0]

WING_PIECE_COUNT = wing_matrix.shape[2]

# Using threads for CPU-bound task (numpy number crunching);
# use a relatively small number of threads
try:
    thread_count = multiprocessing.cpu_count() // 2
except NotImplementedError:
    thread_count = 0
if thread_count > 5:
    thread_count = 5
if thread_count < 1:
    thread_count = 1
pool = concurrent.futures.ThreadPoolExecutor(max_workers=thread_count)

def _get_array(hues):
    time.sleep(0)
    hues = list(hues)
    while len(hues) < WING_PIECE_COUNT:
        hues.append(0)
    colors = numpy.array([
        tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue, 0.9, 1)) + (255,)
        for i, hue in zip(range(WING_PIECE_COUNT), hues)
    ], dtype='uint16')
    size = wing_matrix.shape[0]
    colored = numpy.multiply(wing_matrix, colors, dtype='uint16')
    result = numpy.zeros((size, size, 4), dtype='uint16')
    numpy.floor_divide(colored.sum(axis=2), wing_alpha, out=result, where=wing_where)
    result = numpy.nan_to_num(result, 0)
    result = result.reshape(size, size * 4)
    result = result.astype('uint8')
    result = (pyglet.gl.GLubyte * result.size).from_buffer_copy(result.tobytes())
    return result

def get_wing_image(futures):
    if futures[1].done():
        return futures[1].result()
    if futures[0].done():
        image = pyglet.image.ImageData(
            wing_size, wing_size, 'RGBA', futures[0].result(),
        )
        image.anchor_y = int((1-resources.BUTTERFLY_ANCHORS['wing']) * wing_size)
        image.anchor_x = int((resources.BUTTERFLY_ANCHORS['x-wing']) * wing_size)
        futures[1].set_result(image)
        return image

def start_wing_generation(hues):
    future = pool.submit(_get_array, hues)
    return future, concurrent.futures.Future()
