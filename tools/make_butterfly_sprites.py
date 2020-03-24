# (for Inkscape 1.0)

import subprocess
import csv
from pathlib import Path
import sys

from PIL import Image  # $ python -m pip install pillow

sys.path.insert(0, '.')
print(sys.path)
from caterpillar_game.resources import BUTTERFLY_HEIGHT

result = subprocess.run(
    ['inkscape', '--query-all', 'caterpillar_game/resources/butterfly.svg'],
    stdout=subprocess.PIPE,
    encoding='utf-8',
    check=True,
)
wing_images = []
wing_bytes = bytearray()
for line in csv.reader(sorted(result.stdout.splitlines())):
    object_id, x, y, x, h = line
    if object_id in ('abdomen', 'thorax', 'head', 'eye', 'antenna'):
        basename = object_id
        is_wing = False
    elif object_id.startswith('path'):
        basename = f'wing{len(wing_images):02}'
        is_wing = True
    else:
        continue
    print(object_id, '→', basename)
    tmp_filename = f'caterpillar_game/resources/_tmp.png'
    subprocess.run(
        [
            'inkscape',
            '--export-id', object_id,
            '--export-id-only',
            '--export-area-page',
            '--export-type', 'png',
            '--export-file', tmp_filename,
            '--export-overwrite',
            '--export-height', str(BUTTERFLY_HEIGHT),
            '--export-width', str(BUTTERFLY_HEIGHT),
            'caterpillar_game/resources/butterfly.svg'
        ],
        stdout=subprocess.PIPE,
        encoding='utf-8',
        check=True,
    )
    src = Image.open(tmp_filename)
    if is_wing:
        data = src.convert('LA').getdata(1)
        print([c for c in list(data) if c])
        wing_bytes.extend(data)
    else:
        dest = Image.new('LA', (BUTTERFLY_HEIGHT*2, BUTTERFLY_HEIGHT), (0, 0))
        dest.paste(src, (BUTTERFLY_HEIGHT, 0))
        src = src.transpose(Image.FLIP_LEFT_RIGHT)
        dest.paste(src)
        dest.save(f'caterpillar_game/resources/{basename}.png')
    Path(tmp_filename).unlink()

Path(f'caterpillar_game/resources/wings.dat').write_bytes(wing_bytes)


#caterpillar_game/resources/butterfly.svg select:abdomen; org.inkscape.color.brighter; query-height
