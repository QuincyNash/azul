from game import Game, Move, PointsResult
from player import Player
import random


# Evaluates a players position
def player_evaluation(points_result: PointsResult) -> float:
    return random.random()


# Decides how promising a move is
def move_potential(game: Game, move: Move) -> float:
    return move.amount - len(move.floor_tiles)
