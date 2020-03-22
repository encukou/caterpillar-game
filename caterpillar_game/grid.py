import array
import dataclasses
import collections
import math

import pyglet

from .resources import get_image, TILE_WIDTH

SPEED = 2

DIR_ANGLES = {
    (0, +1): 0,
    (0, -1): 180,
    (+1, 0): 90,
    (-1, 0): -90,
}

UP = 0, +1
DOWN = 0, -1
LEFT = -1, 0
RIGHT = +1, 0


COCCOON_TILES = {
    frozenset({UP, RIGHT}): ('coccoon_2', 0),
    frozenset({RIGHT, DOWN}): ('coccoon_2', 90),
    frozenset({DOWN, LEFT}): ('coccoon_2', 180),
    frozenset({LEFT, UP}): ('coccoon_2', 270),
    frozenset({LEFT, UP, RIGHT}): ('coccoon_3', 0),
    frozenset({UP, RIGHT, DOWN}): ('coccoon_3', 90),
    frozenset({RIGHT, DOWN, LEFT}): ('coccoon_3', 180),
    frozenset({DOWN, LEFT, UP}): ('coccoon_3', 270),
    frozenset({LEFT, UP, RIGHT, DOWN}): ('solid', 0),
}


class Grid:
    def __init__(self):
        self.width = 31
        self.height = 17
        self.map = array.array('b', [0] * self.width * self.height)
        self.caterpillar = Caterpillar(self)
        self.sprites = {}
        self.batch = pyglet.graphics.Batch()
        self.cocoon = None
        for x in range(self.width):
            for y in range(self.height):
                if (x + y) % 2:
                    self[x, y] = 17
        self[0, 2] = 16
        self[10, 5] = 16
        self[11, 5] = 16
        self[12, 5] = 16
        self[13, 5] = 16
        self[14, 5] = 16
        self[15, 5] = 16
        self[16, 5] = 16
        self[17, 5] = 16

        for i in range(11):
            self[self.caterpillar.segments[-1].x+i, self.caterpillar.segments[-1].y] = 16
        for i in range(10):
            self.caterpillar.step()
        for d in (
            DOWN,
            DOWN, DOWN, LEFT, LEFT, UP, UP, LEFT, LEFT, LEFT, LEFT, DOWN, DOWN,
            RIGHT, RIGHT, DOWN, DOWN, LEFT, LEFT, DOWN, DOWN, DOWN, DOWN,
            RIGHT, RIGHT, UP, UP, RIGHT, RIGHT, DOWN, DOWN, RIGHT, RIGHT, RIGHT, RIGHT,
            UP, UP, LEFT, LEFT, UP, UP, RIGHT, RIGHT, UP, UP, UP, LEFT
        ):
            self.caterpillar.turn(d)
            self.caterpillar.step(force_eat=True)


    def draw(self):
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
                x=(x+1) * TILE_WIDTH, y=(y+1) * TILE_WIDTH,
                batch=self.batch,
            )
            sprite.scale = TILE_WIDTH / sprite.width
        elif item:
            sprite.image = get_image(item)

    def add_cocoon(self, caterpillar):
        self.cocoon = Cocoon(self, caterpillar)


def lerp(a, b, t):
    return a * (1-t) + b * t


def flip(direction):
    x, y = direction
    return -x, -y


@dataclasses.dataclass
class Segment:
    x: int
    y: int
    direction: tuple
    from_x: int
    from_y: int
    from_direction: tuple

    def __post_init__(self):
        self.xy = self.x, self.y
        self.is_fresh_end = False
        self.from_angle = DIR_ANGLES[self.from_direction]
        self.adjust_from_angle()

    @classmethod
    def make_initial(cls, x, y, direction):
        dx, dy = direction
        return cls(
            x=x, y=y, direction=direction,
            from_x=x - dx, from_y=y - dy, from_direction=direction,
        )

    def grow_head(self, direction):
        dx, dy = direction
        seg = Segment(
            x=self.x + dx,
            y=self.y + dy,
            direction=direction,
            from_x=self.x,
            from_y=self.y,
            from_direction=self.direction,
        )
        seg.adjust_from_angle()
        return seg

    def look(self, direction):
        self.direction = direction
        self.adjust_from_angle()

    def adjust_from_angle(self):
        to_angle = DIR_ANGLES[self.direction]
        while self.from_angle + 180 < to_angle:
            self.from_angle += 360
        while self.from_angle - 180 > to_angle:
            self.from_angle -= 360

    def update_sprite(self, sprite, t, is_head, i, ct):
        if self.is_fresh_end:
            sprite.x = (self.x+1) * TILE_WIDTH
            sprite.y = (self.y+1) * TILE_WIDTH
            sprite.scale = (t/2+1/2) * TILE_WIDTH / sprite.image.width
        else:
            sprite.x = (lerp(self.from_x, self.x, t)+1) * TILE_WIDTH
            sprite.y = (lerp(self.from_y, self.y, t)+1) * TILE_WIDTH
            sprite.scale = TILE_WIDTH / sprite.image.width
        if is_head:
            wiggle = 2
        else:
            wiggle = i % 2 * 20 - 10
        sprite.rotation = lerp(
            self.from_angle, DIR_ANGLES[self.direction], t
        ) + math.sin(t * math.tau * 2) * wiggle
        if ct:
            if ct > 1:
                ct = 1
            if not is_head:
                sprite.rotation += ct * 90
            sprite.color = 0, lerp(255, 100, ct), 0


