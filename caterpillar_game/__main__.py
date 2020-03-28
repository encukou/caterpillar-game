import os
import sys

from .window import Window
from .grid import Grid
from .butterfly import Demo
from .state import GameState
from .ui import LevelSelect

state = GameState.load()
print(state.to_dict())

try:
    level = int(sys.argv[1])
except (IndexError, ValueError):
    level = 5

#window = Window(Grid(state, level=level))
#window = Window(Demo())
window = Window(state=state)

if 'ENTR_ON' in os.environ:
    # for rapid prototyping (entr), put window somewhat out of the way
    window.set_location(3306, 1300)
    print('—' * os.get_terminal_size()[0])

window.run()
