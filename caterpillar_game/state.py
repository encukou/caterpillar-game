import json
from pathlib import Path

from .butterfly import Butterfly
from .egg import Egg
from .level import KEY_LEVEL_MAP

SAVE_PATH = Path('./savegame.json')

class GameState:
    def __init__(self):
        self.broods = []
        self.in_tutorial = True
        self.butterflies = []
        self.accessible_levels = [False] * 10
        self.last_level = 0
        self.level_achievements = {}
        self.best_scores = {}

    def save(self, path=SAVE_PATH):
        print('SAVING')
        as_dict = self.to_dict()
        print(as_dict)
        as_text = json.dumps(as_dict)
        SAVE_PATH.write_text(as_text)

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
        self.last_level = data['last_level']
        self.level_achievements = {int(l): a for l, a in data['level_achievements'].items()}
        self.best_scores = {int(l): a for l, a in data['best_scores'].items()}
        self.adjust()
        return self

    @property
    def is_emergency(self):
        return (self.count_eggs(max=2) + len(self.butterflies)) < 1#3

    def adjust(self):
        self.accessible_levels[0] = True
        if (self.count_eggs(max=2) + len(self.butterflies)) < 2:
            self.broods.append([Egg()])
            self.butterflies.append(Butterfly())
            self.in_tutorial = True
        if self.best_scores.get(0):
            self.accessible_levels[2] = True
        for loot in self.level_achievements.values():
            for item in loot:
                name, sep, number = item.partition(':')
                print('*'*88, name, number)
                if name == 'key' and sep:
                    number = int(number)
                    number = KEY_LEVEL_MAP.get(number, number)
                    self.accessible_levels[number] = True
        self.save()

    def have_key_for(self, level):
        level = KEY_LEVEL_MAP.get(level, level)
        try:
            return self.accessible_levels[level]
        except KeyError:
            return False

    def to_dict(self):
        return {
            'broods': [[e.to_dict() for e in b] for b in self.broods],
            'in_tutorial': self.in_tutorial,
            'butterflies': [b.to_dict() for b in self.butterflies],
            'last_level': self.last_level,
            'level_achievements': self.level_achievements,
            'best_scores': self.best_scores,
        }

    def count_eggs(self, max=None):
        count = 0
        for brood in self.broods:
            count += len(brood)
            if max is not None and count >= max:
                return count
        return count

    def choose_egg(self):
        self.adjust()
        for brood in reversed(self.broods):
            for egg in brood:
                return egg

    def level_completed(self, level, score, items, butterfly):
        self.best_scores[level] = max(self.best_scores.get(level, 0), score)
        self.level_achievements[level] = sorted(set([
            *self.level_achievements.get(level, ()), *items
        ]))
        if butterfly:
            self.butterflies.append(butterfly)
        self.adjust()
