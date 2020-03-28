import pyglet

from .resources import get_image, FONT_INFO

WIDTH = 1024
HEIGHT = 576

DARK = 61, 43, 6
LIGHT = 169, 151, 118
MED = 142, 111, 49
WHITE = 255, 255, 255
GRAY = 143, 143, 143
SILVER = 200, 200, 200

LEVEL_POSITIONS = [
    (730, 384),
    *[(x, y) for y in (224, 144, 64) for x in (594, 728, 865)]
]

groups = [pyglet.graphics.OrderedGroup(i) for i in range(4)]

def mksprite(*args, **kwargs):
    if 'yy' in kwargs:
        kwargs['y'] = HEIGHT - kwargs.pop('yy')
    color = kwargs.pop('color', None)
    width = kwargs.pop('width', None)
    height = kwargs.pop('height', None)
    sprite = pyglet.sprite.Sprite(*args, **kwargs)
    if color is not None:
        sprite.color = color
    if width is not None:
        sprite.scale_x = width / sprite.image.width
    if height is not None:
        sprite.scale_y = height / sprite.image.height
    return sprite

class LevelSelect:
    def __init__(self, state):
        self.state = state
        self.chosen_level = self.state.last_level
        self.batch = pyglet.graphics.Batch()
        self.butterfly_label = pyglet.text.Label(
            '× 1',
            **FONT_INFO.label_args(),
            anchor_x='left',
            anchor_y='baseline',
            x=150,
            y=HEIGHT-48,
            color=WHITE + (255,),
            batch=self.batch,
            group=groups[2],
        )
        self.egg_label = pyglet.text.Label(
            '× 2',
            **FONT_INFO.label_args(),
            anchor_x='left',
            anchor_y='baseline',
            x=463,
            y=HEIGHT-48,
            color=WHITE + (255,),
            batch=self.batch,
            group=groups[2],
        )
        self.completion_label = pyglet.text.Label(
            '100%',
            **FONT_INFO.label_args(),
            anchor_x='left',
            anchor_y='baseline',
            x=784,
            y=HEIGHT-48,
            color=WHITE + (255,),
            batch=self.batch,
            group=groups[2],
        )
        self.level_bgs = [
            mksprite(
                get_image('solid', 0, 0),
                batch=self.batch,
                group=groups[2],
                color=DARK,
                x=x,
                y=y-1,
                width=128,
                height=72,
            )
            for x, y in LEVEL_POSITIONS
        ]
        self.level_fgs = [
            mksprite(
                get_image('solid', 0, 0),
                batch=self.batch,
                group=groups[2],
                color=MED,
                x=x,
                y=y,
                width=128,
                height=72,
            )
            for x, y in LEVEL_POSITIONS
        ]
        self.level_arrows = [
            mksprite(
                get_image('go-on'),
                batch=self.batch,
                group=groups[3],
                x=x+105,
                y=y+13,
            )
            for x, y in LEVEL_POSITIONS
        ]
        self.level_labels = [
            pyglet.text.Label(
                f'{i}',
                **FONT_INFO.label_args(),
                anchor_x='center',
                anchor_y='baseline',
                x=x+20,
                y=y+40,
                color=DARK + (255,),
                batch=self.batch,
                group=groups[3],
            )
            for i, (x, y) in enumerate(LEVEL_POSITIONS)
        ]
        self.elements = [
            mksprite(
                get_image('solid', 0, 0),
                batch=self.batch,
                group=groups[0],
                color=DARK,
                width=WIDTH,
                height=HEIGHT,
            ),
            mksprite(
                get_image('solid', 0, 0),
                batch=self.batch,
                group=groups[1],
                color=LIGHT,
                width=520,
                height=512,
            ),
            mksprite(
                get_image('solid', 0, 0),
                batch=self.batch,
                group=groups[1],
                color=LIGHT,
                x=561,
                width=464,
                height=512,
            ),
            mksprite(
                get_image('butterfly'),
                batch=self.batch,
                group=groups[2],
                color=WHITE,
                x=113,
                yy=35,
            ),
            mksprite(
                get_image('egg'),
                batch=self.batch,
                group=groups[2],
                color=WHITE,
                x=434,
                yy=35,
            ),
            mksprite(
                get_image('map-icon'),
                batch=self.batch,
                group=groups[2],
                color=WHITE,
                x=748,
                yy=35,
            ),
        ]
        self.update()

    def update(self):
        self.butterfly_label.text = f'× {len(self.state.butterflies)}'
        egg_count = self.state.count_eggs()
        self.egg_label.text = f'× {egg_count}'
        is_emergency = self.state.is_emergency
        if not self.state.accessible_levels[self.chosen_level] or self.state.is_emergency:
            self.chosen_level = 0
        for i, available in enumerate(self.state.accessible_levels):
            if available:
                if i and is_emergency:
                    self.level_fgs[i].color = SILVER
                    self.level_fgs[i].opacity = 255
                    self.level_bgs[i].color = MED
                    self.level_arrows[i].image = get_image('go-off')
                    self.level_arrows[i].opacity = 255
                else:
                    self.level_fgs[i].color = WHITE
                    self.level_fgs[i].opacity = 255
                    self.level_bgs[i].color = DARK
                    if self.chosen_level == i:
                        self.level_arrows[i].image = get_image('go-enter')
                    else:
                        self.level_arrows[i].image = get_image('go-on')
                    self.level_arrows[i].opacity = 255
            else:
                self.level_fgs[i].color = MED
                self.level_fgs[i].opacity = 200
                self.level_bgs[i].color = LIGHT
                self.level_arrows[i].opacity = 0

    def tick(self, dt):
        pass

    def draw(self):
        self.batch.draw()

    def handle_command(self, command):
        if command == '0':
            self.chosen_level = 0
        if command in '123456789':
            level = int(command)
            if self.state.accessible_levels[level] and not self.state.is_emergency:
                self.chosen_level = level
        self.update()
