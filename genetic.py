from constants import *
from typing import List
import random
from multiprocessing import Manager
from evaluation import load_player_eval
from compare import play_game
from pygad import GA
import pygad.torchga as torchga
import torch.nn as nn
from torch import save


def fitness_func(ga_instance: GA, solution: List[float], sol_index: int):
    old_eval = load_player_eval("v4")
    new_eval = load_player_eval("v4", nn_weights=solution)

    fitness = 0
    for _ in range(10):
        seed = random.randint(0, 100000)
        result1 = play_game(
            5,
            new_eval,
            old_eval,
            first_player=0,
            seed=seed,
            depth_limit=1,
        )
        result2 = play_game(
            5,
            new_eval,
            old_eval,
            first_player=1,
            seed=seed,
            depth_limit=1,
        )

        fitness += result1 + result2

    print(f"# {sol_index}: {fitness}")

    if fitness > 150:
        state_dict = torchga.model_weights_as_dict(base_model(), solution)
        save(state_dict, "nn_evaluation.pt")
        print(f"New best model with fitness {fitness}")

    return fitness


def on_generation(ga_instance: GA):
    print(f"Finished generation #{ga_instance.generations_completed}")


def base_model():
    return nn.Sequential(
        nn.Linear(18, 64),
        nn.Sigmoid(),
        nn.Linear(64, 64),
        nn.ReLU(),
        nn.Linear(64, 1),
        nn.ReLU(),
    )


if __name__ == "__main__":
    model = base_model()

    torch_ga = torchga.TorchGA(model=model, num_solutions=200)
    torch_ga.create_population()

    ga = GA(
        fitness_func=fitness_func,
        initial_population=torch_ga.population_weights,
        num_generations=50,
        num_parents_mating=20,
        parent_selection_type="rws",
        crossover_type="uniform",
        mutation_type="adaptive",
        mutation_probability=[0.1, 0.05],
        init_range_high=1,
        init_range_low=-1,
        on_generation=on_generation,
        parallel_processing=["process", 8],
    )
    ga.run()
    ga.plot_fitness()
