import pickle
from solve_maxpoints import DEPTH, points_stop

FILENAME = 'solve_maxpoints.pkl'

if __name__ == "__main__":
    with open(FILENAME, 'rb') as f:
        _Q = pickle.load(f)

    # Show the solution
    for i, T in enumerate(sorted(_Q)):
        if i == 50:  break
        print(T, f"{_Q[T]:5.2f}", "(expected Q)" if i==0 else '')
    print(' ...', len(_Q), 'entries')

    highest_to_play = max(stop for T, Q_T in _Q.items() if (stop := points_stop(T)) < Q_T)
    print(f"\n{highest_to_play = :.0f} (valid depth guess? {highest_to_play + 32 < DEPTH})")
