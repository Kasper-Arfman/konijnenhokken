# How the solver works

[game/solver.py](game/solver.py) computes the strategy that maximizes the **expected number of points per turn**. This document explains what it computes, how it does so, and why the result is exact. For the rules of the game, see the [README](README.md).

## 1. The state

Everything that matters for the rest of a turn is captured by four numbers:

```python
state = (t, r1, r2, c)
```

| Symbol | Meaning |
|--------|---------|
| `t`  | points banked in earlier runs of this turn (after all 7 dice were used) |
| `r1` | dice allocated as 1-rabbits (worth 1 each) |
| `r2` | dice allocated as 2-rabbits (worth 2 each) |
| `c`  | number of cages collected; the multiplier is `c + 1` |

Cages are collected in order (×2 → ×3 → ×4 → ×5), so the count `c` tells you exactly which cages you have. Only the highest one counts, which is why the multiplier is `c + 1`.

The number of dice in use is `r1 + r2 + c`, so the number of dice left to roll is `7 - (r1 + r2 + c)`.

A turn starts in state `(0, 0, 0, 0)`.

## 2. Two values per state

When you're in a state, you choose between stopping and rolling again.

**Stop value**: the points you bank by stopping now.

$$\text{stop}(t, r_1, r_2, c) = t + (r_1 + 2r_2)(c + 1)$$

**Play value**: the expected points if you roll again and keep playing optimally afterwards.

$$\text{play}(s) = \sum_{\text{roll}} P(\text{roll}) \cdot \max_{s' \in \text{allocations}(s,\ \text{roll})} E(s')$$

**State value**: the better of the two.

$$E(s) = \max(\text{stop}(s),\ \text{play}(s))$$

These three formulas are the whole solver. `E` calls `play`, `play` calls `E` on the states one roll later, and so on until the recursion reaches a base case.

In code:

| Function | Computes |
|----------|----------|
| `stop_value(state)` | stop value |
| `play_value(state)` | play value (memoized in `cache`) |
| `E(state)` | state value |
| `E_roll(state, roll)` | value of the best allocation for one specific roll |

## 3. Enumerating rolls

Rolling `k` dice has `6^k` ordered outcomes, but the order doesn't matter: (1, 2, 2) and (2, 1, 2) leave you with the same options. `rolls()` therefore enumerates **multisets** with `combinations_with_replacement` and turns each one into a `Counter` (e.g. `{1: 1, 2: 2}`):

| Dice left | Ordered outcomes | Distinct rolls |
|-----------|------------------|----------------|
| 7 | 279,936 | 792 |
| 6 | 46,656 | 462 |
| 5 | 7,776 | 252 |
| 4 | 1,296 | 126 |
| 3 | 216 | 56 |
| 2 | 36 | 21 |
| 1 | 6 | 6 |

Each multiset is weighted by how many orderings produce it (the multinomial coefficient, `rearrangements()`) times the probability of each ordering:

$$P(\text{roll}) = \frac{k!}{n_1!\, n_2! \cdots n_6!} \prod_{i} p_i^{\,n_i}$$

where $n_i$ is the number of dice that show face $i$ and $p_i = 1/6$. Because the probabilities come from `DICE_PROBABILITIES`, you could also model loaded dice.

## 4. Allocating a roll

`possible_allocations(state, roll)` lists every state you can move to after a roll. You choose:

1. **How many 1s to keep as rabbits** (`0 … roll[1]`)
2. **How many 2s to keep as rabbits** (`0 … roll[2]`)
3. **How many new cages to take**, which must be next in line. If you have `c` cages, the next one needs the die showing `c + 2`, the one after that `c + 3`, and so on up to 5. The chain stops at the first die you didn't roll. The ×2 cage also uses a 2, so it's only possible if at least one 2 wasn't kept as a rabbit.

You must keep **at least one rabbit** per roll, so `(ones, twos) == (0, 0)` is skipped.

Example: state `(0, 1, 0, 1)` (one 1-rabbit, ×2 cage) and roll `{1, 3}` gives:
- `(0, 2, 0, 1)`: keep the 1 as a rabbit
- `(0, 2, 0, 2)`: keep the 1 as a rabbit and take the 3 as the ×3 cage

You never take a 6, and you never keep a cage die without also keeping at least one rabbit.

If no allocation is possible (no 1s or 2s in the roll), you **bust**. `E_roll` returns `0` through `max(..., default=0)`: you lose the whole turn, including the points `t` from earlier runs.

## 5. Base cases

The recursion stops in three situations:

