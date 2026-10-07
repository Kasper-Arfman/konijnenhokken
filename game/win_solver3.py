"""Bottom-up version of win_solver2.py: no recursion, fill the tables in dependency order.

The formulas are the same as in win_solver2.py. Only the ORDER is different:
instead of asking for a value and letting the recursion find what it needs,
every entry is computed after everything it depends on is already in a table.

== Order

    1. Q_final[n]: P2's final turn, trailing by n
         Depends on nothing else.

    2. Q[S] for S = (A, B, i), in order of DECREASING A + B
         P1's turn:  ending with s > 0 leads to (A + s, B, 1)  ->  larger A + B, or Q_final
         P2's turn:  ending with s > 0 leads to (A, B + s, 0)  ->  larger A + B, or game over
         Busting keeps A + B the same: that's the loop, solved per (A, B)
         by value iteration (as in win_solver2.solve_loop).

    3. Inside one turn, Q[S, T] for T = (t, r1, r2, c):
         t from HIGH to LOW         a full board leads to a fresh run with a larger t
         dice used from 7 down to 0 every roll adds dice to the board
         The turn start (0, 0, 0, 0) comes last.

== Bounding t

    Bottom-up needs a highest t to start from. Above t_max you're not allowed to
    roll 7 fresh dice, so a full board at t > t_max means you stop:
        P1:          t_max = highest t with A + t < TARGET or a lead below LEAD_CAP
        P2:          t_max = TARGET - B - 1   (with more, stopping wins the game)
        P2 final:    t_max = n                (with more, stopping wins the game)
"""
from game.solver import possible_allocations, rolls, P, stop_value as stop_score, NUM_DICE

TARGET = 200    # The game ends after the round in which someone reaches this
TIE = 0.5       # Value of a tie
LEAD_CAP = 150  # P1 stops rolling fresh dice when at TARGET or more and this far ahead
TOL = 1e-12     # Convergence of the bust loop
MAX_RUN = 32    # Highest score of one run: 4 twos and 3 cages = 8 x 4

Q_final = {}  # n => win chance of P2 on the final turn, trailing by n
Q_start = {}  # (A, B, i) => win chance of the player about to move (A, B < TARGET)


""" ---- Precomputed tables for a single turn ---- """

# Every board (r1, r2, c), ordered by dice used: 7, 6, ..., 0
BOARDS = sorted(
    [(r1, r2, c) for r1 in range(8) for r2 in range(8) for c in range(5) if r1 + r2 + c <= NUM_DICE],
    key=sum, reverse=True,
)

# allocations[T|roll] for every board and roll: [(P(roll), [next boards]), ...]
# This doesn't depend on t or on the game state, so compute it once.
ALLOCATIONS = {
    board: [
        (P(roll), [T2[1:] for T2 in possible_allocations((0,) + board, roll)])
        for roll in rolls((0,) + board)
    ]
    for board in BOARDS if sum(board) < NUM_DICE
}


""" ---- One turn, bottom-up ---- """

def solve_turn(end_turn, t_max):
    """Fill Q[S, T] for one game state S.

    end_turn(s): value of ending the turn with turn score s (s = 0: bust)
    t_max:       with more points banked, rolling 7 fresh dice is not allowed

    Returns Q[S] (the turn start) and the table Q[S, T]
    """
    Q_turn = {}

    def value(t, board):
        """Q[S, T], read from the table"""
        if sum(board) == NUM_DICE:
            t, board = stop_score((t,) + board), (0, 0, 0)  # Same as banking the run: 7 fresh dice
        if t > t_max:
            return end_turn(t)  # Not allowed to roll fresh dice: you have to stop
        return Q_turn[t, board]

    def play_value(t, board):
        total = 0
        for p, next_boards in ALLOCATIONS[board]:
            if next_boards:
                total += p * max(value(t, b) for b in next_boards)
            else:
                total += p * end_turn(0)  # Bust
        return total

    for t in range(t_max, -1, -1):
        for board in BOARDS:
            if sum(board) == NUM_DICE:
                continue  # Not stored: value() maps it to (t + run score, 0, 0, 0)
            if t == 0 and board == (0, 0, 0):
                return play_value(0, board), Q_turn  # Turn start: you must roll
            stop = end_turn(stop_score((t,) + board))
            Q_turn[t, board] = max(stop, play_value(t, board))


""" ---- Ending a turn, per kind of turn ---- """

def end_value_p1(A, B):
    """P1's value when the game is over"""
    return 1 if A > B else TIE if A == B else 0

def p1_turn(A, B):
    """end_turn and t_max for P1 at (A, B)"""
    def end_turn(s):
        if A + s >= TARGET:
            return 1 - Q_final[A + s - B]   # P2 gets a final turn
        return 1 - Q_start[A + s, B, 1]     # P2's regular turn
    t_max = max(TARGET - 1 - A, B - A + LEAD_CAP - 1)
    return end_turn, t_max

def p2_turn(A, B):
    """end_turn and t_max for P2 at (A, B), A < TARGET"""
    def end_turn(s):
        if B + s >= TARGET:
            return 1 - end_value_p1(A, B + s)   # Round complete, 200 reached: game over
        return 1 - Q_start[A, B + s, 0]         # Next round
    return end_turn, TARGET - B - 1

def p2_final_turn(n):
    """end_turn and t_max for P2's final turn, trailing by n"""
    def end_turn(s):
        return 1 if s > n else TIE if s == n else 0
    return end_turn, n


""" ---- The whole game, bottom-up ---- """

def solve():
    # 1. P2's final turn, for every gap P1 can leave behind
    n_max = max(TARGET, LEAD_CAP) + MAX_RUN
    for n in range(1, n_max + 1):
        Q_final[n], _ = solve_turn(*p2_final_turn(n))

    # 2. All other game states, from high to low A + B
    for total in range(2*(TARGET - 1), -1, -1):
        for A in range(max(0, total - (TARGET - 1)), min(total, TARGET - 1) + 1):
            B = total - A
            solve_loop(A, B)

    return Q_start[0, 0, 0]

def solve_loop(A, B):
    """Q[(A, B, 0)] and Q[(A, B, 1)] depend on each other through busts.
    Value iteration: guess one, compute the other, and repeat until stable"""
    y = 0.5  # Guess for Q[(A, B, 1)]
    while True:
        Q_start[A, B, 1] = y                          # Used when P1 busts
        Q_start[A, B, 0], _ = solve_turn(*p1_turn(A, B))
        y_new, _ = solve_turn(*p2_turn(A, B))         # Uses Q[(A, B, 0)] when P2 busts
        if abs(y_new - y) < TOL:  break
        y = y_new
    Q_start[A, B, 1] = y_new


if __name__ == "__main__":
    print(f"P1 win chance: {solve():.4%}")
