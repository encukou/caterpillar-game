import dataclasses
import collections
import math
import random
import sys

import pyglet

from .resources import get_image, TILE_WIDTH
from .util import lerp

DEBUG = 'megahit' in sys.argv

DIR_ANGLES = {
    (0, +1): 0,
    (+1, 0): 90,
    (0, -1): 180,
    (-1, 0): -90,
}

def get_dir_angle(direction):
    try:
        return DIR_ANGLES[direction]
    except KeyError:
        x, y = direction
        return 90-math.degrees(math.atan2(y, x))


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
        self.from_angle = get_dir_angle(self.from_direction)
        self.visible = True
        self.launched = False
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
        to_angle = get_dir_angle(self.direction)
        while self.from_angle + 180 < to_angle:
            self.from_angle += 360
        while self.from_angle - 180 > to_angle:
            self.from_angle -= 360

    def update_sprite(self, sprite, t, is_head, i, fate, ct):
        if not self.visible:
            return
        if fate == 'crash' and is_head:
            if self.launched:
                t *= 1.5
            else:
                t *= 0.5
            if ct:
                cct = ct
                if ct > 0.5:
                    sprite.image = get_image('crushed')
                    cct = 0.5
                if self.launched:
                    cct /= 4
                sprite.scale_x = 1 + cct / 4
                sprite.scale_y = 1 - cct / 2
        if fate == 'drown' and is_head and ct > 1:
            lt = t - (t/1.5)**3
            sprite.x = lerp(self.from_x, self.x, lt) * TILE_WIDTH
            sprite.y = lerp(self.from_y, self.y, lt) * TILE_WIDTH
            sprite.scale = (1-t) * TILE_WIDTH / sprite.image.width
        elif fate == 'unsail' and ct > 1:
            ct -= 1
            ct /= 4
            lt = 1 - (1 - ct) ** 2
            sprite.x = lerp(self.from_x, self.x, 1+lt/3) * TILE_WIDTH
            sprite.y = lerp(self.from_y, self.y, 1+lt/3) * TILE_WIDTH
            if self.direction[1]:
                sprite.x += + math.sin(t*6) * ct * TILE_WIDTH / (i % 2 * 16 - 8)
            else:
                sprite.y += + math.sin(t*6) * ct * TILE_WIDTH / (i % 2 * 16 - 8)
            if ct > 1:
                sprite.scale = 0
            else:
                sprite.scale = (1-lt) * TILE_WIDTH / sprite.image.width
        elif fate == 'fall' and is_head and ct > 1:
            sprite.x = lerp(self.from_x, self.x, t/6) * TILE_WIDTH
            sprite.y = lerp(self.from_y, self.y, t/6) * TILE_WIDTH
            sprite.scale = (1-t) * TILE_WIDTH / sprite.image.width
        elif self.is_fresh_end:
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
        if fate == 'fall' and is_head:
            wiggle *= 4 * (t+1)
        sprite.rotation = lerp(
            self.from_angle, get_dir_angle(self.direction), t
        ) + math.sin(t * math.tau * 2) * wiggle
        if ct:
            if fate == 'cocooning':
                if ct > 1:
                    ct = 1
                if not is_head:
                    sprite.rotation += ct * 90
                sprite.color = 0, lerp(255, 100, ct), 0
        if self.launched:
            if fate == 'crash':
                t *= 1.2
            amount = (1 - (1-2*t)**2)
            sprite.y += amount * TILE_WIDTH * 2 / 3


