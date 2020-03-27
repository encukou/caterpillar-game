import array
import random

import pyglet

from .resources import get_image, TILE_WIDTH
from .util import pushed_matrix, UP, DOWN, LEFT, RIGHT
from .caterpillar import Caterpillar
from .coccoon import Cocoon

SPEED = 2


class Grid:
    def __init__(self):
        self.width = 31
        self.height = 17
        self.map = array.array('b', [0] * self.width * self.height)
        self.caterpillar = Caterpillar(self)
        self.caterpillar_opacity = 255
        self.sprites = {}
        self.batch = pyglet.graphics.Batch()
        self.cocoon = None
        self.tiles = pyglet.image.TileableTexture. create_for_image(
            get_image('tile', 0, 0, 2, 2)
        )

        self[0, 2] = 16
        self[11, 5] = 16
        self[12, 5] = 16
        self[13, 5] = 16
        self[14, 5] = 16
        self[15, 5] = 16
        self[16, 5] = 16
        self[17, 5] = 16

        for i in range(1, 11):
            self[self.caterpillar.segments[-1].x+i, self.caterpillar.segments[-1].y] = 16
        for i, d in enumerate((
            #DOWN,
            #DOWN, DOWN, LEFT, LEFT, UP, UP, LEFT, LEFT, LEFT, LEFT, DOWN, DOWN,
            #RIGHT, RIGHT, DOWN, DOWN, LEFT, LEFT, DOWN, DOWN, DOWN, DOWN,
            #RIGHT, RIGHT, UP, UP, RIGHT, RIGHT, DOWN, DOWN, RIGHT, RIGHT, RIGHT, RIGHT,
            #UP, UP, LEFT, LEFT, UP, UP, RIGHT, RIGHT, UP, UP, UP, #LEFT
            #UP, UP, UP, *[LEFT]*10, *[DOWN]*1, *[RIGHT]*7, DOWN
        )):
            self.caterpillar.turn(d)
            self.caterpillar.step(force_eat=i>2)


    def draw(self):
        with pushed_matrix():
            pyglet.gl.glTranslatef(TILE_WIDTH/2, TILE_WIDTH/2, 1)
            pyglet.gl.glScalef(1/2, 1/2, 1)
            self.tiles.blit_tiled(
                0, 0, 0,
                self.width * TILE_WIDTH * 2, self.height * TILE_WIDTH * 2,
            )
            pyglet.gl.glScalef(2, 2, 1)
            pyglet.gl.glTranslatef(TILE_WIDTH/2, TILE_WIDTH/2, 0)
            self.batch.draw()
            self.caterpillar.draw()
            if self.cocoon:
                self.cocoon.draw()

    def tick(self, dt):
        self.caterpillar.tick(dt * SPEED)
        if self.cocoon:
            self.cocoon.tick(dt)

    def handle_command(self, command):
        if command == 'up':
            self.caterpillar.turn(UP)
        elif command == 'down':
            self.caterpillar.turn(DOWN)
        elif command == 'left':
            self.caterpillar.turn(LEFT)
        elif command == 'right':
            self.caterpillar.turn(RIGHT)

    def __getitem__(self, x_y):
        x, y = x_y
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return 0
        return self.map[y * self.width + x]

    def __setitem__(self, x_y, item):
        x, y = x_y
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return
        self.map[y * self.width + x] = item
        sprite = self.sprites.get(x_y)
        if sprite and not item:
            self.sprites.pop(x_y).delete()
        elif item and not sprite:
            sprite = self.sprites[x, y] = pyglet.sprite.Sprite(
                get_image(item),
                x=x * TILE_WIDTH, y=y * TILE_WIDTH,
                batch=self.batch,
            )
            sprite.scale = TILE_WIDTH / sprite.width
        elif item:
            sprite.image = get_image(item)

    def add_cocoon(self, caterpillar):
        self.cocoon = Cocoon(self, caterpillar)
