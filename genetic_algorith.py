import random

def fitness(individual):
    # Example: Maximize the sum of the array
    return sum(individual)

def initialize_population(pop_size, array_length, lower_bound, upper_bound):
    return [[random.uniform(lower_bound, upper_bound) for _ in range(array_length)] for _ in range(pop_size)]

def select(population, fitnesses, tournament_size=3):
    selected = random.choices(range(len(population)), k=tournament_size)
    best_idx = max(selected, key=lambda idx: fitnesses[idx])
    return population[best_idx]

def crossover(parent1, parent2):
    point = random.randint(1, len(parent1) - 1)
    return parent1[:point] + parent2[point:]

def mutate(individual, mutation_rate=0.1, mutation_strength=1.0):
    for i in range(len(individual)):
        if random.random() < mutation_rate:
            individual[i] += random.uniform(-mutation_strength, mutation_strength)

def genetic_algorithm(
    pop_size=100, array_length=10, lower_bound=0, upper_bound=10,
    generations=100, mutation_rate=0.1, mutation_strength=1.0
):
    # Initialize population
    population = initialize_population(pop_size, array_length, lower_bound, upper_bound)
    best_individual = None
    best_fitness = float('-inf')

    for gen in range(generations):
        # Evaluate fitness
        fitnesses = [fitness(ind) for ind in population]
        gen_best_idx = fitnesses.index(max(fitnesses))
        if fitnesses[gen_best_idx] > best_fitness:
            best_fitness = fitnesses[gen_best_idx]
            best_individual = population[gen_best_idx]

        # Create new population
        new_population = []
        for _ in range(pop_size):
            parent1 = select(population, fitnesses)
            parent2 = select(population, fitnesses)
            offspring = crossover(parent1, parent2)
            mutate(offspring, mutation_rate, mutation_strength)
            new_population.append(offspring)

        population = new_population
        print(f"Generation {gen + 1}: Best Fitness = {best_fitness:.2f}")

    return best_individual, best_fitness

# Example usage
best_individual, best_fitness = genetic_algorithm()
print(f"Best Individual: {best_individual}")
print(f"Best Fitness: {best_fitness:.2f}")
