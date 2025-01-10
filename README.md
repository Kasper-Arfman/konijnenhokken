# Konijnenhokken
Konijnenhokken is a dice game by 999 Games in which you score points by building a **base score** (rabbits) and a **multiplier** (cages). You play by rolling 7 regular dice, which can be allocated to score points:
1. base +1 
2. base +2 **OR** multiplier x2
3. multiplier x3
4. multiplier x4
5. multiplier x5
6. nothing

Your goal is to score as many points as possible (base_score * max_multiplier) by allocating dice and stopping in time to solidify your earnings.

## How to play
 A turn consists of two steps:
1. Allocating dice
2. Deciding whether to continue

 (1) You may allocate the dice as you like, but there are two rules:
- After every roll, **you must increase the base score**. If you can't (*i.e.* no 1 or 2 was rolled) you end the turn with no points.
- Multipliers must be collected in order (2x -> 3x -> 4x -> 5x). Only your highest multiplier counts

(2) After allocating, the player decides to **stop** or to **roll again**:
 - **stop**: collect points (base_score * max_multiplier)
 - **play**: roll the remaining dice for a chance to score more points. If no dice are left, note down your current total and start a new run using all seven dice.
    * N.B. points acquired in a previous run can still be lost.

## Contents
Konijnenhokken is a solveable game. In other words, it is possible to calculate which choice will on average award you the most points. This repository allows for the computation of the optimal strategy.

 - **versus.py** Play the game with a graphical user interface, solo or versus bots.
 - **solve.py** Find the strategy that maximizes expected gains.
 - **test.py** Let the bot play many games to measure its performance

## Solving the Game
Konijnenhokken can be understood through a network of nodes and vertices. Here, nodes represent the possible states of the game, and vertices indicate which transfers are possible. A player taking his turn is analogous to a traversal along the network.

A state (snapshot of the game) can be fully described by just four numbers:
- $r_1$: number of ones allocated
- $r_2$: number of twos allocated as rabbits
- $c$: number of cages allocated
- $t$: points obtained in previous runs of this turn

Moreover, every state is given a value, $E(\text{state})$, that indicates how many points you can expect from it:

$$E(\text{state}) = \max(\text{stop(state)}, \text{play(state)})$$

where

-  **stop_value**: the number of points you get by stopping.
   $$\text{stop(state)} = t + (r_1 + 2r_2) * (1 + c)$$
-  **play_value**: the number of points you can expect if you roll again.

$$ \text{play(state)} = \sum\limits_{\text{roll}} P(\text{roll}) \cdot E(\text{state} \mid \text{roll}) $$

Here, $P(\text{roll})$ is the probability of a roll, and $E(\text{state} \mid \text{roll})$ is the value of the best allocation choice given this roll:

$$
E(\text{state} \mid \text{roll}) = \max_{\text{allocations}(\text{state}, \text{roll})} E(\text{state})
$$

Once we know the value of some states, we can use the above formulas to determine values of all the other states. So all we need now is a starting point (a state whose value is known). The key here is to realize that stopping is always going to be the best strategy when you have a lot of points. So if we choose a sufficiently large threshold, $t_{max}$, we can say:

$$
E(\text{state}) = 
\begin{cases}
\text{stop}(state) & (\text{if } t > t_{max}) \\
\end{cases}
$$

Once the stop_value and play_value are known, making choices in the game is a piece of cake:
 - **Stop or play**: roll again if play_value > stop_value
 - **Allocating dice**: select the destination that has the greatest $E(state)$



## Disclaimer
The solution presented here optimizes the expected score not the win probability. The latter is a more complex problem, because the best strategy will depend on your current position (winning or losing). If you are winning, you might favor a strategy that earns fewer points with more certainty. Conversely, a losing player might favour a strategy that has a small chance of earning many points.

---
