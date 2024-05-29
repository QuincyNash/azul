from collections import Counter
from typing import Callable, List, Union
from functools import partial
from constants import *
from game import Factory, Game, Move, PointChange, PointsResult
from player import Player
from genetic import base_model
import torch
import torch.nn as nn
import pygad.torchga as torchga


# Decides how promising a move is
def move_potential(move: Move) -> float:
    return move.amount - len(move.floor_tiles)


def nn_evaluation(
    model: nn.Sequential, game: Game, player: Player, points_result: PointsResult
) -> float:
    basic_points = (
        sum(
            (change.points if change.completed else 0)
            for change in points_result.point_changes
        )
        - points_result.negative_floor_points
        + points_result.bonus_points
    )

    inputs: List[float] = []

    def get_point_change(row: int) -> Union[PointChange, None]:
        for change in points_result.point_changes:
            if change.pattern_line == row:
                return change

        return None

    # Give extra bonus for placing tiles in the middle on the first round
    if game.is_first_round:
        for change in points_result.point_changes:
            if TILE_POSITIONS[change.tile][change.pattern_line] in [1, 2, 3]:
                basic_points += 0.5

    total_tile_counts: Factory = Counter()
    for factory in [*game.factories, game.center_pile]:
        total_tile_counts += Counter(factory)

    for row, line in enumerate(player.pattern_lines):
        inputs.append(line.space)

        point_change = get_point_change(row)
        if point_change and not point_change.completed:
            potential_points = point_change.points
        else:
            potential_points = 0

        inputs.append(potential_points)
        inputs.append(0 if line.tile == EMPTY else total_tile_counts[line.tile])

    inputs.append(len(player.floor))
    inputs.append(int(player.has_starting_marker))

    most_tiles_in_row = 0
    for test_player in game.players:
        for row in range(WALL_SIZE):
            tiles_in_row = sum(test_player.wall[row])
            most_tiles_in_row = max(most_tiles_in_row, tiles_in_row)
    inputs.append(WALL_SIZE - most_tiles_in_row)

    result: torch.Tensor = model.forward(torch.Tensor(inputs))

    return basic_points + result.item()


def create_player_evaluation(
    nn_weights: Union[None, List[float]] = None
) -> Callable[[Game, Player, PointsResult], float]:
    model = base_model()

    if nn_weights is None:
        state_dict = torch.load("nn_evaluation.pt")
    else:
        state_dict = torchga.model_weights_as_dict(model, nn_weights)

    model.load_state_dict(state_dict)
    model.eval()

    return partial(nn_evaluation, model)
