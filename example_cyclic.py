"""
Lets consider the following states

A1 A2 A3

B1 B2 B3


Q[A3] = 10
Q[B3] = 12

And we have the following transfer probabilities:

    A1 -> B1: 10%
    A1 -> A2: 90%

    A2 -> B2: 10%
    A2 -> A3: 90%

    B1 -> A1: 10%
    B1 -> B2: 90%

    B2 -> A2: 10%
    B2 -> B3: 90%

So there are cycles, but calculate Q for every state


Every non-final state satisfies   Q[X] = sum(p * Q[Y] for Y, p in EDGES[X])
The cycles are A1 <-> B1 and A2 <-> B2, so plain recursion would never end.
Three ways to solve it below.
"""
from fractions import Fraction

FINAL = {'A3': 10, 'B3': 12}
EDGES = {
    'A1': {'B1': 0.1, 'A2': 0.9},
    'A2': {'B2': 0.1, 'A3': 0.9},
    'B1': {'A1': 0.1, 'B2': 0.9},
    'B2': {'A2': 0.1, 'B3': 0.9},
}


""" ---- Method 1: value iteration. Guess everything, apply the equations until nothing changes ---- """

def value_iteration(tol=1e-12):
    Q = dict(FINAL) | {X: 0 for X in EDGES}  # Any guess works
    rounds = 0
    while True:
        rounds += 1
        new = {X: sum(p * Q[Y] for Y, p in edges.items()) for X, edges in EDGES.items()}
        change = max(abs(new[X] - Q[X]) for X in EDGES)
        Q.update(new)
        if change < tol:
            return Q, rounds
    # Converges because every round keeps only the 10% that loops back: the error shrinks 10x per round


""" ---- Method 2: one linear system for all states at once ---- """

def linear_system():
    """Q[X] - sum(p * Q[Y]) = (known part), solved by Gaussian elimination (exact, with fractions)"""
    unknowns = list(EDGES)
    idx = {X: i for i, X in enumerate(unknowns)}
    n = len(unknowns)
    # Row i:  Q[X] - sum(p * Q[Y] for unknown Y) = sum(p * FINAL[Y] for final Y)
    M = [[Fraction(int(i == j)) for j in range(n)] + [Fraction(0)] for i in range(n)]
    for X, edges in EDGES.items():
        for Y, p in edges.items():
            p = Fraction(p).limit_denominator()
            if Y in FINAL:  M[idx[X]][n] += p * FINAL[Y]
            else:           M[idx[X]][idx[Y]] -= p
    for col in range(n):
        pivot = next(r for r in range(col, n) if M[r][col] != 0)
        M[col], M[pivot] = M[pivot], M[col]
        M[col] = [v / M[col][col] for v in M[col]]
        for r in range(n):
            if r != col and M[r][col] != 0:
                M[r] = [a - M[r][col] * b for a, b in zip(M[r], M[col])]
    return dict(FINAL) | {X: M[idx[X]][n] for X in unknowns}


""" ---- Method 3: solve the cycles one at a time, like the game solver will ---- """

# The strongly connected components (the cycles), in the order they can be solved:
# {A2, B2} only needs A3, B3, which are known.  {A1, B1} only needs A2, B2.
COMPONENTS = [('A2', 'B2'), ('A1', 'B1')]

def solve_pair(Q, X, Y):
    """X and Y point to each other:
        Q[X] = pX * Q[Y] + aX      (aX: everything X gets from already solved states)
        Q[Y] = pY * Q[X] + aY
    Substitute:  Q[X] = pX * (pY * Q[X] + aY) + aX  =>  Q[X] = (aX + pX * aY) / (1 - pX * pY)"""
    pX, pY = EDGES[X][Y], EDGES[Y][X]
    aX = sum(p * Q[Z] for Z, p in EDGES[X].items() if Z != Y)
    aY = sum(p * Q[Z] for Z, p in EDGES[Y].items() if Z != X)
    Q[X] = (aX + pX * aY) / (1 - pX * pY)
    Q[Y] = aY + pY * Q[X]

def by_components():
    Q = dict(FINAL)
    for X, Y in COMPONENTS:
        solve_pair(Q, X, Y)
    return Q


if __name__ == "__main__":
    Q1, rounds = value_iteration()
    Q2 = linear_system()
    Q3 = by_components()
    print(f"{'state':6} {'iteration':>12} {'linear system':>16} {'components':>12}")
    for X in ['A1', 'A2', 'A3', 'B1', 'B2', 'B3']:
        print(f"{X:6} {Q1[X]:12.6f} {str(Q2[X]):>16} {Q3[X]:12.6f}")
    print(f"value iteration took {rounds} rounds")
