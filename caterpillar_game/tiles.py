import dataclasses
import random

import pyglet

from .resources import get_image, TILE_WIDTH
from .util import UP, DOWN, LEFT, RIGHT, get_color, lerp, random_hue, flip

@dataclasses.dataclass
class Tile:
    grid: object
    x: int
    y: int
    props: dict = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        self.active = True
        self.prepare_sprite()
        self.prepare()

    def prepare(self):
        pass

    def prepare_sprite(self):
        if 'sprite' in self.props:
            self.sprite = self.make_sprite()

    def delete(self):
        self.active = False

    def tick(self, dt):
        pass

    def is_edge(self, caterpillar):
        return False

    def enter(self, caterpillar):
        return False

    def make_sprite(self, image=None, **kwargs):
        if image == None:
            image = get_image(self.props['sprite'])
        kwargs.setdefault('x', self.x * TILE_WIDTH)
        kwargs.setdefault('y', self.y * TILE_WIDTH)
        kwargs.setdefault('batch', self.grid.batch)
        sprite = pyglet.sprite.Sprite(image, **kwargs)
        sprite.scale = 1/2
        return sprite

    def grow_flower(self):
        return False

    def attempt_turn(self, caterpillar, new_direction):
        return True

    def launch(self, caterpillar):
        return False

    def is_water(self, caterpillar):
        return False

    def coccoon_info(self):
        return None, 0


empty = Tile(None, -1, -1)

class Edge(Tile):
    def is_edge(self, caterpillar):
        return True

    def enter(self, caterpillar):
        caterpillar.die('crash', '''
            Out of the box? Keep to thinking.
            It's the edge of the world as we know it.
            Grow some wings first.
            The next world is waiting...
            No new butterfly today.
        ''')

edge = Edge(None, -1, -1)

groups = [pyglet.graphics.OrderedGroup(i) for i in range(4)]

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

class EdibleTile(Tile):
    def prepare(self):
        self.end_t = None

    def enter(self, caterpillar):
        self.grid[self.x, self.y] = None
        return True

    def delete(self):
        self.end_t = self.grid.t

    def tick(self, dt):
        if self.end_t is not None:
            t = (self.grid.t - self.end_t) * 2
            if t > 1:
                self.sprite.delete()
                self.sprite = None
                return False
            self.sprite.scale = (1 - t) / 2
            return True

@register('grass')
@register('_')
class Grass(EdibleTile):
    def prepare(self):
        self.end_t = None
        self.flower = None

    def prepare_sprite(self):
        self.sprite = self.make_sprite(get_image('grass'), group=groups[0])

    def enter(self, caterpillar):
        if self.flower:
            return self.flower.enter(caterpillar, from_grass=True)
        super().enter(caterpillar)
        if random.randrange(3) == 0:
            self.grid.add_a_flower(grass_only=True)
        self.grid.score(1, self.x, self.y)
        return True

    def delete(self):
        super().delete()
        if self.flower:
            self.flower.delete()

    def tick(self, dt):
        if self.flower:
            self.flower.tick(dt)
        return super().tick(dt)

    def grow_flower(self):
        if self.flower:
            return False
        self.flower = Flower(self.grid, self.x, self.y)
        return True


@register('flower')
class Flower(EdibleTile):
    def prepare(self):
        self.start_t = self.grid.t
        self.end_t = None
        self.grown = False
        self.hue = random_hue()
        self.stem_sprite = self.make_sprite(
            get_image('flower-stem', anchor_y=1/8),
            y = (self.y - 3/8) * TILE_WIDTH,
            group=groups[1],
        )
        self.petals_sprite = self.make_sprite(
            get_image('flower-petals'),
            group=groups[2],
            y = (self.y + 1/8) * TILE_WIDTH,
        )
        self.petals_sprite.color = get_color(self.hue, 0.5)
        self.center_sprite = self.make_sprite(
            get_image('flower-center'),
            group=groups[3],
            y = (self.y + 1/8) * TILE_WIDTH,
        )
        self.center_sprite.color = get_color(self.hue, 0.2)

    def enter(self, caterpillar, from_grass=False):
        super().enter(caterpillar)
        caterpillar.collected_hues.append(self.hue)
        self.grid.add_a_flower()
        if random.randrange(3) == 0:
            self.grid.add_a_flower(grass_only=True)
        if from_grass:
            self.grid.score(10, self.x, self.y)
        else:
            self.grid.score(9, self.x, self.y)
        return True

    def tick(self, dt):
        self.petals_sprite.rotation += dt * 40
        if self.end_t is not None:
            t = (self.grid.t - self.end_t) * 2
            if t > 1:
                self.stem_sprite.delete()
                self.petals_sprite.delete()
                self.center_sprite.delete()
                return False
            scale = (1 - t) / 2
            self.stem_sprite.scale_y = scale
            self.petals_sprite.scale = scale
            self.center_sprite.scale = scale
            return True
        elif not self.grown:
            t = self.grid.t - self.start_t
            if t > 1:
                t = 1
                self.grown = True
            scale = t / 2
            self.stem_sprite.scale_y = scale
            self.petals_sprite.scale = scale
            self.center_sprite.scale = scale
            y = (self.y + lerp(-3/8, 1/8, t)) * TILE_WIDTH
            self.petals_sprite.y = y
            self.center_sprite.y = y

@register('≈')
class Water(Tile):
    def enter(self, caterpillar):
        if caterpillar.swimming:
            return
        if caterpillar.use('mushroom-w'):
            caterpillar.utter('WHOA!')
            caterpillar.swimming = True
            return
        caterpillar.die('drown', '''
            Hmm... What's drown here?
            You met with a watery fate.
            Frogs gotta eat, too.
            No mushrooms left for crossing.
            No new butterfly today.
        ''')

    def is_water(self, caterpillar):
        return True

