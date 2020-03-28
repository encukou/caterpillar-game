# Caterpillar Effect

A game made for the [PyWeek 29](https://pyweek.org/29/) jam!

Guide fearless caterpillars through meadows of peril and adventure!
Make a closed loop to form a cocoon, scoring tiles (or objects) inside
the cocoon.

Each level (except a free-play meadow) has three achievements to pick up:
an apple, a star, and both at the same time.

Some items have one-time effects when eaten: you can stop time,
bridge over water, or smash rocks.


## Prerequisites


The game was developed with Python 3.7, but should work with Python 3.6+.

Additional libraries are listed in `requirements.txt`.
The game uses `numpy`, `pyglet`, and some smaller pure-Python libraries.


## Installing

If you know how, create and activate a virtualenv.

Unzip the archive (or clone the repo) into a directory,
and navigate into it in your shell.

Then, update your `pip` (just in case), and install the requirements:

    $ python -m pip install -U pip
    $ python -m pip install -r requirements.txt


## Starting

To run the game:

    $ python run_game.py

Note that the game will create the file `savegame.json` in the current directory.


## The Controls

### Gameplay

* Arrows move you around.
* `Esc` quits the level. (Careful, you'll lose your caterpillar!)


### Level Select

* Numbers `0`-`6` select the desired level
* `Enter` starts the action!
* `Esc` quits the game.
* Mouse clicks work too.


### Common

* `f` toggles full-screen.
* `s` saves a screenshot to the current directory.


## License

The code is licensed under the MIT license; see LICENSE.MIT.
All graphics are licensed under CC-BY-SA 4.0; see LICENSE.CC-BY-SA.

Butterfly image traced from photo by *Dave Shafer*:
https://www.flickr.com/photos/opera-nut/3948026503  
Licenced under CCY-BY 2.0; see https://creativecommons.org/licenses/by/2.0/

The font Aldrich is © MADType:
https://fonts.google.com/specimen/Aldrich  
Licenced under OFL; see LICENSE.OFL
