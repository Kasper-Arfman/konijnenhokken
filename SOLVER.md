# How the solvers work

| File | What it does |
|------|--------------|
| [game/rules.py](game/rules.py) | The rules the solvers share: rolls, allocations, scores |
| [solve_singleplayer.py](solve_singleplayer.py) | Maximizes the expected score of a turn → `solution_singleplayer.pkl` |
| [solution_singleplayer_metrics.py](solution_singleplayer_metrics.py) | Investigates that solution |
| [solve_1v1.py](solve_1v1.py) | Maximizes the chance of winning a 1v1 game → `solution_1v1.pkl` (readable, slow) |
| [solve_1v1_fast.py](solve_1v1_fast.py) | The same 1v1 solution, fast enough for a 200-point game |
| [solution_1v1_metrics.py](solution_1v1_metrics.py) | Investigates the 1v1 solution |

Both solvers are written the same way: every value is a lookup in a table that is filled by a recursive function the first time you ask for it (memoization). For the rules of the game, see the [README](README.md).

---

# Single player

## 1. The turn state

Everything that matters for the rest of a turn is captured by four numbers, `T = (t, r1, r2, c)`:

| Symbol | Meaning |
|--------|---------|
| `t`  | points banked in earlier runs of this turn (a run ends when all 7 dice are used) |
| `r1` | dice kept as 1-rabbits (1 point each) |
| `r2` | dice kept as 2-rabbits (2 points each) |
| `c`  | cages collected; cages come in order (×2 → ×3 → ×4 → ×5), so the multiplier is `c + 1` |

`r1 + r2 + c` dice are on the board, and you roll the other `7 - (r1 + r2 + c)`. A turn starts at `TURN_START = (0, 0, 0, 0)`.

## 2. The formulas

In each state you choose between stopping and rolling again:

$$\text{stop\_score}(T) = t + (r_1 + 2r_2)(c + 1)$$

$$\text{play}(T) = \sum_{\text{roll}} P(\text{roll}) \cdot \max_{T' \in \text{allocations}(T,\ \text{roll})} E(T') \qquad \text{(0 if you bust)}$$

$$E(T) = \max(\text{stop\_score}(T),\ \text{play}(T))$$

`E` calls `play`, and `play` calls `E` for the states one roll later. In [solve_singleplayer.py](solve_singleplayer.py) these are `E`, `play_value` and `roll_value`. `play_value` memoizes its results in `play_values`, and that dict is the solution.

## 3. Rolls and allocations ([game/rules.py](game/rules.py))

**Rolls.** The order of the dice doesn't matter, so `rolls(T)` lists each distinct roll once (792 for 7 dice instead of 6⁷ = 279,936), as a `Counter` like `{1: 1, 2: 2}`. Its probability counts the orders it can be rolled in:

$$P(\text{roll}) = \frac{k!}{n_1!\, n_2! \cdots n_6!} \cdot \frac{1}{6^k}$$

**Allocations.** `possible_allocations(T, roll)` lists every state you can move to. You choose how many 1s and 2s to keep as rabbits (at least one), and how many cages to take. Cages must come next in line: with `c` cages the next one needs the die `c + 2`, and the ×2 cage needs a 2 that you didn't keep as a rabbit. No allocations means you bust: you lose the whole turn, including `t`.

**Full board.** With all 7 dice used, a run is complete: its score is banked and you can roll 7 fresh dice. So `(100, 0, 4, 3)` is the same state as `(132, 0, 0, 0)`. `canonical(T)` maps the first to the second, so only one is stored. Look up `Q[canonical(T)]` when `T` might be a full board.

## 4. Why the recursion ends

Every roll you survive puts at least one die on the board, so a run lasts at most 7 rolls. A full board starts a new run with more points banked, which could go on forever, so above `DEPTH` banked points you always stop. That doesn't change the answer:

| Banked `t` | Stop | Roll 7 fresh dice |
|---|---|---|
| 98 | 98 | 98.17 |
| 100 | 100 | 100.06 |
| 101 | 101 | 101.00 (just below) |
| 102 | 102 | 101.94 |

A fresh run adds about 6 points on average but busts about 6% of the time, which costs everything banked. That's worth it up to about 6 / 0.06 ≈ 100 points. `DEPTH = 201` leaves plenty of margin.

## 5. Results ([solution_singleplayer_metrics.py](solution_singleplayer_metrics.py))

| | |
|---|---|
| Expected score per turn | **12.7261** |
| Chance to bust | 35.68% |
| Highest possible score | 132 (bank exactly 100, then four 2s and three cages: 8 × 4) |
| Rolls 7 fresh dice with up to | 100 points banked |
| States stored | 14,852 |
| Runtime | about 4 s |

The metrics come from the exact distribution of final scores: start with probability 1 at the turn start, and push it through every roll, following the strategy's choices.

**Why not just take the highest stop score in `Q`?** `Q` contains every state the solver *looked at*, not only the states the strategy *visits*. To decide whether to stop at a state, the solver computes what rolling on is worth, so it explores states after it even when the answer is "stop". The highest stop score in `Q` is 232, which the strategy never reaches.

## 6. Playing with the solution

- **Which allocation?** The state with the highest `max(stop_score(T'), Q[canonical(T')])`
- **Stop or roll?** Roll if `Q[canonical(T)] > stop_score(T)`

