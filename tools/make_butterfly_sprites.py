# (for Inkscape 1.0)

import subprocess
import csv
from pathlib import Path

from PIL import Image  # $ python -m pip install pillow

HEIGHT = 256

result = subprocess.run(
    ['inkscape', '--query-all', 'caterpillar_game/resources/butterfly.svg'],
    stdout=subprocess.PIPE,
    encoding='utf-8',
    check=True,
)
wingcount = 0
for line in csv.reader(sorted(result.stdout.splitlines())):
    object_id, x, y, x, h = line
    if object_id in ('abdomen', 'thorax', 'head', 'eye', 'antenna'):
        basename = object_id
    elif object_id.startswith('path'):
        basename = f'wing{wingcount:02}'
        wingcount += 1
    else:
        continue
    print(object_id, '→', basename)
    tmp_filename = f'caterpillar_game/resources/_tmp.png'
    out_filename = f'caterpillar_game/resources/{basename}.png'
    subprocess.run(
        [
            'inkscape',
            '--export-id', object_id,
            '--export-id-only',
            '--export-area-page',
            '--export-type', 'png',
            '--export-file', tmp_filename,
            '--export-overwrite',
            '--export-height', str(HEIGHT),
            '--export-width', str(HEIGHT),
            'caterpillar_game/resources/butterfly.svg'
        ],
        stdout=subprocess.PIPE,
        encoding='utf-8',
        check=True,
    )
    src = Image.open(tmp_filename)
    dest = Image.new('LA', (HEIGHT*2, HEIGHT), (0, 0))
    dest.paste(src, (HEIGHT, 0))
    src = src.transpose(Image.FLIP_LEFT_RIGHT)
    dest.paste(src)
    dest.save(out_filename)
    Path(tmp_filename).unlink()

Path('caterpillar_game/resources/wingcount.txt').write_text(f'{wingcount}')


#caterpillar_game/resources/butterfly.svg select:abdomen; org.inkscape.color.brighter; query-height
