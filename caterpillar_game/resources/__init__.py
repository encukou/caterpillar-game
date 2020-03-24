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

BUTTERFLY_ANCHORS = {
    'abdomen': 65,
    'thorax': 44,
    'head': 36,
    'eye': 36,
    'antenna': 33,
    'wing': 50,
}

WING_COUNT = int(importlib.resources.read_text(__name__, 'wingcount.txt'))

spritesheet_image = None
butterfly_images = {}

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


def get_butterfly_image(name):
    try:
        return butterfly_images[name]
    except KeyError:
        if isinstance(name, int):
            name = f'wing{name:02d}'
        with importlib.resources.path(__name__, f'{name}.png') as p:
            image = pyglet.image.load(p)
        image.anchor_x = image.width // 2
        y_anchor = BUTTERFLY_ANCHORS.get(name) or BUTTERFLY_ANCHORS['wing']
        image.anchor_y = image.height // 128 * (128 - y_anchor)
        butterfly_images[name] = image
        return image
