import os
import sys

from .window import Window
from .grid import Grid
from .butterfly import Demo
from .state import GameState

state = GameState.load()
print(state.to_dict())

try:
    level = int(sys.argv[1])
except (IndexError, ValueError):
    level = 5

window = Window(Grid(state, level=level))
#window = Window(Demo())

if 'ENTR_ON' in os.environ:
    # for rapid prototyping (entr), put window somewhat out of the way
    window.set_location(1, 1)
    print('—' * os.get_terminal_size()[0])

window.run()
