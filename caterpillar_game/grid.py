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


class Grid:
    def __init__(self):
        self.width = 31
        self.height = 17
        self.map = array.array('b', [0] * self.width * self.height)
        self.caterpillar = Caterpillar(self)
        self.sprites = {}
        self.batch = pyglet.graphics.Batch()
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

    def draw(self):
        self.batch.draw()
        self.caterpillar.draw()

    def tick(self, dt):
        self.caterpillar.move(dt * SPEED)

    def handle_command(self, command):
        if command == 'up':
            self.caterpillar.turn((0, +1))
        elif command == 'down':
            self.caterpillar.turn((0, -1))
        elif command == 'left':
            self.caterpillar.turn((-1, 0))
        elif command == 'right':
            self.caterpillar.turn((+1, 0))

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


def lerp(a, b, t):
    return a * (1-t) + b * t


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
        self.grid = grid
        self.direction = direction
        dx, dy = direction
        self.segments = collections.deque()
        self.segments.append(Segment.make_initial(
            grid.width // 2, grid.height // 2, self.direction,
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
        x, y = direction
        head = self.segments[-1]
        fx, fy = head.from_direction
        if x != -fx or y != -fy:
            self.direction = direction
            self.segments[-1].look(direction)

    def move(self, dt):
        if self.cocooning:
            self.ct += dt
            self.t += dt
            if self.t > 0.5:
                self.t = 0.5
        else:
            while self.t + dt > 1:
                dt -= 1
                self.step()
            self.t += dt

    def step(self):
        head = self.segments[-1]
        new_head = head.grow_head(self.direction)
        for segment in self.segments:
            if segment.xy == new_head.xy:
                self.cocooning = True
        self.segments.append(new_head)
        if self.grid[new_head.x, new_head.y] == 16:
            self.grid[new_head.x, new_head.y] = 0
            self.segments[0].is_fresh_end = True
        else:
            self.segments.popleft()
