from math import factorial, prod
from collections import Counter
from itertools import combinations_with_replacement
from functools import cache

@cache
def _allocations(board: tuple, roll: tuple):
    """The boards (r1, r2, c) you can move to. Doesn't depend on t, so it's cached per board"""
    r1, r2, c = board
    boards = set()
    for ones in range(roll[1]+1):
        for twos in range(roll[2]+1):
            if ones == twos == 0:  continue  # Must add atleast one rabbit

            boards.add((r1+ones, r2+twos, c))  # Adding only rabbits is one possibility

            # Alternatively, add any number of cages as well
            for dc, cage in enumerate(range(c+2, 6), 1):
                if roll[cage] <= (twos if cage == 2 else 0):  break  # Played my only two for points

                boards.add((r1+ones, r2+twos, c+dc))
    return tuple(boards)  # A tuple: the cached result is shared, so it mustn't be changed

@cache
def _rolls(dice_remaining: int):
    """((probability, counts), ...) where counts[face] is how often face was rolled. Only depends on the number of dice"""
    total = 6 ** dice_remaining
    result = []
    for x in combinations_with_replacement((1, 2, 3, 4, 5, 6), dice_remaining):
        roll = Counter(x)
        orders = factorial(dice_remaining) // prod(factorial(v) for v in roll.values())
        result.append((orders / total, tuple(roll.get(face, 0) for face in range(7))))
    return tuple(result)


class SolverFinalTurn:
    """The last turn of the game, trailing by `gap` points: more points win, exactly `gap` is a draw"""
    NUM_DICE = 7
    DRAW = 0.5

    def __init__(self, gap):
        self.GAP = gap
        self._Q = {}

    def solve(self):
        self.Q((0, 0, 0, 0))  # This call builds the cache (_Q)

        _Q = {T: Q_T for T, Q_T in sorted(self._Q.items()) if Q_T > self.Q_stop(T)}  # Only include play-states
        return _Q

    def Q(self, T):
        return max(self.Q_stop(T), self.Q_play(T))

    def Q_stop(self, T):
        points = self.points_stop(T)
        if points > self.GAP:   return 1
        if points == self.GAP:  return self.DRAW
        return 0

    def points_stop(self, T):
        t, r1, r2, c = T
        return t + (r1 + 2*r2)*(c+1)

    def Q_play(self, T):
        if sum(T[1:]) == self.NUM_DICE:
            T = (self.points_stop(T), 0, 0, 0)

        if T not in self._Q:
            if self.stop_playing(T):  self._Q[T] = 1  # Base case: banked points already beat the gap
            else:                self._Q[T] = sum(p * self.Q_roll(T, counts) for p, counts in self.rolls(T))
        return self._Q[T]

    def stop_playing(self, T):
        """Base conditions for when to stop playing"""
        return T[0] > self.GAP

    def Q_roll(self, T, counts):
        return max((self.Q(T2) for T2 in self.allocations(T, counts)), default=0)  # No allocations: bust

    def allocations(self, T: tuple, counts: tuple):
        t, r1, r2, c = T
        return [(t, *board) for board in _allocations((r1, r2, c), counts)]

    def rolls(self, T):
        return _rolls(self.NUM_DICE - sum(T[1:]))


if __name__ == "__main__":
    import numpy as np

    T0 = (0, 0, 0, 0)
    Q_final = np.array([SolverFinalTurn(gap).solve()[T0] for gap in range(100)])
    print(Q_final)