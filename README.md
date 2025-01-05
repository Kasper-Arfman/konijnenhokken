Konijnenhokken is a dice game in which you score points by building a base score and a multiplier.
You play by rolling 7 regular dice, which can be allocated to score points:
 1 -> base +1 
 2 -> base +2 OR x2 multiplier
 3 -> x3 multiplier
 4 -> x4 mulitplier
 5 -> x5 multiplier
 6 -> nothing
Your score will be calculated as base_score * max_multiplier

 A turn consists of two steps:
  - allocating dice
  - deciding whether to continue

 You may allocate the dice as you like, but there are two rules:
  - After every roll, you must increase the base score. Otherwise, you end the turn with 0 points.
  - Multipliers must be collected in order (2x -> 3x -> 4x -> 5x). Only your highest multiplier counts

Next, the player decides to stop or to continue playing.
 - stop: collect your points (base_score * max_multiplier)
 - play: roll again with the remaining dice, for a chance to score more points.
    * If no dice are left, write down an intermediate score and start a new run with all seven dice.
    * N.B. points acquired in a previous run can still be lost.

 
