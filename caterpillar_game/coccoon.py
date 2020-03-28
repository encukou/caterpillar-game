import random
import math
from heapq import heappush, heappop

import pyglet
from bresenham import bresenham

from .resources import get_image, TILE_WIDTH
from .util import lerp, flip, UP, DOWN, LEFT, RIGHT
from .butterfly import ButterflySprite

WEAVE_SPEED = 50


COCCOON_TILES = {
    frozenset({RIGHT, DOWN}): ('coccoon_2', 0),
    frozenset({DOWN, LEFT}): ('coccoon_2', 90),
    frozenset({LEFT, UP}): ('coccoon_2', 180),
    frozenset({UP, RIGHT}): ('coccoon_2', 270),
    frozenset({RIGHT, DOWN, LEFT}): ('coccoon_3', 0),
    frozenset({DOWN, LEFT, UP}): ('coccoon_3', 90),
    frozenset({LEFT, UP, RIGHT}): ('coccoon_3', 180),
    frozenset({UP, RIGHT, DOWN}): ('coccoon_3', 270),
    frozenset({LEFT, UP, RIGHT, DOWN}): ('solid', 0),
}

class Cocoon:
    def __init__(self, grid, caterpillar):
        self.grid = grid
        self.caterpillar = caterpillar
        self.butterfly = caterpillar.make_butterfly()
        self.butterfly_sprite = ButterflySprite(self.butterfly, scale=0)
        self.edge_tiles = set()
        self.lines = []
        self.t = 0
        self.last_score_t = 0

        self.batch = pyglet.graphics.Batch()
        self.line_batch = pyglet.graphics.Batch()
        self.sprites = []
        self.pending_scores = []

        self.sprite_color = 0, 100, 0
        self.web_opacity = 255

        self.cocoon_tiles = cocoon_tiles = {}
        head = caterpillar.segments[-1]
        xs = set()
        ys = set()
        for cocooning in False, True:
            for segment in caterpillar.segments:
                xy = segment.xy
                if cocooning:
                    x, y = xy
                    self.edge_tiles.add(xy)
                    xs.add(x)
                    ys.add(y)
                    cocoon_tiles[x, y] = {
                        segment.direction, flip(segment.from_direction)
                    }
                if xy == head.xy:
                    cocooning = True
            if ys:
                break

        self.green_t, self.white_t, self.end_t = 1, 2, 2.2

        if not ys:
            print('OOPS!')
            self.xmean = self.ymean = 0
            self.update_t()

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

        self.xmean = sum(xs) / len(xs)
        self.ymean = sum(ys) / len(ys)
        for (x, y), dirs in cocoon_tiles.items():
            tile_name, tile_rotation = COCCOON_TILES.get(
                frozenset(dirs), ('solid', 0)
            )
            sprite = pyglet.sprite.Sprite(
                get_image(tile_name),
                x=x * TILE_WIDTH,
                y=y * TILE_WIDTH,
                batch=self.batch,
            )
            sprite.scale = TILE_WIDTH / sprite.width
            sprite.color = self.sprite_color
            sprite.rotation = tile_rotation
            sprite.opacity = 100
            sprite._caterpillar_rotation = random.gauss(0, 2) * 180
            sprite._caterpillar_orig_x = sprite.x
            sprite._caterpillar_orig_y = sprite.y
            for i in range(20):
                sx = random.gauss(x-self.xmean, 1) * 300
                sy = random.gauss(y-self.ymean, 1) * 300
                sprite._caterpillar_speed_x = sx
                sprite._caterpillar_speed_y = sy
                if sx + sy > 300:
                    break
            self.sprites.append(sprite)

            score = 4
            if (x, y) in self.edge_tiles:
                score += 10
            self.pending_scores.append((score, x, y))

        for segment in caterpillar.segments:
            if segment.xy not in cocoon_tiles:
                self.pending_scores.append((-10, segment.x, segment.y))

        self.green_t, self.white_t, self.end_t = self.add_lines()
        random.shuffle(self.pending_scores)
        self.update_t()

    def update_t(self):
        self.butterfly_t = math.ceil((self.end_t + 1/2) / 2) * 2 + 1
        self.bflexit_t = self.butterfly_t + 1

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
            for i in range(20):
                sx, sy = start
                candidate_coords = cx, cy = random.choice(edges)
                sq_distance = abs(sx - cx) ** 2 + abs(sy - cy) ** 2
                if (
                    (best_coords is None or sq_distance > best_sq_distance)
                    and sq_distance
                    and start != candidate_coords
                    and (start, candidate_coords) not in covered
                    and self.bresenham_check(start, candidate_coords)
                ):
                    best_sq_distance = sq_distance
                    best_coords = candidate_coords
            if best_coords is not None:
                distance = math.sqrt(best_sq_distance)
                duration = math.log(distance) / math.log(1.4)
                if duration < 0.01:
                    duration = 0.01
                bx, by = best_coords
                fx, fy = fuzz
                new_fuzz = random.uniform(-.5, .5), random.uniform(-.5, .5)
                nfx, nfy = new_fuzz
                self.lines.append(CocoonLine(
                    self,
                    (sx + fx, sy + fy),
                    (bx + nfx, by + nfy),
                    start_t=pos,
                    duration=duration,
                    batch=self.line_batch,
                    length=distance,
                ))
                new_head_counter -= 1
                covered.add((start, best_coords))
                covered.add((best_coords, start))
                if new_head_counter <= 0:
                    heappush(heads, (pos+duration, best_coords, new_fuzz))
                    new_head_counter = 5
                heappush(heads, (pos+duration, best_coords, new_fuzz))
        if not heads:
            return 1, 2, 2.2
        pos, start, fuzz = heappop(heads)
        end = pos / WEAVE_SPEED
        return end + 1, end + 1.5, end + 5

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
        if self.butterfly_sprite.scale:
            self.butterfly_sprite.draw()

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
            if self.pending_scores:
                self.white_t += 1/2
                self.end_t += 1/2
                self.green_t += 1/2
                self.update_t()
                return
            t -= self.green_t
            t /= (self.white_t - self.green_t)
            a = int(lerp(0, 255, t))
            b = int(lerp(100, 255, t))
            self.sprite_color = sprite_color = a, b, a
            for sprite in self.sprites:
                sprite.color = sprite_color
            self.web_opacity = lerp(255, 0, t)
            self.grid.caterpillar_opacity = lerp(255, 0, t)
            return
        self.sprite_color = sprite_color = 255, 255, 255
        self.web_opacity = 0
        self.grid.caterpillar_opacity = 0
        for sprite in self.sprites:
            sprite.color = sprite_color
        self.anim_butterfly(t)
        if t < self.end_t:
            t -= self.white_t
            t /= (self.end_t - self.white_t)
            for sprite in self.sprites:
                sprite.x = sprite._caterpillar_orig_x + t * sprite._caterpillar_speed_x
                sprite.y = sprite._caterpillar_orig_y + t * sprite._caterpillar_speed_y
                sprite.rotation = t * sprite._caterpillar_rotation
                sprite.opacity = lerp(255, 0, t**5)
            return
        for sprite in self.sprites:
            sprite.opacity = 0

    def tick(self, dt):
        self.t += dt
        if self.pending_scores:
            self.last_score_t += dt
            while self.last_score_t > 0.05 and self.pending_scores:
                self.last_score_t -= 0.05
                self.grid.score(*self.pending_scores.pop())

    def anim_butterfly(self, t):
        t -= self.white_t
        self.butterfly_sprite.wing_t = t
        if t < 2:
            t /= 2
            self.butterfly_sprite.scale = t
            self.butterfly_sprite.x = lerp(self.xmean, self.grid.width/2-1/2, t) * TILE_WIDTH
            self.butterfly_sprite.y = lerp(self.ymean, self.grid.height/2+1, t) * TILE_WIDTH
            return
        self.butterfly_sprite.x = (self.grid.width/2-1/2) * TILE_WIDTH
        self.butterfly_sprite.y = (self.grid.height/2+1) * TILE_WIDTH
        self.butterfly_sprite.scale = 1
        t -= 4
        if t < 0:
            return
        if t < 2:
            t /= 2
            self.butterfly_sprite.scale = lerp(1, 1/20, t)
            self.butterfly_sprite.x = lerp(self.grid.width/2-1/2, 3.2, t) * TILE_WIDTH
            self.butterfly_sprite.y = lerp(self.grid.height/2+1, 16, t) * TILE_WIDTH
            return
        t -= 4
        self.butterfly_sprite.scale = 1/20
        self.butterfly_sprite.x = 3.2 * TILE_WIDTH
        self.butterfly_sprite.y = 16 * TILE_WIDTH
        if t < 0:
            return
        self.butterfly_sprite.wing_t = 0
        self.grid.signal_done()

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
            x=self.sx * TILE_WIDTH,
            y=self.sy * TILE_WIDTH,
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

        self.sprite.opacity = self.cocoon.web_opacity