@register('#')
class Abyss(Tile):
    def enter(self, caterpillar):
        caterpillar.die('fall', '''
            That's a long way down.
            Should have brought a parachute.
            Bats gotta eat, too.
            One level down?
            Plunge in with reckless Abaddon.
        ''')

@register('%')
class Boulder(Tile):
    def prepare(self):
        super().prepare()
        self.sprites = []

    def enter(self, caterpillar):
        if caterpillar.use('mushroom-s'):
            caterpillar.grid[self.x, self.y] = None
            caterpillar.utter('HYIAH!')
            self.end_t = self.grid.t
            N = 5
            self.sprites = []
            image = get_image('boulder')
            for x in range(N):
                for y in range(N):
                    sprite = pyglet.sprite.Sprite(
                        image.get_region(
                            x * image.width//N,
                            y * image.height//N,
                            image.width//N,
                            image.height//N,
                        ),
                        batch=self.grid.batch,
                    )
                    sprite.start_x = (self.x + x/N - 1/2) * TILE_WIDTH
                    sprite.start_y = (self.y + y/N - 1/2) * TILE_WIDTH
                    sprite.end_x = (
                        (self.x + x/N - 1/2)
                        + random.gauss(x-N/2, 7)
                        + caterpillar.direction[0] * 2
                    ) * TILE_WIDTH
                    sprite.end_y = (
                        (self.y + y/N - 1/2)
                        + random.gauss(y-N/2, 7)
                        + caterpillar.direction[1] * 2
                    ) * TILE_WIDTH
                    sprite.rot_speed = random.uniform(-360, 360)
                    self.sprites.append(sprite)
            self.sprite.image = get_image('grass')
            self.sprite.start_x = self.sprite.x
            self.sprite.start_y = self.sprite.y
            self.sprite.end_x = self.sprite.x+1
            self.sprite.end_y = self.sprite.y+1
            self.sprite.rot_speed = 10
            self.sprites.append(self.sprite)
        else:
            caterpillar.die('crash', '''
                Can't eat that!
                You ran into a boulder.
                Squished by a boulder.
                This is too heavy!
                An impassable boulder blocks the way.
                Do caterpillars really need gravestones?
                No new butterfly today.
                Grow some wings first.
                Birds gotta eat, too.
                Ouch!
            ''')

    def tick(self, dt):
        if self.sprites:
            t = self.grid.t - self.end_t
            if t < 1:
                for sprite in self.sprites:
                    sprite.x = lerp(sprite.start_x, sprite.end_x, t)
                    sprite.y = lerp(sprite.start_y, sprite.end_y, t)
                    sprite.rotation = sprite.rot_speed * t
                    sprite.opacity = (1 - t)**2 * 255
                return True

    def coccoon_info(self):
        return 'boulder', 10

@register('w')
class BubblyMushroom(EdibleTile):
    def enter(self, caterpillar):
        super().enter(caterpillar)
        if caterpillar.collect('mushroom-w'):
            caterpillar.utter('YOU FEEL LIGHTER')

@register('t')
class SoporificMushroom(EdibleTile):
    def enter(self, caterpillar):
        super().enter(caterpillar)
        caterpillar.pause('Z')

@register('s')
class StrengthMushroom(EdibleTile):
    def enter(self, caterpillar):
        super().enter(caterpillar)
        if 'boulder' in caterpillar.collected_items:
            caterpillar.collect('mushroom-s')
            caterpillar.utter('YOU FEEL STRONGER')
        else:
            caterpillar.pause('?')

@register('S')
@register('T')
@register('W')
class Diamond(Tile):
    def prepare(self):
        self.sprite = self.make_sprite()

    def enter(self, caterpillar):
        caterpillar.die('crash', '''
            Can't eat that!
            You ran into a diamond.
            This is too hard!
            Gemstone turned gravestone.
            No new butterfly today.
            Tough luck.
        ''')

    def coccoon_info(self):
        return 'diamond-' + self.props['str'].lower(), 1000

@register('$')
class Apple(EdibleTile):
    def enter(self, caterpillar):
        super().enter(caterpillar)
        if caterpillar.collect('apple'):
            caterpillar.utter('YUM!')

@register('*')
class Star(Tile):
    def enter(self, caterpillar):
        caterpillar.die('crash', '''
            You met with a starry fate.
            This is too pointy!
            Should have gone around it.
            This is solider than it looked!
        ''')

    def coccoon_info(self):
        return 'star', 500

@register('>')
@register('<')
@register('^')
@register('v')
class ArrowPad(Tile):
    def prepare(self):
        self.direction = self.props['dx'], self.props['dy']

    def enter(self, caterpillar):
        caterpillar.turn(self.direction)

    def attempt_turn(self, caterpillar, new_direction):
        return new_direction == self.direction

    def is_edge(self, caterpillar):
        return caterpillar.direction == flip(self.direction)

@register('→')
@register('←')
@register('↑')
@register('↓')
class Launcher(ArrowPad):
    def launch(self, caterpillar):
        return True

@register('K')
class Key(Tile):
    def prepare_sprite(self):
        self.gold = not self.grid.state.have_key_for(self.props["opens"])
        if self.gold:
            self.sprite = self.make_sprite(get_image('key'))
        else:
            self.sprite = self.make_sprite(get_image('spent-key'))

    def enter(self, caterpillar):
        caterpillar.die('crash', '''
            Can't eat that!
            It's shiny, but apparently not edible.
            Keys are not part of a balanced diet.
            Should have gone around it.
            That's too heavy to eat.
        ''')

    def coccoon_info(self):
        self.sprite.image = get_image('spent-key')
        return f'key:{self.props["opens"]}', 100
