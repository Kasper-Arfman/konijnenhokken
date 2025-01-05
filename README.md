# Konijnenhokken
Konijnenhokken is a dice game by 999 Games in which you score points by building a **base score** and a **multiplier**. You play by rolling 7 regular dice, which can be allocated to score points:
1. base +1 
2. base +2 **OR** multiplier x2
3. multiplier x3
4. multiplier x4
5. multiplier x5
6. nothing

Your goal is to score as many points as possible (base_score * max_multiplier) by allocating dice and knowing when to stop to cash out your score.

## How to play
 A turn consists of two steps:
1. Allocating dice
2. Deciding whether to continue

 You may allocate the dice as you like, but there are two rules:
1. After every roll, **you must increase the base score**. If you can't (no 1 or 2 was rolled) you end the turn with 0 points.
2. Multipliers must be collected in order (2x -> 3x -> 4x -> 5x). Only your highest multiplier counts

Next, the player decides to **stop** or to **roll again**:
 - **stop**: collect points (base_score * max_multiplier)
 - **play**: roll the remaining dice, for a chance to score more points. If no dice are left, write down an intermediate score and start a new run with all seven dice.
    * N.B. points acquired in a previous run can still be lost.


## Solving the game
Konijnenhokken is a solveable game. In other words, it is always possible to calculate which choice will on average award you the most points.

This repository:
 - **versus.py** Play the game with a graphical user interface, solo or versus bots.
 - **solve.py** Figure out which strategy earns the most points on average
 - **test.py** Let the bot play many games and measure its performance



## Disclaimner
The solution presented here optimizes the expected score not the win probability. The latter is a more complex problem, because the best strategy will depend on your current position (winning or losing). If you are winning, you might favor a strategy that earns fewer points with more certainty. Conversely, a losing player might favour a strategy that has a small chance of earning many points.

---
