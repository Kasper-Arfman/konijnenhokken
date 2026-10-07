import time
from game import win_solver

def main():
    """Solve the 1v1 game: minimize the probability of losing"""
    start = time.time()
    R, T, F = win_solver.solve()
    win_solver.save(R, T, F)

    p1_loses, p2_loses = R[0, 0]
    print(f"\nPlayer 1 loses: {p1_loses:.4%}")
    print(f"Player 2 loses: {p2_loses:.4%}")
    print(f"Tie:            {1 - p1_loses - p2_loses:.4%}")
    print(f"Solved in {time.time() - start:.0f}s")

if __name__ == "__main__":
    main()
    print(f"\nFinished Successfully")
