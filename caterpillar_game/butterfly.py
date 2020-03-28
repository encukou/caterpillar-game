import random
import math
import time

import pyglet

from .resources import get_butterfly_image, get_image
from .resources import BUTTERFLY_ANCHORS, BUTTERFLY_HEIGHT
from .wing import start_wing_generation, get_wing_image, WING_PATCH_COUNT
from .util import random_hue

BODY_COLOR = (61, 43, 6)

class Demo:
    def __init__(self):
        self.butterflies = [
            ButterflySprite(
                Butterfly(''.join(
                    random_hue()
                    for i in range(WING_PATCH_COUNT)
                )),
                x=512, y=356,
            )
        ]*0
        self.bg = pyglet.sprite.Sprite(get_image('solid'))
        self.bg.color = 200, 200, 200
        self.bg.scale = 100
        self.t = 0
        '''
        coords = [(x, y) for x in range(10) for y in range(10)]
        random.shuffle(coords)
        for x, y in coords:
            butterfly = ButterflySprite(
                Butterfly(''.join(
                    random_hue()
                    for i in range(WING_PATCH_COUNT)
                )),
                scale=0.1,
                x=x*102+51, y=y*57+35,
            )
            self.butterflies.append(butterfly)
        '''
        _b = {}
        for y in range(10):
            x = 0
            if y == 0:
                butterfly = Butterfly(' ' * WING_PATCH_COUNT)
            else:
                butterfly = Butterfly(random_hue() * WING_PATCH_COUNT)
            sprite = ButterflySprite(
                butterfly,
                scale=0.1,
                x=x*102+51, y=y*57+35,
            )
            self.butterflies.append(sprite)
            _b[x, y] = butterfly

        for x in range(1, 10):
            plus_hues = ''.join(
                random_hue() for i in range(WING_PATCH_COUNT)
            )
            ys = list(range(10))
            random.shuffle(ys)
            for y in ys:
                from .egg import Egg
                if x % 2:
                    d = -1
                else:
                    d = 1
                butterfly = Egg([_b[x-1, y], _b[x-1, (y+d)%10]]).make_butterfly(plus_hues)
                sprite = ButterflySprite(
                    butterfly,
                    scale=0.1,
                    x=x*102+51, y=y*57+35,
                )
                self.butterflies.append(sprite)
                _b[x, y] = butterfly

    def tick(self, dt):
        if dt > 0.5:
            return
        self.t += dt

    def draw(self):
        self.bg.draw()
        for i, butterfly in enumerate(reversed(self.butterflies)):
            butterfly.draw(self.t + i * 1/9 * (1 + i*0.01), partial=i%7==0)

class Butterfly:
    def __init__(self, hues=' ' * WING_PATCH_COUNT):
        self.hues = hues

    def to_dict(self):
        return {
            'wing': str(self.hues),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(hues=data.get('wing', ' '*WING_PATCH_COUNT))


class ButterflySprite:
    def __init__(self, butterfly, x=0, y=0, scale=1, wing_t=0):
        self.wing_batch = pyglet.graphics.Batch()
        self.body_batch = pyglet.graphics.Batch()
        self.sprites = []
        self.wing_sprite = None
        for name in 'abdomen', 'thorax', 'head', 'antenna', 'eye':
            sprite = pyglet.sprite.Sprite(
                get_butterfly_image(name),
                batch=self.body_batch,
            )
            sprite.y = (
                BUTTERFLY_ANCHORS['wing']-BUTTERFLY_ANCHORS[name]
            ) * BUTTERFLY_HEIGHT
            sprite.color = BODY_COLOR
            self.sprites.append(sprite)
        self.scale = scale
        self.x = x
        self.y = y
        self.wing_t = wing_t
        self.wing_gen = start_wing_generation(butterfly.hues)
        self.alive_since = None

    @property
    def is_done(self):
        return self.wing_sprite or get_wing_image(self.wing_gen)

    @property
    def age(self):
        if self.alive_since is None:
            return 0
        return time.time() - self.alive_since

    def draw(self, t=None, partial=False):
        if t is None:
            t = self.wing_t
        t = t % 2
        if t > 1:
            t = 2 - t
        if not self.wing_sprite:
            image = get_wing_image(self.wing_gen)
            if image is None:
                if not partial:
                    return
            else:
                self.wing_sprite = pyglet.sprite.Sprite(
                    image, batch=self.wing_batch,
                )
                self.sprites.append(self.wing_sprite)
                self.alive_since = time.time()
        #age = self.age
        #if self.age < 1:
        #    t = min(1-self.age, t)
        wing_scale = 1 - abs(math.sin(t*math.tau/4))**3 * 0.99
        x_wing = BUTTERFLY_ANCHORS['x-wing'] * BUTTERFLY_HEIGHT
        pyglet.gl.glPushMatrix()
        try:
            pyglet.gl.glTranslatef(self.x, self.y, 0)
            pyglet.gl.glScalef(self.scale, self.scale, 1)
            self.body_batch.draw()
            pyglet.gl.glTranslatef(x_wing, 0, 0)
            pyglet.gl.glScalef(wing_scale, 1, 1)
            self.wing_batch.draw()
            pyglet.gl.glTranslatef(-2 * x_wing / wing_scale, 0, 0)
            pyglet.gl.glScalef(-1, 1, 1)
            self.wing_batch.draw()
        finally:
            pyglet.gl.glPopMatrix()
