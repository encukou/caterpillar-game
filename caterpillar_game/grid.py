import array
import random
import math

import pyglet

from .resources import get_image, TILE_WIDTH, HALF_FONT_INFO
from .util import pushed_matrix, UP, DOWN, LEFT, RIGHT
from .caterpillar import Caterpillar
from .coccoon import Cocoon
from .level import load_level_to_grid
from . import tiles

SPEED = 2


class Grid:
    def __init__(self, state, egg=None, level=0):
        self.state = state
        self.egg = egg
        self.width = 31
        self.height = 17
        self.tiles = {}
        self.caterpillar = None
        self.caterpillar_opacity = 255
        self.sprites = {}
        self.eol_tiles = []
        self.batch = pyglet.graphics.Batch()
        self.score_batch = pyglet.graphics.Batch()
        self.displayed_score = 0
        self.t = 0
        self.gameover_t = None
        self.total_score = 0
        self.score_labels = []
        self.cocoon = None
        self.done = False
        self.background = pyglet.image.TileableTexture. create_for_image(
            get_image('tile', 0, 0, 2, 2)
        )
        self.level = level
        self.autogrow_flowers = True
        if level == 0:
            self.add_caterpillar()
            self.init_level0()
        else:
            load_level_to_grid(level, self)

        self.main_score_label = pyglet.text.Label(
            f'',
            **HALF_FONT_INFO.label_args(),
            anchor_x='right',
            anchor_y='baseline',
            align='center',
            batch=self.score_batch,
            x=(self.width - .5) * TILE_WIDTH,
            y=(self.height - .5) * TILE_WIDTH + HALF_FONT_INFO.baseline,
        )
        self.gameover_label = pyglet.text.Label(
            f'',
            **HALF_FONT_INFO.label_args(),
            anchor_x='left',
            anchor_y='baseline',
            align='center',
            batch=self.score_batch,
            color=(0, 0, 0, 0),
            x=-.5 * TILE_WIDTH,
            y=(self.height - .5) * TILE_WIDTH + HALF_FONT_INFO.baseline,
        )

        self.t = 1
        if self.caterpillar is None:
            self.add_caterpillar()

    def add_caterpillar(self, x=None, y=None, direction=(1, 0)):
        self.caterpillar = Caterpillar(
            self, self.egg or self.state.choose_egg(),
            x=x, y=y, direction=direction,
        )

    def init_level0(self):
        for x in range(self.width):
            for y in range(self.height):
                if random.randrange(7) < 2:
                    self[x, y] = 'grass'

        for x, y in (0, 2), (11, 5), (17, 5):
            self[x, y] = 'flower'

        head_x, head_y = self.caterpillar.segments[-1].xy
        self[head_x - 1, head_y] = None
        self[head_x + 0, head_y] = None
        self[head_x + 1, head_y] = 'grass'
        self[head_x + 2, head_y] = 'grass'
        self[head_x + 2, head_y].grow_flower()
        self[head_x + 3, head_y] = None
        self[head_x + 0, head_y - 1] = 'grass'
        self[head_x + 0, head_y + 1] = 'grass'

        for i, d in enumerate((
            #RIGHT, RIGHT, RIGHT, RIGHT, RIGHT, RIGHT, RIGHT,
            #RIGHT, RIGHT, RIGHT, RIGHT, RIGHT, RIGHT, RIGHT,
            #DOWN, LEFT, UP,
            #DOWN, DOWN, LEFT, LEFT, UP, UP, LEFT, LEFT, LEFT, LEFT, DOWN, DOWN,
            #RIGHT, RIGHT, DOWN, DOWN, LEFT, LEFT, DOWN, DOWN, DOWN, DOWN,
            #RIGHT, RIGHT, UP, UP, RIGHT, RIGHT, #DOWN, DOWN, RIGHT, RIGHT, RIGHT, RIGHT,
            #UP, UP, LEFT, LEFT, UP, UP, RIGHT, RIGHT, UP, UP, UP, #LEFT
            #UP, UP, UP, *[LEFT]*10, *[DOWN]*1, *[RIGHT]*7, DOWN
        )):
            self.caterpillar.turn(d)
            self.caterpillar.step(force_eat=i>2)

    def add_a_flower(self, grass_only=False):
        if not self.autogrow_flowers:
            return False
        if grass_only == False:
            if self.add_a_flower(grass_only=True):
                return True
        xs = list(range(self.width))
        ys = list(range(self.width))
        random.shuffle(xs)
        random.shuffle(ys)
        caterpillar_xys = set(s.xy for s in self.caterpillar.segments)
        for x in xs:
            for y in ys:
                if (x, y) in caterpillar_xys:
                    continue
                tile = self.tiles.get((x, y))
                if tile is None:
                    if not grass_only:
                        self[x, y] = 'flower'
                        return True
                elif tile.grow_flower():
                    return True

    def draw(self):
        with pushed_matrix():
            pyglet.gl.glTranslatef(TILE_WIDTH/2, TILE_WIDTH/2, 1)
            pyglet.gl.glScalef(1/2, 1/2, 1)
            self.background.blit_tiled(
                0, 0, 0,
                self.width * TILE_WIDTH * 2, self.height * TILE_WIDTH * 2,
            )
            pyglet.gl.glScalef(2, 2, 1)
            pyglet.gl.glTranslatef(TILE_WIDTH/2, TILE_WIDTH/2, 0)
            self.batch.draw()
            self.caterpillar.draw()
            if self.cocoon:
                self.cocoon.draw()
            self.score_batch.draw()

    def tick(self, dt):
        self.t += dt
        self.caterpillar.tick(dt * SPEED)
        if self.cocoon:
            self.cocoon.tick(dt)
        self.eol_tiles = [tile for tile in self.eol_tiles if tile.tick(dt)]
        for tile in self.tiles.values():
            tile.tick(dt)
        if self.score_labels:
            new_score_labels = []
            for label in self.score_labels:
                t = self.t - label._caterpillar_start_t
                label.x = (label._caterpillar_x) * TILE_WIDTH
                label.y = (label._caterpillar_y + t + t**2*2) * TILE_WIDTH
                label.color = (*label._caterpillar_color, int(abs(1 - t)**.5 * 255))
                if t < 1:
                    new_score_labels.append(label)
                else:
                    label.delete()
            self.score_labels = new_score_labels
        if self.displayed_score != self.total_score:
            diff = (self.total_score - self.displayed_score)
            if diff < 1:
                self.displayed_score = self.total_score
            else:
                self.displayed_score += (self.total_score - self.displayed_score) * 0.1
                if diff > 1000:
                    self.displayed_score += 111
                if diff > 100:
                    self.displayed_score += 11
                elif diff > 10:
                    self.displayed_score += 1
                elif diff > 0:
                    self.displayed_score += 0.5
                else:
                    self.displayed_score -= 0.5
            if self.displayed_score:
                self.main_score_label.text = str(int(self.displayed_score))
            else:
                self.main_score_label.text = ''
        if self.gameover_t is not None:
            gt = (self.t - self.gameover_t)
            n = 30
            b = int(min(255-n, (255-n) * gt))
            o = int(math.sin(gt * math.tau / 2) * n)
            self.gameover_label.color = (
                b-o, b-o, b-o, 255
            )

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
            return tiles.edge
        return self.tiles.get(x_y, tiles.empty)

    def __setitem__(self, x_y, item):
        eol_tile = self.tiles.pop(x_y, None)
        if eol_tile:
            self.eol_tiles.append(eol_tile)
            eol_tile.delete()
        x, y = x_y
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return
        if item is not None:
            if isinstance(item, str):
                item = tiles.new(item, self, x, y)
            self.tiles[x_y] = item

    def add_cocoon(self, caterpillar):
        self.cocoon = Cocoon(self, caterpillar)

    def score(self, amount, x, y):
        self.total_score += amount
        if self.total_score <= 0:
            self.total_score = 0
            self.main_score_label.text = ''
        else:
            self.main_score_label.text = str(self.total_score)
        if not (0 < amount < 5):
            label = self.add_label(
                f'{amount:+1}',
            )
            if amount > 0:
                label._caterpillar_color = 250, 255, 200
            else:
                label._caterpillar_color = 255, 230, 200

    def add_label(self, label, x, y):
        label = pyglet.text.Label(
            label,
            **HALF_FONT_INFO.label_args(),
            anchor_x='center',
            anchor_y='baseline',
            align='center',
            batch=self.score_batch,
            x=x * TILE_WIDTH,
            y=y * TILE_WIDTH,
        )
        self.score_labels.append(label)
        label._caterpillar_start_t = self.t
        label._caterpillar_x = x
        label._caterpillar_y = y
        label._caterpillar_color = 255, 255, 255
        return label

    def signal_done(self):
        if self.done:
            return True
        self.shot = pyglet.image.get_buffer_manager().get_color_buffer().get_texture()

    def signal_game_over(self, message):
        self.gameover_label.text = f'{message}    Press esc to exit.'.upper()
        self.gameover_t = self.t
