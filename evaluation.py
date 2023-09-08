from typing import Callable, TypedDict
from constants import *
from game import Game, Move
from player import Player
from importlib import import_module


class EvaluationVersion(TypedDict):
    player_evaluation: Callable[[Game, Player], float]
    move_potential: Callable[[Move], float]


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
    game: Game, player_evaluation: Callable[[Game, Player], float]
) -> float:
    player1 = player_evaluation(game, game.players[0])
    player2 = player_evaluation(game, game.players[1])

    return player1 - player2


# Considers who the active player is
def game_evaluation_for_player(
    turn: int, game: Game, player_evaluation: Callable[[Game, Player], float]
) -> float:
    multiplier = 1 if turn == 0 else -1
    return multiplier * game_evaluation(game, player_evaluation)
