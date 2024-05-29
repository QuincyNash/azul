from __future__ import annotations
from typing import Callable, TypedDict, List
from constants import *
from importlib import import_module
from game import Game, PointsResult, Move
from player import Player


class EvaluationVersion(TypedDict):
    player_evaluation: Callable[[Game, Player, PointsResult], float]
    move_potential: Callable[[Move], float]


def load_player_eval(
    version: str, *, nn_weights: Union[List[float], None] = None
) -> EvaluationVersion:
    module = import_module(f"evaluation_versions.{version}")

    if hasattr(module, "player_evaluation"):
        evaluation = module.player_evaluation
    elif nn_weights is None:
        evaluation = module.create_player_evaluation()
    else:
        evaluation = module.create_player_evaluation(nn_weights)

    potential = module.move_potential
    return {
        "player_evaluation": evaluation,
        "move_potential": potential,
    }


# Evaluation always ranks the position from the point of view of player 1
def game_evaluation(
    game: Game,
    player1: Player,
    player2: Player,
    points_results: List[PointsResult],
    player_evaluation: Callable[[Game, Player, PointsResult], float],
) -> float:
    player1_eval = player_evaluation(game, player1, points_results[0])
    player2_eval = player_evaluation(game, player2, points_results[1])

    return player1_eval - player2_eval


# Considers who the active player is
def game_evaluation_for_player(
    turn: int,
    game: Game,
    player1: Player,
    player2: Player,
    points_results: List[PointsResult],
    player_evaluation: Callable[[Game, Player, PointsResult], float],
) -> float:
    multiplier = 1 if turn == 0 else -1
    return multiplier * game_evaluation(
        game, player1, player2, points_results, player_evaluation
    )
