import array
import random

import pyglet

from .resources import get_image, TILE_WIDTH
from .util import pushed_matrix, UP, DOWN, LEFT, RIGHT
from .caterpillar import Caterpillar
from .coccoon import Cocoon
from . import tiles

SPEED = 2


class Grid:
    def __init__(self):
        self.width = 31
        self.height = 17
        self.tiles = {}
        self.caterpillar = Caterpillar(self)
        self.caterpillar_opacity = 255
        self.sprites = {}
        self.eol_tiles = []
        self.batch = pyglet.graphics.Batch()
        self.t = 0
        self.cocoon = None
        self.background = pyglet.image.TileableTexture. create_for_image(
            get_image('tile', 0, 0, 2, 2)
        )

        for x in range(self.width):
            for y in range(self.height):
                if random.randrange(7) < 2:
                    self[x, y] = 'grass'

        for x, y in (0, 2), (11, 5), (17, 5):
            self[x, y] = 'flower'

        for i in range(3, 5):
            self[self.caterpillar.segments[-1].x+i, self.caterpillar.segments[-1].y] = 'flower'
        for i in range(5):
            self.add_a_flower()
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

    def add_a_flower(self, grass_only=False):
        if grass_only == False:
            if self.add_a_flower(grass_only=True):
                return True
        xs = list(range(self.width))
        ys = list(range(self.width))
        random.shuffle(xs)
        random.shuffle(ys)
        caterpillar_xys = set(s.xy for s in self.caterpillar.segments)
        for x in xs:
            for y in ys:
                if (x, y) in caterpillar_xys:
                    continue
                tile = self.tiles.get((x, y))
                if tile is None:
                    if not grass_only:
                        self[x, y] = 'flower'
                        return True
                elif tile.grow_flower():
                    return True

    def draw(self):
        with pushed_matrix():
            pyglet.gl.glTranslatef(TILE_WIDTH/2, TILE_WIDTH/2, 1)
            pyglet.gl.glScalef(1/2, 1/2, 1)
            self.background.blit_tiled(
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
        self.t += dt
        self.caterpillar.tick(dt * SPEED)
        if self.cocoon:
            self.cocoon.tick(dt)
        self.eol_tiles = [tile for tile in self.eol_tiles if tile.tick(dt)]
        for tile in self.tiles.values():
            tile.tick(dt)

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
            return tiles.edge
        return self.tiles.get(x_y, tiles.empty)

    def __setitem__(self, x_y, item):
        eol_tile = self.tiles.pop(x_y, None)
        if eol_tile:
            self.eol_tiles.append(eol_tile)
            eol_tile.delete()
        x, y = x_y
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return
        if item is not None:
            self.tiles[x_y] = tiles.new(item, self, x, y)

    def add_cocoon(self, caterpillar):
        self.cocoon = Cocoon(self, caterpillar)
