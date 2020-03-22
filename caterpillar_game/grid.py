import array

from .resources import get_image, TILE_WIDTH

SPEED = 2

class Grid:
    def __init__(self):
        self.width = 16
        self.height = 9
        self.map = array.array('b', [0] * self.width * self.height)
        self.map[2] = 16
        self.caterpillar = Caterpillar(self)

    def draw(self):
        self.caterpillar.draw()
        for i, n in enumerate(self.map):
            if n:
                x = i % self.width
                y = i // self.width
                get_image(n).blit(x * TILE_WIDTH, y * TILE_WIDTH)

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

    def draw(self):
        t = self.t
        for x, y, px, py in self.coords:
            self.image.blit(lerp(px, x, t) * TILE_WIDTH, lerp(py, y, t) * TILE_WIDTH)

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
