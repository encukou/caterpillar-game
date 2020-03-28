
from .resources import LEVELS
from . import tiles

tileinfo = {
    0: {'str': '.'},
    0xa0000082: {'str': '@', 'dx': +1, 'dy': 0},
    0x60000082: {'str': '@', 'dx': -1, 'dy': 0},
}
convertfuncs = {
    'int': int,
    'string': str,
}
for tileset in LEVELS['tilesets']:
    firstgid = tileset['firstgid']
    tileinfo.update({
        tile['id'] + firstgid: {
            **{
                p['name']: convertfuncs[p['type']](p['value'])
                for p in tile.get('properties', ())},
            'sprite': (8 - tile['id'] // 16) * 16 + (tile['id'] % 16),
        }
        for tile in tileset['tiles']
    })

LEVEL_MAP = {
    1: 3,
    2: 5,
    3: 6,
    4: 7,
    5: 8,
    6: 9,
    9: 1,
}
KEY_LEVEL_MAP = {
    1: 2,
    2: 2,
    3: 2,

    4: 1,
    5: 2,
    6: 3,

    7: 4,
    8: 5,
    9: 6,
}

def load_level_to_grid(level, grid):
    level = LEVEL_MAP.get(level, level)
    start_col = (level - 1) % 3 * 32
    start_row = (3 - (level - 1) // 3) * 18

    pitch = LEVELS['width']
    data = LEVELS['layers'][1]['data']

    for y in range(grid.height):
        try:
            for x in range(grid.width):
                ny = grid.height - y - 1
                tile = data[(grid.height - start_row - ny) * pitch + start_col + x]
                props = tileinfo.get(tile, {})
                tile_str = props.get('str')
                if tile_str:
                    print(' ' + props['str'] + ' ', end='')
                else:
                    print(f'{tile:^3}', end='')
                tile_class = tiles.tile_classes.get(tile_str)
                if tile_class:
                    grid[x, ny] = tile_class(grid, x, ny, props)
                elif tile_str == '?':
                    grid[x, ny] = 'grass'
                    grid[x, ny].grow_flower()
                elif tile_str == '@':
                    grid.add_caterpillar(
                        x, ny, (props['dx'], props['dy'])
                    )
                else:
                    assert tile < 1000, hex(tile)
        finally:
            print()

    grid.autogrow_flowers = False
