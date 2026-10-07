import pickle
from game.solver import solve, possible_allocations, rolls, stop_value, canonical

def main():
    """Solve the game"""
    avg_score, Q = solve()
    print(f"{avg_score = }")

    # Export the solution (play values)
    with open('solution.pkl', 'wb') as f:
        pickle.dump(Q, f)

    score, state = highest_score(Q)
    print(f"highest_score = {score}  (stopping at {state})")

    


def highest_score(Q):
    """Highest score a turn can end with when following the strategy, with the luckiest dice.

    Walk through every state the strategy can reach: for each roll, take the
    allocation the strategy picks, and keep going while the strategy plays on.
    """
    value = lambda state: max(stop_value(state), Q[canonical(state)])
    best = (0, None)
    todo, seen = [(0, 0, 0, 0)], set()
    while todo:
        state = todo.pop()
        for roll in rolls(state):
            options = possible_allocations(state, roll)
            if not options:  continue  # Bust

            chosen = canonical(max(options, key=value))
            if chosen in seen:  continue
            seen.add(chosen)

            if Q[chosen] > stop_value(chosen):  # The strategy plays on
                todo.append(chosen)
            else:
                best = max(best, (stop_value(chosen), chosen))
    return best

def sorted_dict(d: dict, value=False):
    """Sort a dict by key (default) or by value"""
    return dict(sorted(d.items(), key=lambda x:x[value]))
    
if __name__ == "__main__":
    main()
    print(f"\nFinished Successfully")