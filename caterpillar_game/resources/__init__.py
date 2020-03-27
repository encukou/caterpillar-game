import importlib.resources
import functools
import tempfile

import pyglet

TILE_WIDTH = 32
IMAGE_WIDTH = 64

BUTTERFLY_HEIGHT = 512

SPRITES = {
    'body': (0, 0),
    'head': (1, 0),
    'line': (2, 0),
    'coccoon_2': (4, 0),
    'coccoon_3': (5, 0),
    'coccoon_4': (6, 0),
    'solid': (7, 0),

    'flower': (1, 0),
    'grass': (1, 1),

    'egg': (0, 2),
    'egg-space': (1, 2),
    'butterfly': (2, 2),
    'map-icon': (3, 2),
    'butterfly-mini': (4, 2),
    'butterfly-oudent': (5, 2),
    'x': (6, 2),
    'up-on': (7, 2),
    'up-off': (8, 2),
    'down-on': (9, 2),
    'down-off': (10, 2),
    'go-on': (11, 2),
    'go-off': (12, 2),
    'go-enter': (13, 2),
    'spinner': (15, 2),

    'tile': (0, 4),
}

BUTTERFLY_ANCHORS = {
    'abdomen': 65/128,
    'thorax': 44/128,
    'head': 36/128,
    'eye': 36/128,
    'antenna': 33/128,
    'wing': 50/128,
    'x-wing': 4/128,
}

spritesheet_image = None
butterfly_images = {}


# Pyglet can only load fonts from an actual file
_font_file = tempfile.NamedTemporaryFile(suffix='Aldrich-Regular.ttf')
_font_file.write(importlib.resources.read_binary(__name__, 'Aldrich-Regular.ttf'))
pyglet.font.add_file(_font_file.name)
FONT = pyglet.font.load('Aldrich')

def get_spritesheet_image():
    global spritesheet_image
    if spritesheet_image is None:
        with importlib.resources.path(__name__, 'sprites.png') as p:
            spritesheet_image = pyglet.image.load(p)
    return spritesheet_image

@functools.lru_cache()
def get_image(name, anchor_x=0.5, anchor_y=0.5, width=1, height=1):
    try:
        x, y = SPRITES[name]
    except KeyError:
        x = name % 16
        y = name // 16
    region = get_spritesheet_image().get_region(
        x * IMAGE_WIDTH, y * IMAGE_WIDTH,
        width * IMAGE_WIDTH, height * IMAGE_WIDTH,
    )
    region.anchor_x = round(IMAGE_WIDTH * anchor_x)
    region.anchor_y = round(IMAGE_WIDTH * anchor_y)
    return region


def get_butterfly_image(name):
    try:
        return butterfly_images[name]
    except KeyError:
        with importlib.resources.path(__name__, f'{name}.png') as p:
            image = pyglet.image.load(p)
        image.anchor_x = image.width // 2
        y_anchor = BUTTERFLY_ANCHORS.get(name)
        image.anchor_y = int(image.height * (1 - y_anchor))
        butterfly_images[name] = image
        return image