class Caterpillar:
    def __init__(self, grid, egg, direction=(+1, 0), x=None, y=None):
        self.cocooned = False
        self.fate = None
        self.moving = True
        self.paused = False
        self.grid = grid
        self.direction = direction
        self.pause_label = None
        self.swimming = False
        self.egg = egg
        self.zt = 0
        dx, dy = direction
        self.segments = collections.deque()
        self.segments.append(Segment.make_initial(
            (grid.width // 2 if x is None else x) + dx,
            (grid.height // 2 if y is None else y) + dy,
            self.direction,
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
        self.collected_items = set()
        
        self.collect('boulder')

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
            is_head = (i == len(self.segments) - 1)
            segment.update_sprite(
                sprite,
                t=t, ct=self.ct,
                is_head=is_head,
                fate=self.fate,
                i=i,
            )
            if segment.visible:
                sprite.opacity = self.grid.caterpillar_opacity
            else:
                sprite.opacity = False
            if is_head:
                can_swim = 'mushroom-w' in self.collected_items
                can_bash = 'mushroom-s' in self.collected_items
                if can_swim and can_bash:
                    sprite.color = 150, 200, 200
                elif can_swim:
                    sprite.color = 0, 255, 200
                elif can_bash:
                    sprite.color = 150, 200, 150
                else:
                    sprite.color = 100, 255, 0
            else:
                sprite.color = 100, 255, 0
        self.batch.draw()
        if DEBUG:
            sprite = pyglet.sprite.Sprite(
                get_image('solid'),
                x=self.segments[-1].x * TILE_WIDTH,
                y=self.segments[-1].y * TILE_WIDTH,
            )
            sprite.scale = len(self.segments)
            sprite.opacity = 100
            sprite.draw()

    def turn(self, direction):
        if self.fate:
            return
        if self.swimming:
            return
        x, y = direction
        head = self.segments[-1]
        fx, fy = head.from_direction
        turning_back = x == -fx and y == -fy
        if self.paused and not turning_back:
            self.paused = False
            self.moving = True
            self.pause_label = None
            self.sprites[0].image = self.head_image
        if not self.moving:
            return
        if not self.grid[head.xy].attempt_turn(self, direction):
            return
        if not turning_back or len(self.segments) == 1:
            self.direction = direction
            head.look(direction)

    def tick(self, dt):
        if DEBUG:
            dt *= 4
        if self.fate:
            self.ct += dt
        if self.pause_label:
            self.zt += dt * 3
            head = self.segments[-1]
            while self.zt > 1:
                self.zt -= 1
                self.utter(self.pause_label, 1, 1)
        if self.paused:
            dt *= (1 - self.t/2)
            if self.t + dt > 0.75:
                self.moving = False
        if not self.moving:
            self.t += dt
            if self.paused:
                threshold = 0.9
            else:
                threshold = 0.5
            if self.t > threshold:
                self.t = threshold
                if self.fate == 'cocooning' and not self.cocooned:
                    self.cocooned = True
                    self.grid.add_cocoon(self)
        else:
            while self.t + dt > 1:
                dt -= 1
                self.step()
            self.t += dt

    def step(self, force_eat=False, recursing=False):
        head = self.segments[-1]
        direction = self.direction
        launched = False
        if self.grid[head.xy].launch(self):
            x, y = direction
            x *= 2
            y *= 2
            phantom_segment = head.grow_head(direction)
            self.segments.append(phantom_segment)
            phantom_segment.visible = False
            direction = x, y
            launched = True
        new_head = head.grow_head(direction)
        new_head.launched = launched
        head_tile = self.grid[new_head.x, new_head.y]
        if head_tile.is_edge(self) and not recursing:
            xd, yd = direction
            possibilities = [(-yd, xd), (yd, -xd)]
            random.shuffle(possibilities)
            for nxd, nyd in possibilities:
                if not self.grid[head.x + nxd, head.y + nyd].is_edge(self):
                    self.turn((nxd, nyd))
                    return self.step(force_eat=force_eat, recursing=True)
        if self.swimming and not head_tile.is_water(self):
            self.swimming = False
        if not self.fate:
            for segment in self.segments:
                if segment.xy == new_head.xy and segment.visible:
                    new_head.look(segment.direction)
                    self.fate = 'cocooning'
                    self.moving = False
        if self.fate in ('drown', 'fall'):
            if self.ct < 1.5:
                self.segments.append(new_head)
            else:
                self.sprites[0].image = self.head_image = self.body_image
            if len(self.segments) > 1:
                self.segments.popleft()
            else:
                self.segments[0].visible = False
        elif self.fate and self.fate != 'cocooning':
            pass
        else:
            self.segments.append(new_head)
            if self.fate == 'cocooning':
                should_grow = True
            else:
                should_grow = head_tile.enter(self)
            if should_grow:
                self.segments[0].is_fresh_end = True
            else:
                self.segments.popleft()
                if len(self.segments) > 1 and not self.segments[0].visible:
                    self.segments.popleft()
                if self.swimming:
                    on_dry_land = False
                    for segment in self.segments:
                        if not self.grid[segment.xy].is_water(self):
                            on_dry_land = True
                            break
                    if not on_dry_land:
                        self.die('unsail', """
                            Sailing is over.
                            That bridge is too short.
                            Dreaming of underwater butterflies?
                            Fishes gotta eat, too!
                            Pray to the Drowned God.
                            Disqualified for underwater recovery.
                            Finding Nemo?
                            That went swimmingly... Not.
                        """)
        if DEBUG and not self.swimming and not self.fate:
            self.pause('.')

    def make_butterfly(self):
        return self.egg.make_butterfly(self.collected_hues)

    def die(self, fate, messages):
        self.fate = fate
        if fate not in ('drown', 'fall', 'unsail'):
            self.moving = False
        self.grid.signal_game_over(
            random.choice(messages.strip().splitlines()).strip()
        )
        self.sprites[0].image = get_image('scared')

    def pause(self, label=None):
        self.sprites[0].image = get_image('asleep')
        self.paused = True
        self.pause_label = label

    def collect(self, item):
        added = item not in self.collected_items
        self.collected_items.add(item)
        self.grid.update_collected(self)
        if self.collected_items.issuperset({'star', 'apple'}):
            self.collected_items.add('ampersand')
            self.grid.update_collected(self)
        return added

    def use(self, item):
        if item in self.collected_items:
            self.collected_items.remove(item)
            self.grid.update_collected(self)
            return True
        return False

    def utter(self, utterance, randomize_x=0, randomize_y=0):
        head = self.segments[-1]
        self.grid.add_label(utterance,
            head.x + random.gauss(0, 1/3) * randomize_x,
            head.y + random.random() / 2 * randomize_y,
        )
