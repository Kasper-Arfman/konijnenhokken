


# starting state

# [x] find all the states

# Out of those states, find the states that have 7 total.
# These are possible turn_scores

d = {}
n = 0
scores = set()
for r1 in range(8):
    for r2 in range(8-r1):
        for c in range(min(8-r1-r2, 5)):

            if r1 + r2 + c == 7:
                score = (r1 + 2*r2) * (c+1)
                # print(score)
                scores.add(score)



def find_composable_numbers(scores, limit):
    # Initialize the DP array
    dp = [False] * (limit + 1)
    dp[0] = True  # Base case: 0 can always be formed with no elements
    
    # Update dp array for each score
    for score in scores:
        for j in range(score, limit + 1):
            if dp[j - score]:
                dp[j] = True
    
    # Extract all numbers that can be formed
    return [i for i in range(limit) if dp[i]]

scores = list(sorted(scores))
print(scores)
scores = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 21, 22, 24, 25, 27, 28, 30, 32]



numbers = find_composable_numbers(scores, 100)
print(numbers, len(numbers))