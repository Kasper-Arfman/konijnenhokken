import sys
from collections import Counter
from itertools import combinations_with_replacement
from math import factorial

class Solver:
    """
    Given a directed acyclic graph. The nodes have the following properties:
     - options for the choice to make at this node
        each choice gives a probability distribution of transfers to other states
     - choice evaluating function
        (state, choice) -> value
     - state evaluating function (based on the quality of the options)
        (state) -> value

    Compute the policy that optimizes the node value
    """

    def __init__(self):
        self.policy = {}  # state => option
        self._state_value = {}  # state => float
        self._option_value = {}  # (state, option) => value

    def solve(self, state):
        self.state_value(state)
        return self._state_value[state], self.policy[state]

    """ ---- USER SPECIFICATIONS ---- """

    def options(self, state):
        raise NotImplementedError()

    def eval_option(self, state, option):
        """How is the value of an option calculated"""
        outcomes = option(state)
        return sum(p*self.state_value(s) for p, s in outcomes)
    
    def eval_state(self, state):
        value = lambda option: self.option_value(state, option)
        choice = max(self.options(state), key=value)
        return choice, value(choice)
    
    def base_case_value(self, state):
        raise NotImplementedError()

    """ ---- SOLVER LOGIC ---- """

    def option_value(self, state, option):
        if (state, option) not in self._option_value:
            self._option_value[state, option] = self.eval_option(state, option)
        return self._option_value[state, option]

    def state_value(self, state):
        if state not in self._state_value:

            # Base case
            if (value := self.base_case_value(state)) is not None:
                self._state_value[state] = value

            else:
                choice, value = self.eval_state(state)
                self.policy[state] = choice
                self._state_value[state] = value

        return self._state_value[state]

        

class Konijnenhokken(Solver):
    """Find the strategy that maximizes expected gains"""

    MAX_POINTS = 101  # Sufficiently large to guarantee stopping as best strategy
    NUM_DICE = 7
    DICE_SIDES = 6
    GAME_OVER_STATE = (0, -1, -1, -1)  # Game over state: zero points

    def options(self, state):
        """Main choice: roll again or not?"""
        return (self.stop, self.play)

    def base_case_value(self, state):
        # Player decided to stop
        if -1 in state:
            return state[0]

        # Player ran out of dice
        if sum(state[1:]) == self.NUM_DICE:
            state = (self.stop_value(state), 0, 0, 0)
            return self.state_value(state)

        # Player exceeded the points threshold
        if state[0] >= self.MAX_POINTS:
            return self.stop_value(state)



    """ ---- OPTIONS: stop ---- """

    def stop(self, state):
        stop_state = (self.stop_value(state), -1, -1, -1)
        return ((1.00, stop_state),)

    def stop_value(self, state):
        t, r1, r2, c = state
        return t + (r1 + 2*r2)*(c+1)

    """ ---- OPTIONS: play ---- """

    def play(self, state):
        num_dice = self.NUM_DICE - sum(state[1:])
        rolls = (Counter(x) for x in combinations_with_replacement(range(1, self.DICE_SIDES+1), num_dice))
        return tuple((self.roll_probability(roll), self.best_allocation(state, roll)) for roll in rolls)

    def roll_probability(self, roll: Counter):
        """Probability of a roll"""
        # Number of ways to arrive at this roll outcome
        multiplicity = factorial(sum(roll.values()))
        for v in roll.values():
            multiplicity //= factorial(v)

        # Total number of rolls
        possible_rolls = self.DICE_SIDES**roll.total()

        return multiplicity / possible_rolls
    
    def best_allocation(self, state, roll: Counter):
        return max(self.allocations(state, roll), key=self.state_value, default=self.GAME_OVER_STATE)
    
    def allocations(self, state: tuple, roll: dict):
        """All the possible states that can be obtained from a roll"""
        t, r1, r2, c = state
        states = set()
        for d1 in range(roll[1]+1):
            for d2 in range(roll[2]+1):
                # Must add atleast one rabbit
                if (d1, d2) == (0, 0):  continue

                # 1: Add only rabbits
                states.add((t, r1+d1, r2+d2, c))

                # In case all 2s are used up
                if not (roll[2] - d2):  continue

                # 2: Add cages as well
                for dc, cage in enumerate(range(c+2, 6), 1):
                    if cage not in roll:  break
                    states.add((t, r1+d1, r2+d2, c+dc))

        return states


class ExampleGame(Solver):
    """Calculate the win probability for a simple game with two players.

    Each player has two choices:
     - play safe: get 50% chance at 2 points. 50% chance at 1 point (1.5 avg)
     - play risk: get 20% chance at 3 points. 80% chance at 1 point (1.4 avg)
    """

    MAX_POINTS = 10  # Number of 

    def options(self, state):
        return (self.safe, self.risk)

    def base_case_value(self, state):
        xA, xB = state
        if xA >= self.MAX_POINTS:  return 1
        if xB >= self.MAX_POINTS:  return 0

    def eval_option(self, state, option):
        outcomes = option(state)
        return sum(p*(1-self.state_value(s)) for p, s in outcomes)
    
    def eval_state(self, state):
        """A state is worth the win rate of the best choice"""
        value = lambda option: self.option_value(state, option)
        choice = max(self.options(state), key=value)
        return choice, value(choice)

    """ ---- OPTIONS ---- """
    def safe(self, state):
        return [
            (1/2, self.add(state, 2)), 
            (1/2, self.add(state, 1)),
            ]  # 1.5 per beurt

    def risk(self, state):
        return [
            ( 1/25, self.add(state, 10)), 
            (24/25, self.add(state, 1)),
            ]  # 1.36 per beurt

    def add(self, state, points):
        xA, xB = state
        return (xB, xA+points)
    

class Konijnenhokken1v1(Solver):
    """Find the strategy that maximizes win_rate in a 1v1
    
    WARNING: this is not acyclic: each player can get 0 points forever
    """

    def options(self, state): ...

    def base_case_value(self, state): ...

    def eval_option(self, state, option): ...
    
    def eval_state(self, state): ...


def main():
    game = ExampleGame()
    q = game.solve((0, 0))
    print(q)

    for state in sorted(game.policy):
        print(f"{state} -- win_rate: {game.state_value(state):.2f} - {game.policy[state]}")

if __name__ == "__main__":
    main()