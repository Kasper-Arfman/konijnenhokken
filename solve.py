import pickle
from game.solver import solve

def main():
    """Solve the game"""
    max_score, Q = solve()
    print(f"{max_score = }")
    
    # Export the solution (play values)
    with open('solution.pkl', 'wb') as f:
        pickle.dump(Q, f)

def sorted_dict(d: dict, value=False):
    """Sort a dict by key (default) or by value"""
    return dict(sorted(d.items(), key=lambda x:x[value]))
    
if __name__ == "__main__":
    main()
    print(f"\nFinished Successfully")