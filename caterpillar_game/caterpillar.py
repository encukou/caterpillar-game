import dataclasses
import collections
import math
import random

import pyglet

from .resources import get_image, TILE_WIDTH
from .util import lerp

DIR_ANGLES = {
    (0, +1): 0,
    (+1, 0): 90,
    (0, -1): 180,
    (-1, 0): -90,
}


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
            sprite.x = self.x * TILE_WIDTH
            sprite.y = self.y * TILE_WIDTH
            sprite.scale = (t/2+1/2) * TILE_WIDTH / sprite.image.width
        else:
            sprite.x = lerp(self.from_x, self.x, t) * TILE_WIDTH
            sprite.y = lerp(self.from_y, self.y, t) * TILE_WIDTH
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
    def __init__(self, grid, egg, direction=(+1, 0)):
        self.cocooning = False
        self.cocooned = False
        self.grid = grid
        self.direction = direction
        self.egg = egg
        dx, dy = direction
        self.segments = collections.deque()
        self.segments.append(Segment.make_initial(
            grid.width // 2 - dx, grid.height // 2 - dy, self.direction,
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
        self.collected_hues = []

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
            sprite = self.sprites[-1-i]
            segment.update_sprite(
                sprite,
                t=t, ct=self.ct,
                is_head=(i == len(self.segments) - 1),
                i=i,
            )
            sprite.opacity = self.grid.caterpillar_opacity
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
        head_tile = self.grid[new_head.x, new_head.y]
        if head_tile.is_edge(self):
            xd, yd = self.direction
            possibilities = [(-yd, xd), (yd, -xd)]
            random.shuffle(possibilities)
            for nxd, nyd in possibilities:
                if not self.grid[head.x + nxd, head.y + nyd].is_edge(self):
                    self.turn((nxd, nyd))
                    return self.step(force_eat=force_eat)
        for segment in self.segments:
            if segment.xy == new_head.xy:
                new_head.look(segment.direction)
                self.cocooning = True
        self.segments.append(new_head)
        should_grow = head_tile.enter(self)
        if should_grow:
            self.segments[0].is_fresh_end = True
        else:
            self.segments.popleft()

    def make_butterfly(self):
        return self.egg.make_butterfly(self.collected_hues)
