import importlib.resources

import pyglet

TILE_WIDTH = 32
IMAGE_WIDTH = 64

SPRITES = {
    'body': (0, 0),
    'head': (1, 0),
}

spritesheet_image = None

def get_spritesheet_image():
    global spritesheet_image
    if spritesheet_image is None:
        with importlib.resources.path(__name__, 'sprites.png') as p:
            spritesheet_image = pyglet.image.load(p)
    return spritesheet_image

def get_image(name):
    try:
        x, y = SPRITES[name]
    except KeyError:
        x = name % 16
        y = name // 16
    region = get_spritesheet_image().get_region(
        x * IMAGE_WIDTH, y * IMAGE_WIDTH, IMAGE_WIDTH, IMAGE_WIDTH,
    )
    region.anchor_x = IMAGE_WIDTH//2
    region.anchor_y = IMAGE_WIDTH//2
    return region
