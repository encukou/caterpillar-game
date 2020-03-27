import json
from pathlib import Path

from .butterfly import Butterfly
from .egg import Egg


SAVE_PATH = Path('./savegame.json')

class GameState:
    def __init__(self):
        self.broods = []
        self.in_tutorial = True
        self.butterflies = []
        self.accessible_levels = [True] + [False] * 9

    def save(self, path=SAVE_PATH):
        with SAVE_PATH.open('w') as f:
            json.dump(f, self.to_dict())

    @classmethod
    def load(cls, path=SAVE_PATH):
        try:
            f = SAVE_PATH.open()
        except FileNotFoundError:
            self = cls()
            self.adjust()
        else:
            with f:
                self = cls.from_dict(json.load(f))
        return self

    @classmethod
    def from_dict(cls, data):
        self = cls()
        self.broods = [[Egg.from_dict(d) for d in b] for b in data['broods']]
        self.in_tutorial = data['in_tutorial']
        self.butterflies = [Butterfly.from_dict(b) for b in data['butterflies']]
        self.accessible_levels = data['accessible_levels']
        self.adjust()

    def adjust(self):
        if (self.count_eggs(max=2) + len(self.butterflies)) < 2:
            self.broods.append([Egg()])
            self.butterflies.append(Butterfly())
            self.in_tutorial = True

    def to_dict(self):
        return {
            'broods': [[e.to_dict() for e in b] for b in self.broods],
            'in_tutorial': self.in_tutorial,
            'butterflies': [b.to_dict() for b in self.butterflies],
            'accessible_levels': self.accessible_levels,
        }

    def count_eggs(self, max=None):
        count = 0
        for brood in self.broods:
            count += len(brood)
            if count >= max:
                return count
        return count
