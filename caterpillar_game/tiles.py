import dataclasses

import pyglet

from .resources import get_image, TILE_WIDTH
from .util import UP, DOWN, LEFT, RIGHT

@dataclasses.dataclass
class Tile:
    grid: object
    x: int
    y: int

    def __post_init__(self):
        self.active = True
        self.prepare()

    def prepare(self):
        pass

    def delete(self):
        self.active = False

    def eol_tick(self, dt):
        pass

    def is_edge(self, caterpillar):
        return False

    def enter(self, caterpillar):
        return False

    def make_sprite(self, image, **kwargs):
        kwargs.setdefault('x', self.x * TILE_WIDTH)
        kwargs.setdefault('y', self.y * TILE_WIDTH)
        kwargs.setdefault('batch', self.grid.batch)
        sprite = pyglet.sprite.Sprite(image, **kwargs)
        sprite.scale = 1/2
        return sprite


empty = Tile(None, -1, -1)

class Edge(Tile):
    def is_edge(self, caterpillar):
        return True

edge = Edge(None, -1, -1)

tile_classes = {}

def new(name, grid, x, y):
    cls = tile_classes[name]
    tile = cls(grid, x, y)
    return tile

def register(name):
    def _decorator(cls):
        tile_classes[name] = cls
        return cls
    return _decorator

@register('grass')
class Grass(Tile):
    def prepare(self):
        self.sprite = self.make_sprite(get_image('grass'))

    def enter(self, caterpillar):
        self.grid[self.x, self.y] = None
        return True

    def delete(self):
        self.end_t = self.grid.t

    def eol_tick(self, dt):
        t = self.grid.t - self.end_t
        if t > 1:
            self.sprite.delete()
            self.sprite = None
            return False
        self.sprite.scale = (1 - t) / 2
        return True


@register('flower')
class Flower(Tile):
    pass
