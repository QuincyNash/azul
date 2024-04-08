from game import Game, Move, PointsResult
import random

from player import Player


# Evaluates a players position
def player_evaluation(game: Game, player: Player, points_result: PointsResult) -> float:
    return random.random()


# Decides how promising a move is
def move_potential(move: Move) -> float:
    return move.amount - len(move.floor_tiles)
