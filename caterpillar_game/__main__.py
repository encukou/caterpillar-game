import os

from .window import Window
from .grid import Grid
from .butterfly import Demo

window = Window(Grid())

if 'ENTR_ON' in os.environ:
    # for rapid prototyping (entr), put window somewhat out of the way
    window.set_location(1, 1)

window.run()
