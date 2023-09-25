from typing import Callable, TypedDict
from constants import *
from game import PointsResult, Game, Move
from player import Player
from importlib import import_module


class EvaluationVersion(TypedDict):
    player_evaluation: Callable[[PointsResult], float]
    move_potential: Callable[[Game, Move], float]


def load_player_eval(version: str) -> EvaluationVersion:
    module = import_module(f"evaluation_versions.{version}")
    evaluation = module.player_evaluation
    potential = module.move_potential
    return {
        "player_evaluation": evaluation,
        "move_potential": potential,
    }


# Evaluation always ranks the position from the point of view of player 1
def game_evaluation(
    points_results: List[PointsResult],
    player_evaluation: Callable[[PointsResult], float],
) -> float:
    player1 = player_evaluation(points_results[0])
    player2 = player_evaluation(points_results[1])

    return player1 - player2


# Considers who the active player is
def game_evaluation_for_player(
    turn: int,
    points_results: List[PointsResult],
    player_evaluation: Callable[[PointsResult], float],
) -> float:
    multiplier = 1 if turn == 0 else -1
    return multiplier * game_evaluation(points_results, player_evaluation)
