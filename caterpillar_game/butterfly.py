import random
import math

import pyglet

from .resources import get_butterfly_image, get_image, BUTTERFLY_ANCHORS, WING_COUNT
from .wing import get_wing_image

BODY_COLOR = (61, 43, 6)

class Demo:
    def __init__(self):
        self.butterflies = [Butterfly([
            random.uniform(0, 1)
            for i in range(WING_COUNT)
        ]) for i in range(1)]
        self.bg = pyglet.sprite.Sprite(get_image('solid'))
        self.bg.color = 200, 200, 200
        self.bg.scale = 100
        self.t = 0

    def tick(self, dt):
        self.t += dt

    def draw(self):
        self.bg.draw()
        for butterfly in self.butterflies:
            butterfly.draw(max(-1, min(self.t-1.1, 0)))


class Butterfly:
    def __init__(self, hues):
        self.wing_batch = pyglet.graphics.Batch()
        self.body_batch = pyglet.graphics.Batch()
        self.sprites = []
        sprite = pyglet.sprite.Sprite(
            get_wing_image(hues),
            batch=self.wing_batch,
        )
        self.size = sprite.height
        self.sprites.append(sprite)
        for name in 'abdomen', 'thorax', 'head', 'antenna', 'eye':
            sprite = pyglet.sprite.Sprite(
                get_butterfly_image(name),
                batch=self.body_batch,
            )
            sprite.y = (BUTTERFLY_ANCHORS['wing']-BUTTERFLY_ANCHORS[name])*self.size
            sprite.color = BODY_COLOR
            self.sprites.append(sprite)

    def draw(self, t=0):
        scale = abs(math.cos(t*math.tau/4))**3 * 0.99 + 0.01
        x_wing = BUTTERFLY_ANCHORS['x-wing'] * self.size
        pyglet.gl.glPushMatrix()
        try:
            pyglet.gl.glTranslatef(512, 356, 0)
            self.body_batch.draw()
            pyglet.gl.glTranslatef(x_wing, 0, 0)
            pyglet.gl.glScalef(scale, 1, 1)
            self.wing_batch.draw()
            pyglet.gl.glTranslatef(-2 * x_wing / scale, 0, 0)
            pyglet.gl.glScalef(-1, 1, 1)
            self.wing_batch.draw()
        finally:
            pyglet.gl.glPopMatrix()
