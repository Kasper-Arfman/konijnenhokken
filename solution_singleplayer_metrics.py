"""Investigate the single-player solution (run solve_singleplayer.py first)"""
from collections import defaultdict
from game.rules import TURN_START, points_stop, canonical, rolls, dice_left
from solve_singleplayer import load, best_allocation, should_play


def score_distribution(Q):
    """Probability of every final score of a turn when following the strategy (0 = bust).

    Push probability forward through the turn: start with 100% at the turn start,
    and every roll splits the probability over the states the strategy moves to.
    States are handled in order of (banked points, dice used), so all probability
    has arrived at a state before it is passed on.
    """
    final = defaultdict(float)  # Final score => probability
    rolling = defaultdict(float, {TURN_START: 1.0})  # States where you roll next => probability
    order = lambda state: (state[0], -dice_left(state))

    while rolling:
        state = min(rolling, key=order)
        p_state = rolling.pop(state)
        for p, roll in rolls(state):
            if not any(roll[face] for face in (1, 2)):
                final[0] += p_state * p  # Bust
                continue
            chosen = best_allocation(Q, state, roll)
            if should_play(Q, chosen):
                rolling[canonical(chosen)] += p_state * p
            else:
                final[points_stop(chosen)] += p_state * p
    return dict(sorted(final.items()))

def fresh_dice_limit(Q):
    """Most points banked at which the strategy still rolls 7 fresh dice"""
    return max(t for (t, *board), value in Q.items() if board == [0, 0, 0] and value > t)


def main():
    Q = load()
    dist = score_distribution(Q)
    average = sum(score * p for score, p in dist.items())
    highest = max(dist)

    print(f"Expected score per turn:  {Q[TURN_START]:.4f}  (solver)")
    print(f"                          {average:.4f}  (score distribution)")
    print(f"Chance to bust:           {dist[0]:.2%}")
    print(f"Highest possible score:   {highest}  (chance {dist[highest]:.1e})")
    print(f"Rolls 7 fresh dice with up to {fresh_dice_limit(Q)} points banked")

    print("\nChance of scoring at least ...")
    for threshold in (1, 10, 20, 30, 50, 75, 100):
        p = sum(p for score, p in dist.items() if score >= threshold)
        print(f"  {threshold:3} points: {p:7.2%}")

    print("\nMost likely scores:")
    for score, p in sorted(dist.items(), key=lambda x: -x[1])[:5]:
        print(f"  {score:3} points: {p:6.2%}")

if __name__ == "__main__":
    main()
