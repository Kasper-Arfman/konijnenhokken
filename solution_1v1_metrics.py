"""Investigate the 1v1 solution (run solve_1v1.py or solve_1v1_fast.py first)"""
import sys
import solve_1v1
from solve_1v1 import load, turn_values, should_play, P1, P2, P2_FINAL


def fresh_dice_limit(S):
    """Most points banked at which the player still rolls 7 fresh dice in game state S
    (the single-player strategy stops at 100)"""
    turn = turn_values(S)
    limits = [t for t in range(1, 1000) if (t, 0, 0, 0) in turn and should_play(S, turn, (t, 0, 0, 0))]
    return max(limits, default=0)


def main():
    sys.setrecursionlimit(10_000)  # Solving a turn recurses through all its rolls
    Q = load()
    target = solve_1v1.TARGET
    p1 = Q[0, 0, P1]
    print(f"Target {target}, a tie counts as {solve_1v1.TIE} win")
    print(f"Win chance at the start:  P1 (moves first) {p1:.2%},  P2 {1 - p1:.2%}")

    print("\nP1's win chance at the start of a round (rows: P1's points, columns: P2's points)")
    scores = list(range(0, target, max(1, target // 8)))
    print("       " + "".join(f"{B:7}" for B in scores))
    for A in scores:
        print(f"{A:7}" + "".join(f"{Q[A, B, P1]:7.0%}" for B in scores))

    print("\nP2's win chance in the final turn, trailing by n points")
    for n in (1, 5, 10, 15, 20, 30, 50, 75, 100):
        if (n, 0, P2_FINAL) in Q:
            print(f"  n = {n:3}: {Q[n, 0, P2_FINAL]:7.2%}")

    print("\nMost points banked at which you still roll 7 fresh dice (single player: 100)")
    situations = {
        "P1, start of the game": (0, 0, P1),
        "P2, start of the game": (0, 0, P2),
        "P1, far behind near the end": (target * 3 // 4, target - 10, P1),
        "P1, far ahead near the end": (target - 10, target * 3 // 4, P1),
    }
    for name, S in situations.items():
        print(f"  {name:28} {str(S):16} {fresh_dice_limit(S)}")

if __name__ == "__main__":
    main()