class Caterpillar:
    def __init__(self, grid, direction=(+1, 0)):
        self.cocooning = False
        self.cocooned = False
        self.grid = grid
        self.direction = direction
        dx, dy = direction
        self.segments = collections.deque()
        self.segments.append(Segment.make_initial(
            grid.width // 2, grid.height // 2+3, self.direction,
        ))
        self.body_image = get_image('body')
        self.head_image = get_image('head')
        self.t = 0
        self.ct = 0
        self.batch = pyglet.graphics.Batch()
        sprite = pyglet.sprite.Sprite(
            self.head_image,
            batch=self.batch,
        )
        sprite.color = 0, 255, 0
        sprite.scale = TILE_WIDTH / sprite.width
        self.sprites = [sprite]

    def draw(self):
        while len(self.sprites) < len(self.segments):
            sprite = pyglet.sprite.Sprite(
                self.body_image,
                batch=self.batch,
            )
            sprite.scale = TILE_WIDTH / sprite.width
            sprite.color = 0, 255, 0
            self.sprites.append(sprite)
        while len(self.sprites) > len(self.segments):
            self.sprites.pop().delete()
        t = self.t
        for i, segment in enumerate(self.segments):
            segment.update_sprite(
                self.sprites[-1-i],
                t=t, ct=self.ct,
                is_head=(i == len(self.segments) - 1),
                i=i,
            )
        self.batch.draw()

    def turn(self, direction):
        if not self.cocooning:
            x, y = direction
            head = self.segments[-1]
            fx, fy = head.from_direction
            if x != -fx or y != -fy:
                self.direction = direction
                self.segments[-1].look(direction)

    def tick(self, dt):
        if self.cocooning:
            self.ct += dt
            self.t += dt
            if self.t > 0.5:
                self.t = 0.5
                if not self.cocooned:
                    self.cocooned = True
                    self.grid.add_cocoon(self)
        else:
            while self.t + dt > 1:
                dt -= 1
                self.step()
            self.t += dt

    def step(self, force_eat=False):
        head = self.segments[-1]
        new_head = head.grow_head(self.direction)
        for segment in self.segments:
            if segment.xy == new_head.xy:
                new_head.look(segment.from_direction)
                self.cocooning = True
        self.segments.append(new_head)
        if self.grid[new_head.x, new_head.y] == 16 or force_eat:
            self.grid[new_head.x, new_head.y] = 0
            self.segments[0].is_fresh_end = True
        else:
            self.segments.popleft()

class Cocoon:
    def __init__(self, grid, caterpillar):
        self.grid = grid
        self.caterpillar = caterpillar
        self.lines = []
        self.t = 0

        self.batch = pyglet.graphics.Batch()
        self.debug_batch = pyglet.graphics.Batch()
        self.sprites = []

        counting = False
        counted = []
        cocoon_tiles = {}
        head = caterpillar.segments[-1]
        xs = set()
        ys = set()
        for segment in caterpillar.segments:
            if counting:
                x, y = segment.xy
                xs.add(x)
                ys.add(y)
                cocoon_tiles[x, y] = {
                    segment.direction, flip(segment.from_direction)
                }
                counted.append((
                    x, y,
                    {segment.direction, flip(segment.from_direction)},
                ))
                for direction in segment.direction, flip(segment.from_direction):
                    sprite = pyglet.sprite.Sprite(
                        get_image('debugarrow'),
                        x=(x+1) * TILE_WIDTH,
                        y=(y+1) * TILE_WIDTH,
                        batch=self.batch,
                    )
                    sprite.scale = TILE_WIDTH / sprite.width
                    sprite.color = 100, 255, 100
                    sprite.rotation = DIR_ANGLES[direction]
                    self.sprites.append(sprite)
            if segment.xy == head.xy:
                counting = True

        if not ys:
            return

        for y in range(min(ys), max(ys)+1):
            filling = set()
            for x in range(min(xs), max(xs)+1):
                d = cocoon_tiles.get((x, y))
                prev_filling = filling
                if d:
                    filling = filling ^ (d & {UP, DOWN})
                    d |= filling
                elif filling:
                    d = cocoon_tiles[x, y] = {UP, DOWN}
                if d:
                    if prev_filling:
                        d.add(LEFT)
                    if filling:
                        d.add(RIGHT)

        for (x, y), dirs in cocoon_tiles.items():
            tile_name, tile_rotation = COCCOON_TILES.get(frozenset(dirs), 'solid')
            sprite = pyglet.sprite.Sprite(
                get_image(tile_name),
                x=(x+1) * TILE_WIDTH,
                y=(y+1) * TILE_WIDTH,
                batch=self.batch,
            )
            sprite.scale = TILE_WIDTH / sprite.width
            sprite.color = 100, 255, 255
            sprite.rotation = tile_rotation
            sprite.opacity = 200
            self.sprites.append(sprite)


            for f in dirs:
                    sprite = pyglet.sprite.Sprite(
                        get_image('debugarrow'),
                        x=(x+1) * TILE_WIDTH,
                        y=(y+1) * TILE_WIDTH,
                        batch=self.debug_batch,
                    )
                    sprite.scale = TILE_WIDTH / sprite.width
                    sprite.rotation = DIR_ANGLES[f]
                    self.sprites.append(sprite)

    def draw(self):
        self.batch.draw()
        self.debug_batch.draw()

    def tick(self, dt):
        self.t += dt
