import math
import statistics
import random
from itertools import zip_longest

from .butterfly import Butterfly
from .util import encode_hue, decode_hue
from .wing import WING_PATCH_COUNT


class Egg:
    def __init__(self, parents=()):
        self.parents = parents

    def to_dict(self):
        return [p.to_dict() for p in self.parents]

    @classmethod
    def from_dict(cls, data):
        self = cls()
        self.parents = [Butterfly.from_dict(d) for d in data]
        return self

    def make_butterfly(self, hues):
        sins = [0]
        coss = [0]
        for hue in hues:
            angle = decode_hue(hue)
            if angle is not None:
                angle *= math.tau
                sins.append(math.sin(angle))
                coss.append(math.cos(angle))
        y = statistics.mean(sins)
        x = statistics.mean(coss)
        if y == x == 0:
            mean_hue = ' '
        else:
            mean_hue = encode_hue(math.atan2(y, x) / math.tau)

        parent_hues = list(p.hues for p in self.parents)
        assert all(len(h) == WING_PATCH_COUNT for h in parent_hues)
        if not parent_hues:
            offspring_hues = mean_hue * WING_PATCH_COUNT
        else:
            offspring_hues = []
            for i, patch_hues in enumerate(zip_longest(*parent_hues)):
                if random.randrange(WING_PATCH_COUNT*2) < 3:
                    chosen = mean_hue
                else:
                    for i in range(3):
                        chosen = random.choice(patch_hues)
                        if chosen is None:
                            chosen = ' '
                        if chosen == ' ':
                            if random.randrange(2):
                                chosen = mean_hue
                                break
                        else:
                            break
                offspring_hues.append(chosen)
            while len(offspring_hues) < WING_PATCH_COUNT:
                offspring_hues.append(mean_hue)
            assert len(offspring_hues) == WING_PATCH_COUNT
            offspring_hues = ''.join(offspring_hues)

        assert len(offspring_hues) == WING_PATCH_COUNT
        return Butterfly(offspring_hues)
