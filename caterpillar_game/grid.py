import array

from .resources import get_image, TILE_WIDTH

class Grid:
    def __init__(self):
        self.width = 16
        self.height = 9
        self.map = array.array('b', [0] * self.width * self.height)
        self.caterpillar = Caterpillar(self)

    def draw(self):
        self.caterpillar.draw()


class Caterpillar:
    def __init__(self, grid):
        self.grid = grid
        self.coords = [(grid.width // 2, grid.height // 2)]
        self.image = get_image('body')

    def draw(self):
        for x, y in self.coords:
            self.image.blit(x * TILE_WIDTH, y * TILE_WIDTH)