These are `best_allocation` and `should_play` in [solve_singleplayer.py](solve_singleplayer.py). [game/user.py](game/user.py) (`QBot`) and [main.py](main.py) (the app) do the same.

This maximizes your average score. It does **not** maximize your chance of winning against an opponent: when you're far behind near the end, a risky turn can win more often.

---

# 1v1

## 7. Rules being solved

- Player 1 and player 2 alternate turns. A **round** is P1's turn followed by P2's turn.
- The game ends after the round in which someone reaches `TARGET = 200` points. Most points wins.
- Both players maximize their win chance `Q = P(win) + TIE · P(tie)`, with `TIE = 0.5`.

With `TIE = 0.5`, my `Q` and my opponent's `Q` add up to 1. So when the turn passes to the opponent, my value is `1 - Q[their state]`, and one number per state is enough.

## 8. States

| | |
|---|---|
| `S = (A, B, 0)` | P1 is about to move. `A`, `B`: points of P1 and P2 |
| `S = (A, B, 1)` | P2 is about to move |
| `S = (n, 0, 2)` | P2's final turn: P1 has reached the target and leads by `n`. Only the gap matters |
| `Q[S]` | win chance of the player about to move |
| `Q[S, T]` | win chance of the player moving, midway through the turn |

Every `Q` is from the point of view of the player who is moving.

## 9. A turn is the single-player problem with a different payoff

Inside a turn, everything works as in the single-player solver. Only what stopping is worth changes: instead of your score, it's the win chance of the game state you end up in:

| Turn | End the turn with turn score `s` (bust: `s = 0`) |
|------|--------------------------------------------------|
| P1 | `1 - Q[(A + s, B, 1)]` |
| P2 | `1` if `B + s ≥ 200` (P2 wins), else `1 - Q[(A, B + s, 0)]` |
| P2's final turn | `1` if `s > n`, `TIE` if `s = n`, `0` if `s < n` |

This is `end_turn(S, s)` in [solve_1v1.py](solve_1v1.py). Then:

$$Q[S, T] = \max(\text{end\_turn}(S, \text{stop\_score}(T)),\ \text{play}[S, T]) \qquad Q[S] = \text{play}[S, \text{TURN\_START}]$$

## 10. The only loop: busting

Every turn that doesn't bust increases `A + B`. Busting doesn't:

```
Q[(A, B, 0)]  --P1 busts-->  Q[(A, B, 1)]  --P2 busts-->  Q[(A, B, 0)]
```

Plain recursion would go around this loop forever. `solve_loop` puts a guess for `Q[(A, B, 1)]` in the table, solves both turns, and repeats until the values stop changing (value iteration). Double busts are rare, so this converges quickly.

## 11. Bounding a turn

- P2 stops as soon as stopping wins, so P2's turns can't go on forever.
- P1 doesn't roll 7 fresh dice when at 200 or more and `LEAD_CAP = 150` points ahead. With a 40-point target, cap 150 and cap 300 gave identical tables, so the cap doesn't change any decision.

## 12. Memory

Only `Q[S]` is kept: about 80,000 game states. `Q[S, T]` is only needed while solving the turn of `S`, because other turns only use `Q[S]`. Keeping it would take about 10⁹ entries (around 100 GB as a Python dict). When playing, `turn_values(S)` recomputes the turn you're in.

## 13. The fast version ([solve_1v1_fast.py](solve_1v1_fast.py))

The readable solver is pure Python: a 20-point game takes minutes, and a 200-point game would take weeks. The fast version computes the same table, in the same file format:

1. **Bottom-up.** Game states are solved from the highest `A + B` down. Every turn that doesn't bust leads to a higher `A + B`, which is then already solved. Inside a turn, `t` goes from high to low and dice used from 7 down to 0.
2. **Many game states at once.** States with the same `A + B` don't depend on each other, so they're solved together as columns of numpy arrays, split over the CPU cores.
3. **Grouped rolls.** Rolls that allow the same allocations are merged: 1,067 groups instead of 5,464 rolls per banked score.
4. **The bust loop solved directly.** With fixed decisions, a turn's value is linear in what busting is worth: `Q = a + p_bust · bust_value`. That gives the loop's solution directly; this repeats until the decisions stop changing (usually 2–4 times).

On a 10-point game, the two solvers agree to 4 × 10⁻¹³ (0.8 s against 89 s).

## 14. Results ([solution_1v1_metrics.py](solution_1v1_metrics.py))

| | |
|---|---|
| P1 (moves first) wins | 46.58% |
| P2 wins | 53.42% |
| Game states stored | 80,232 |
| Runtime (fast solver, 16 cores) | about 20 minutes |

Moving second is an advantage: P2 plays the last turn knowing exactly what to beat.

The strategy is more careful than the single-player one. At the start of the game you stop rolling 7 fresh dice above about 70 banked points (single player: 100), and with a big lead near the end already above 25.

## 15. Playing with the solution

`turn_values(S)` solves the turn of game state `S` and returns `Q[S, T]` for all its states. Then:

- **Which allocation?** `best_allocation(turn, T, roll)`: the state with the highest `turn[canonical(T')]`
- **Stop or roll?** `should_play(S, turn, T)`: roll if `turn[canonical(T)] > end_turn(S, stop_score(T))`