1. **Bust**: covered above; it's worth 0.
2. **All 7 dice used** (`r1 + r2 + c == 7`): the current run is complete. Its score is added to `t` and a new run starts with all dice: `next_turn` maps the state to `(stop(s), 0, 0, 0)`. The play value of the full state is the play value of that fresh state. You can still choose to stop instead, because `E` takes the max.
3. **`t >= DEPTH`** (101): `play_value` returns `-1`, so `E` always picks stopping.

Base case 3 is a cutoff, not a rule of the game. Without it, the recursion would go on forever: every completed run starts another one with a higher `t`. The cutoff is safe because rolling seven fresh dice risks losing all of `t` (bust chance with 7 dice is $(4/6)^7 \approx 5.9\%$), while the expected gain from that roll stays roughly constant. Above some `t`, the risk outweighs the gain. Solving with `DEPTH = 200` and `DEPTH = 300` gives exactly the same result, and in both cases rolling a fresh set is only worth it up to `t = 100`. So `DEPTH = 101` doesn't change the answer, but it's right at the edge: if you change the rules or dice, raise it.

## 6. Why the recursion terminates

Every roll you survive adds at least one die to the board, so within a run `r1 + r2 + c` strictly increases and a run lasts at most 7 rolls. Every completed run increases `t` by at least 7 points (seven dice, each worth at least 1), so after at most `DEPTH / 7` runs the cutoff kicks in. The states form a **directed acyclic graph**, so recursion with memoization visits each state once.

## 7. Memoization and output

`play_value` stores its result in the module-level `cache` dict, keyed by state. Without it, the same state would be recomputed for every path leading to it, which is exponentially many.

`solve()`:
1. Calls `E((0, 0, 0, 0))`, which fills `cache` with the play value of every reachable state.
2. Returns the expected score of a turn and the sorted cache `Q`.
3. Clears the cache.

[solve.py](solve.py) pickles `Q` into `solution.pkl`. With the current rules this is:

| | |
|---|---|
| Expected score per turn | **12.726** |
| States stored | 7,252 (with `DEPTH = 101`) |
| Highest `t` reached | 132 |
| Runtime | about 2.5 s |

A full board is the same state as the fresh run it leads to: `(100, 0, 4, 3)` is `(132, 0, 0, 0)`. `canonical()` maps full boards to the fresh run, so only one of them is stored. Look up `Q[canonical(state)]` when a state might be a full board.

## 8. Playing with the solution

`Q` stores only play values, but that's all the bot needs because stop values are cheap to compute:

- **Stop or roll?** Roll if `Q[state] > stop_value(state)`.
- **Which allocation?** Of the states in `possible_allocations(state, roll)`, pick the one with the highest `max(stop_value(s), Q[s])`.

This is what [game/user.py](game/user.py) and [main.py](main.py) do.

## 9. What "optimal" means here

The strategy maximizes the expected score of a single turn. Turns are independent (nothing carries over between them), so over many turns this also maximizes your average score.

It does **not** maximize your chance of winning a game against an opponent. When you're far behind near the end, a risky strategy with a lower average but a higher chance of a big turn can win more often. Taking that into account requires including both players' total scores in the state. That's what the 1v1 solver below does.

---

# The 1v1 solver

[game/win_solver.py](game/win_solver.py) finds the strategy that **minimizes the probability of losing** a two-player game. Run it with [solve_win.py](solve_win.py), which writes `win_solution.pkl`.

## 10. Rules being solved

- Player 1 and player 2 alternate turns. A **round** is P1's turn followed by P2's turn.
- The game ends after the round in which someone reaches 200 points. In the code, `TARGET = 199` and the check is "exceeds `TARGET`".
- Most points wins. Equal points is a tie.
- Both players **minimize their own chance of losing**, so a tie counts as much as a win. When two choices are equally safe, a player prefers the one more likely to win outright.
- A turn starts with a roll: you can't pass.

## 11. Game positions

Between turns, the game is described by the two scores and whose turn it is. Each position has two values, stored in absolute terms:

| | |
|---|---|
| `L1` | probability that player 1 loses |
| `L2` | probability that player 2 loses |

The tie probability is `1 - L1 - L2`. Using absolute values instead of "my loss" means nothing has to be flipped when the turn passes to the other player.

The solver fills three tables (`A` = P1's score, `B` = P2's score):

| Table | Position |
|-------|----------|
| `R[A, B]` | start of a round: P1 is about to play (both scores < 200) |
| `T[A, B]` | P1 has just finished at `A < 200`, P2 is about to play |
| `F[n]` | P1 has finished at 200 or more and leads by `n`: P2's **final** turn |

