import sys
from pathlib import Path

# The major, minor version numbers your require
MIN_VER = (3, 6)

if sys.version_info[:2] < MIN_VER:
    sys.exit(
        "This game requires Python {}.{}.".format(*MIN_VER)
    )

if sys.version_info[:2] == MIN_VER:
    print("Python 3.7 is recommended")

sys.path.insert(0, Path(__file__).parent)

import caterpillar_game.__main__
