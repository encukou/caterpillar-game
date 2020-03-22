import importlib.resources
import functools

import pyglet

TILE_WIDTH = 32
IMAGE_WIDTH = 64

SPRITES = {
    'body': (0, 0),
    'head': (1, 0),
    'solid': (2, 0),
    'debugarrow': (3, 0),
    'coccoon_2': (4, 0),
    'coccoon_3': (5, 0),
    'coccoon_4': (6, 0),
    'line': (7, 0),
}

spritesheet_image = None

def get_spritesheet_image():
    global spritesheet_image
    if spritesheet_image is None:
        with importlib.resources.path(__name__, 'sprites.png') as p:
            spritesheet_image = pyglet.image.load(p)
    return spritesheet_image

@functools.lru_cache()
def get_image(name, anchor_x=0.5, anchor_y=0.5):
    try:
        x, y = SPRITES[name]
    except KeyError:
        x = name % 16
        y = name // 16
    region = get_spritesheet_image().get_region(
        x * IMAGE_WIDTH, y * IMAGE_WIDTH, IMAGE_WIDTH, IMAGE_WIDTH,
    )
    region.anchor_x = round(IMAGE_WIDTH * anchor_x)
    region.anchor_y = round(IMAGE_WIDTH * anchor_y)
    return region
