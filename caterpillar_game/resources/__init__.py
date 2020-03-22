import importlib.resources

import pyglet

TILE_WIDTH = 64

SPRITES = {
    'body': (0, 0),
}

spritesheet_image = None

def get_spritesheet_image():
    global spritesheet_image
    if spritesheet_image is None:
        with importlib.resources.path(__name__, 'sprites.png') as p:
            spritesheet_image = pyglet.image.load(p)
    return spritesheet_image

def get_image(name):
    x, y = SPRITES[name]
    return get_spritesheet_image().get_region(
        x * TILE_WIDTH, y * TILE_WIDTH, TILE_WIDTH, TILE_WIDTH,
    )
