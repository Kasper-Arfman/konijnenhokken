"""Two players, both on 199 points, target 200. Player 1 is to move.

Any points reach the target. The game always ends after player 2's turn:
    - player 1 stops on s >= 200: player 2 gets one final turn to beat s (win 1, tie 0.5, loss 0)
    - player 1 busts: player 2 wins by scoring anything; if player 2 busts too, we're back at the start

That makes the game cyclic: V = player 1's value at the start, and a double bust is worth V again.
Value iteration: guess V, solve both turns with that guess, which gives a new V; repeat until it converges.
"""
from itertools import count

from solve_final import _rolls, _allocations

NUM_DICE = 7
T0 = (0, 0, 0, 0)


def points_stop(T):
    t, r1, r2, c = T
    return t + (r1 + 2*r2)*(c+1)


class SolverTurn:
    """A single turn that maximises the expected payoff.
    stop_value(points): payoff of stopping with `points` this turn
    bust:               payoff of busting
    cap:                force a stop once this many points are banked (keeps the recursion finite)"""
    def __init__(self, stop_value, bust, cap=None):
        self.stop_value = stop_value
        self.bust = bust
        self.cap = cap
        self._Q = {}
        self._P_bust = {}

    def Q(self, T):
        return max(self.Q_stop(T), self.Q_play(T))

    def Q_stop(self, T):
        points = points_stop(T)
        if points == 0:  return 0
        return self.stop_value(points)

    def Q_play(self, T):
        if sum(T[1:]) == NUM_DICE:
            T = (points_stop(T), 0, 0, 0)

        if T not in self._Q:
            if self.stop_playing(T):  self._Q[T] = self.stop_value(points_stop(T))
            else:                self._Q[T] = sum(p * self.Q_roll(T, counts) for p, counts in _rolls(NUM_DICE - sum(T[1:])))
        return self._Q[T]

    def stop_playing(self, T):
        """Base conditions for when to stop playing"""
        t = T[0]
        if self.cap is not None and t >= self.cap:  return True
        return t > 0 and self.stop_value(t) >= 1  # Banked points already guarantee the best payoff

    def Q_roll(self, T, counts):
        t, r1, r2, c = T
        return max((self.Q((t, *board)) for board in _allocations((r1, r2, c), counts)), default=self.bust)

    def P_bust(self, T):
        """Probability of busting from T when playing on, following the optimal policy"""
        if sum(T[1:]) == NUM_DICE:
            T = (points_stop(T), 0, 0, 0)

        if T not in self._P_bust:
            if self.stop_playing(T):  self._P_bust[T] = 0
            else:                self._P_bust[T] = sum(p * self.P_bust_roll(T, counts) for p, counts in _rolls(NUM_DICE - sum(T[1:])))
        return self._P_bust[T]

    def P_bust_roll(self, T, counts):
        t, r1, r2, c = T
        boards = [(t, *board) for board in _allocations((r1, r2, c), counts)]
        if not boards:  return 1
        best = max(boards, key=self.Q)
        if self.Q_stop(best) >= self.Q_play(best):  return 0
        return self.P_bust(best)


class SolverEndgame:
    def __init__(self, score=199, target=200, cap=100, tol=1e-10):
        self.SCORE = score    # Both players' score
        self.TARGET = target
        self.cap = cap        # Player 1 stops once a turn reaches this many points (approximation)
        self.tol = tol
        self._F = {}

    def F(self, s):
        """Opponent's value of their final turn when they have to beat s"""
        if s not in self._F:
            def payoff(points):
                score = self.SCORE + points
                return 1 if score > s else 0.5 if score == s else 0
            self._F[s] = SolverTurn(payoff, bust=0).Q_play(T0)
        return self._F[s]

    def W(self, points):
        """Player 1's value of stopping with `points` this turn"""
        s = self.SCORE + points
        if s < self.TARGET:  raise NotImplementedError("Stopping below the target leaves this game state")
        return 1 - self.F(s)

    def solve(self):
        """V: player 1's value at the start of a round.
        Player 2 moves last in the round: reaching the target ends the game with a win.
        If both bust, the round starts over and player 1 is worth V again."""
        V = 0.5
        for i in count(1):
            turn2 = SolverTurn(lambda points: 1 if self.SCORE + points >= self.TARGET else 0, bust=1 - V)
            U = turn2.Q_play(T0)  # Player 2's value after player 1 busts

            turn = SolverTurn(self.W, bust=1 - U, cap=self.cap)
            V_new = turn.Q_play(T0)
            print(f"iteration {i}: V = {V_new:.12f}")
            if abs(V_new - V) < self.tol:
                return V_new, turn
            V = V_new


    def solve(self):
        """Compute the quality of state A using value iteration.
        A: player 1 to move at the start of a round
        B: player 2 to move after player 1 busted
        Every Q is from the point of view of the player to move."""
        self.Q = {'A': 0.5, 'B': 0.5}  # Guessed values
        self._turns = {}

        for i in count(1):
            Q_A = self.Q['A']
            self.Q['B'] = self.P_bust('B')*(1 - self.Q['A']) + self.P_survive('B')*self.Q_survive('B')
            self.Q['A'] = self.P_bust('A')*(1 - self.Q['B']) + self.P_survive('A')*self.Q_survive('A')
            print(f"iteration {i}: Q_A = {self.Q['A']:.12f}, P_bust(A) = {self.P_bust('A'):.6f}, P_bust(B) = {self.P_bust('B'):.6f}")
            if abs(self.Q['A'] - Q_A) < self.tol:
                return self.Q['A'], self.turn('A')

    def turn(self, state):
        """Optimal turn for `state`, given the current guess for the state a bust leads to"""
        bust = 1 - self.Q['B' if state == 'A' else 'A']
        key = (state, bust)
        if key not in self._turns:
            if state == 'A':  self._turns[key] = SolverTurn(self.W, bust=bust, cap=self.cap)
            else:             self._turns[key] = SolverTurn(lambda points: 1 if self.SCORE + points >= self.TARGET else 0, bust=bust)
        return self._turns[key]

    def P_bust(self, state):
        return self.turn(state).P_bust(T0)

    def P_survive(self, state):
        return 1 - self.P_bust(state)

    def Q_survive(self, state):
        """Expected payoff given that the turn does not bust"""
        turn = self.turn(state)
        if self.P_survive(state) == 0:  return 0
        return (turn.Q_play(T0) - self.P_bust(state)*turn.bust) / self.P_survive(state)




    def solve(self, S, T0):  # S: scoreboard and turnplayer, T: turn state

        if (S, T0) not in self._Q:
            self._Q[S, T0] = 0.5 # Begin by using a guess for the value we want to compute.

            policy = Policy(self._Q)  # Compute the optimal policy

            P_bust, Q_bust = bust(S, T0, policy) = ...
            P_live, Q_live = sum()


            Q[S2, T0]




if __name__ == "__main__":
    V, turn = SolverEndgame().solve()
    print(f"Player 1 (to move) scores {V:.6f}, player 2 scores {1 - V:.6f}")