The answer to "who is favoured?" is `R[0, 0]`. With both players playing optimally:

| | |
|---|---|
| P1 loses | 52.24% |
| P2 loses | 45.88% |
| Tie | 1.89% |

Moving second is an advantage, because P2 gets the last turn knowing exactly what to beat.

## 12. A turn is the same problem with a different payoff

Within a turn, the dice work exactly as in the single-player solver: the same states `(t, r1, r2, c)`, the same rolls and the same allocations. The only difference is what stopping is worth. Instead of "your score", stopping with turn score `s` leads to another game position:

| Turn | Stop with turn score `s` | Bust |
|------|--------------------------|------|
| P1 (start of round) | `T[A+s, B]`, or `F[A+s-B]` if `A+s ≥ 200` | `T[A, B]` |
| P2 (regular) | `R[A, B+s]`, or *P2 wins* if `B+s ≥ 200` | `R[A, B]` |
| P2 (final, trailing by `n`) | win if `s > n`, tie if `s = n`, lose if `s < n` | lose |

So each turn is a single-player problem whose payoff table comes from the positions that follow it. The function `solve_turn` takes that payoff table and returns the value of the turn under the best play: the player picks the allocation and the stop/roll choice that minimize their own loss probability.

Sanity check: give `solve_turn` the payoff "−score" and it reproduces the expected score of the single-player solver, 12.726119…

## 13. Solving order

Any turn that doesn't bust adds at least one point, so `A + B` grows. The solver therefore works through **diagonals** of constant `A + B`, from 398 down to 0. Every position a turn can lead to then lies on a diagonal that's already solved, except when busting:

- P1 busts: `R[A, B]` leads to `T[A, B]` (same scores)
- P2 busts: `T[A, B]` leads back to `R[A, B]`

This loop has a direct solution. With fixed policies, a turn's value is linear in its bust value: `value = a + p_bust · bust_value`, where `p_bust` is the chance the turn ends in a bust. `solve_turn` tracks `p_bust` as a third value next to `L1` and `L2`, so the loop

$$R = a_R + p_R\,T, \qquad T = a_T + p_T\,R$$

can be solved directly: $R = (a_R + p_R a_T) / (1 - p_R p_T)$. The best policies depend on the bust value, so this repeats with the new `R` until it stops changing (policy iteration). That usually takes 2–3 rounds.

## 14. Making it fast

The game has about 40,000 round positions and as many P2 positions. Each one needs a full turn solve, and some solves are repeated during policy iteration. Doing that one position at a time in Python would take days, so:

- **Rolls are grouped.** Rolls that allow the same set of allocations are merged. This reduces the 5,464 (configuration, roll) pairs and 17,054 allocation options per banked score to 1,067 groups with 6,276 options.
- **Positions are batched with numpy.** All positions on one diagonal are solved together as columns of the same arrays.
- **Positions finish at different times.** Each position has its own banking limit, and columns are sorted so that only positions still in play are computed.
- **Diagonals are split over CPU cores.** Positions on the same diagonal don't depend on each other.

With these, the full solve takes about 20 minutes on a 16-core machine.

## 15. Approximations

Two caps keep the tables finite. Both are far beyond anything that matters in practice:

- **`NEED_CAP` (300):** P2's final-turn table stops at a 300-point deficit. Beyond that, P2's chance of not losing is below 10⁻⁶.
- **`LEAD_CAP` (150):** once P1 has 200 or more and leads by 150, P1 stops rolling fresh sets of dice. With a 40-point target, the tables with cap 150 and with cap 300 are **identical**, so the cap doesn't change any decision.

## 16. Verification

With the target set to 40, I solved the game, then simulated 100,000 games in which both players follow `turn_policy`. The simulation uses its own implementation of the rules:

| | Solver | Simulation |
|---|---|---|
| P1 wins | 41.40% | 41.44% |
| P2 wins | 54.47% | 54.44% |
| Tie | 4.13% | 4.12% |

## 17. Playing with the solution

`turn_policy(R, T, F, my_score, opp_score, first)` solves the current turn for one position and returns `{(t, r1, r2, c): (stop, play)}`. Each value is a tuple `(P(I lose), -P(I win))`, so **smaller is better** and comparing tuples gives the solver's own tie-breaking:

- **Which allocation?** Pick the state with the smallest `min(stop, play)`.
- **Stop or roll?** Roll if `play < stop`.

A bot has to call this at the start of each turn, which takes a fraction of a second.
