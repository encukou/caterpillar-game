import array

import pyglet

from .resources import get_image, TILE_WIDTH

SPEED = 2

class Grid:
    def __init__(self):
        self.width = 16
        self.height = 9
        self.map = array.array('b', [0] * self.width * self.height)
        self.caterpillar = Caterpillar(self)
        self.sprites = {}
        self.batch = pyglet.graphics.Batch()
        self[0, 2] = 16

    def draw(self):
        self.batch.draw()
        self.caterpillar.draw()

    def tick(self, dt):
        self.caterpillar.move(dt * SPEED)

    def handle_command(self, command):
        if command == 'up':
            self.caterpillar.direction = 0, +1
        elif command == 'down':
            self.caterpillar.direction = 0, -1
        elif command == 'left':
            self.caterpillar.direction = -1, 0
        elif command == 'right':
            self.caterpillar.direction = +1, 0

    def __getitem__(self, x_y):
        x, y = x_y
        return self.map[y * self.width + x]

    def __setitem__(self, x_y, item):
        x, y = x_y
        self.map[y * self.width + x] = item
        sprite = self.sprites.get(x_y)
        if sprite and not item:
            self.sprites.pop(x_y).delete()
        elif item and not sprite:
            sprite = self.sprites[x, y] = pyglet.sprite.Sprite(
                get_image(item),
                x=x * TILE_WIDTH, y=y * TILE_WIDTH,
                batch=self.batch,
            )
        elif item:
            sprite.image = get_image(item)


def lerp(a, b, t):
    return a * (1-t) + b * t


class Caterpillar:
    def __init__(self, grid, direction=(+1, 0)):
        self.grid = grid
        self.direction = direction
        self.coords = [(
            grid.width // 2, grid.height // 2,
            grid.width // 2 - direction[0], grid.height // 2 - direction[1],
        )]
        self.image = get_image('body')
        self.t = 0
        self.sprites = []
        self.batch = pyglet.graphics.Batch()

    def draw(self):
        while len(self.sprites) < len(self.coords):
            self.sprites.append(pyglet.sprite.Sprite(self.image, batch=self.batch))
        while len(self.sprites) > len(self.coords):
            self.sprites.pop().delete()
        t = self.t
        for i, (x, y, px, py) in enumerate(self.coords):
            sprite = self.sprites[i]
            sprite.x = lerp(px, x, t) * TILE_WIDTH
            sprite.y = lerp(py, y, t) * TILE_WIDTH
        self.batch.draw()

    def move(self, dt):
        self.t += dt
        while self.t > 1:
            self.t -= 1
            self.step()

    def step(self):
        head = self.coords[-1]
        hx, hy, _, _ = head
        dx, dy = self.direction
        nx = hx + dx
        ny = hy + dy
        self.coords.append(
            (nx, ny, hx, hy)
        )
        if self.grid[nx, ny] == 16:
            self.grid[nx, ny] = 0
        else:
            del self.coords[0]
