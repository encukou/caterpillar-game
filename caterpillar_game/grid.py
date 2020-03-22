import array
import dataclasses
import collections
import math
import random
from heapq import heappush, heappop

import pyglet
from bresenham import bresenham

from .resources import get_image, TILE_WIDTH

SPEED = 2
WEAVE_SPEED = 50

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
        self.edge_tiles = set()
        self.lines = []
        self.t = 0

        self.batch = pyglet.graphics.Batch()
        self.line_batch = pyglet.graphics.Batch()
        self.sprites = []

        self.sprite_color = 0, 100, 0

        coccooning = False
        self.cocoon_tiles = cocoon_tiles = {}
        head = caterpillar.segments[-1]
        xs = set()
        ys = set()
        for segment in caterpillar.segments:
            xy = segment.xy
            if coccooning:
                x, y = xy
                self.edge_tiles.add(xy)
                xs.add(x)
                ys.add(y)
                cocoon_tiles[x, y] = {
                    segment.direction, flip(segment.from_direction)
                }
            if xy == head.xy:
                coccooning = True

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
            tile_name, tile_rotation = COCCOON_TILES.get(
                frozenset(dirs), 'solid'
            )
            sprite = pyglet.sprite.Sprite(
                get_image(tile_name),
                x=(x+1) * TILE_WIDTH,
                y=(y+1) * TILE_WIDTH,
                batch=self.batch,
            )
            sprite.scale = TILE_WIDTH / sprite.width
            sprite.color = self.sprite_color
            sprite.rotation = tile_rotation
            sprite.opacity = 100
            self.sprites.append(sprite)

        self.green_t, self.white_t, self.end_t = self.add_lines()

    def add_lines(self):
        edges = list(self.edge_tiles)
        heads = [(0.5 * WEAVE_SPEED, self.caterpillar.segments[-1].xy, (0, 0))]
        new_head_counter = 5
        covered = set()
        for i in range(300):
            if not heads:
                break
            best_coords = None
            pos, start, fuzz = heappop(heads)
            for i in range(7):
                sx, sy = start
                candidate_coords = cx, cy = random.choice(edges)
                sq_distance = abs(sx - cx) ** 2 + abs(sy - cy) ** 2
                if (
                    (best_coords is None or sq_distance > best_sq_distance)
                    and start != candidate_coords
                    and (start, candidate_coords) not in covered
                    and self.bresenham_check(start, candidate_coords)
                ):
                    best_sq_distance = sq_distance
                    best_coords = candidate_coords
            if best_coords is not None:
                distance = math.sqrt(best_sq_distance)
                bx, by = best_coords
                fx, fy = fuzz
                new_fuzz = random.uniform(-.5, .5), random.uniform(-.5, .5)
                nfx, nfy = new_fuzz
                self.lines.append(CocoonLine(
                    self,
                    (sx + fx, sy + fy),
                    (bx + nfx, by + nfy),
                    start_t=pos,
                    duration=distance,
                    batch=self.line_batch,
                    length=distance,
                ))
                new_head_counter -= 1
                covered.add((start, best_coords))
                covered.add((best_coords, start))
                if new_head_counter <= 0:
                    heappush(heads, (pos+distance, best_coords, new_fuzz))
                    new_head_counter = 5
                heappush(heads, (pos+distance, best_coords, new_fuzz))
        if not heads:
            return 1, 2, 2.2
        pos, start, fuzz = heappop(heads)
        end = pos / WEAVE_SPEED
        return end + 1, end + 1.5, end + 1.6

    def bresenham_check(self, start, end):
        for x, y in bresenham(*start, *end):
            if (x, y) not in self.cocoon_tiles:
                return False
        return True

    def draw(self):
        self.update_sprites()
        self.batch.draw()
        for line in self.lines:
            line.update_sprite(self.t)
        self.line_batch.draw()

    def update_sprites(self):
        t = self.t
        if t < self.green_t:
            t /= self.green_t
            op = int(255 * t)
            for sprite in self.sprites:
                sprite.opacity = op
            return
        for sprite in self.sprites:
            sprite.opacity = 255
        if t < self.white_t:
            t -= self.green_t
            t /= (self.white_t - self.green_t)
            a = int(lerp(0, 255, t))
            b = int(lerp(100, 255, t))
            self.sprite_color = sprite_color = a, b, a
            for sprite in self.sprites:
                sprite.color = sprite_color
            return
        self.sprite_color = sprite_color = 255, 255, 255
        for sprite in self.sprites:
            sprite.color = sprite_color

    def tick(self, dt):
        self.t += dt

class CocoonLine:
    def __init__(self, cocoon, start, end, start_t, duration, batch, length):
        self.cocoon = cocoon
        self.sx, self.sy = start
        self.ex, self.ey = end
        self.start_t = start_t
        self.duration = duration + 0.1
        self.length = length
        self.sprite = sprite = pyglet.sprite.Sprite(
            get_image('line', 0.5, 0),
            x=(self.sx+1) * TILE_WIDTH,
            y=(self.sy+1) * TILE_WIDTH,
            batch=batch,
        )
        sprite.rotation = 90 - math.degrees(math.atan2(
            self.ey - self.sy, self.ex - self.sx
        ))
        sprite.scale_x = TILE_WIDTH / 5 / sprite.image.width
        sprite.scale_y = 0
        sprite.color = 255, 255, 255
        self.max_sprite_scale = length * TILE_WIDTH / sprite.image.width

    def update_sprite(self, t):
        t *= WEAVE_SPEED
        t -= self.start_t
        if t < 0:
            return
        t /= self.duration
        if t > 1:
            self.sprite.scale_y = self.max_sprite_scale
        else:
            self.sprite.scale_y = t * self.max_sprite_scale

        t -= 1
        if t < 0:
            self.sprite.color = 255, 255, 255
        elif t > 1:
            self.sprite.color = self.cocoon.sprite_color
        else:
            cr, cg, cb = self.cocoon.sprite_color
            lr = lerp(255, cr, t)
            lg = lerp(255, cg, t)
            lb = lerp(255, cb, t)
            self.sprite.color = lr, lg, lb
