import random
import colorsys
import math

import pyglet

from .resources import WING_COUNT, get_butterfly_image, get_image, BUTTERFLY_ANCHORS

BODY_COLOR = (61, 43, 6)

class Demo:
    def __init__(self):
        self.butterfly = Butterfly([
            random.uniform(0, 1)
            for i in range(WING_COUNT)
        ])
        self.bg = pyglet.sprite.Sprite(get_image('solid'))
        self.bg.color = 200, 200, 200
        self.bg.scale = 100
        self.t = 0

    def tick(self, dt):
        self.t += dt

    def draw(self):
        self.bg.draw()
        self.butterfly.draw(self.t)


class Butterfly:
    def __init__(self, hues):
        self.colors = [
            tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue, 0.9, 1))
            for hue in hues
        ]
        while len(hues) > WING_COUNT:
            hues.pop()
        while len(hues) < WING_COUNT:
            hues.append((255, 255, 255))
        print(self.colors)
        self.wing_batch = pyglet.graphics.Batch()
        self.body_batch = pyglet.graphics.Batch()
        self.sprites = []
        for i, color in enumerate(self.colors):
            sprite = pyglet.sprite.Sprite(
                get_butterfly_image(i),
                batch=self.wing_batch,
            )
            sprite.color = color
            self.sprites.append(sprite)
        for name in 'abdomen', 'thorax', 'head', 'antenna', 'eye':
            sprite = pyglet.sprite.Sprite(
                get_butterfly_image(name),
                batch=self.body_batch,
                y=(BUTTERFLY_ANCHORS['wing']-BUTTERFLY_ANCHORS[name])*2
            )
            sprite.color = BODY_COLOR
            self.sprites.append(sprite)

    def draw(self, t=0):
        pyglet.gl.glPushMatrix()
        try:
            pyglet.gl.glTranslatef(512, 256, 0)
            self.body_batch.draw()
            pyglet.gl.glScalef(1-abs(math.cos(t))**3 * 0.95 + 0.05, 1, 1)
            self.wing_batch.draw()
        finally:
            pyglet.gl.glPopMatrix()
