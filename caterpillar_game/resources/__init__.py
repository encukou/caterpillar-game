import functools
import tempfile
import json

try:
    import importlib.resources as importlib_resources
except ImportError:
    import importlib_resources

import pyglet

TILE_WIDTH = 32
IMAGE_WIDTH = 64

BUTTERFLY_HEIGHT = 512

SPRITES = {
    'body': (0, 0),
    'head': (1, 0),
    'line': (2, 0),
    'asleep': (3, 0),
    'coccoon_2': (4, 0),
    'coccoon_3': (5, 0),
    'coccoon_4': (6, 0),
    'solid': (7, 0),
    'diamond-s': (9, 0),
    'apple': (10, 0),
    'diamond-w': (11, 0),
    'diamond-t': (12, 0),

    'flower-stem': (0, 1),
    'grass': (1, 1),
    'flower-petals': (3, 1),
    'flower-center': (4, 1),
    'boulder': (5, 1),
    'mushroom-s': (9, 1),
    'star': (10, 1),
    'mushroom-w': (11, 1),
    'mushroom-t': (12, 1),
    'key': (13, 1),
    'diamond': (14, 1),

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
    'spinner': (14, 2),

    'scared': (14, 3),
    'void': (15, 3),

    'tile': (0, 4),
    'crushed': (15, 4),

    'ampersand': (15, 5),

    'spent-key': (15, 6),
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
_font_file.write(importlib_resources.read_binary(__name__, 'Aldrich-Regular.ttf'))
pyglet.font.add_file(_font_file.name)
FONT = pyglet.font.load('Aldrich')

with importlib_resources.open_text(__name__, 'maps.json') as f:
    LEVELS = json.load(f)

class FONT_INFO:
    font_name = 'Aldrich'
    font_size = 29
    baseline = 2

    @classmethod
    def label_args(cls):
        return {'font_name': cls.font_name, 'font_size': cls.font_size}

class HALF_FONT_INFO(FONT_INFO):
    font_size = 29/2
    baseline = 1

def get_spritesheet_image():
    global spritesheet_image
    if spritesheet_image is None:
        with importlib_resources.path(__name__, 'sprites.png') as p:
            spritesheet_image = pyglet.image.load(p)
    return spritesheet_image

@functools.lru_cache()
def get_image(name, anchor_x=0.5, anchor_y=0.5, width=1, height=1):
    if isinstance(name, str) and name.startswith('key:'):
        name = 'key'
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
        with importlib_resources.path(__name__, f'{name}.png') as p:
            image = pyglet.image.load(p)
        image.anchor_x = image.width // 2
        y_anchor = BUTTERFLY_ANCHORS.get(name)
        image.anchor_y = int(image.height * (1 - y_anchor))
        butterfly_images[name] = image
        return image
