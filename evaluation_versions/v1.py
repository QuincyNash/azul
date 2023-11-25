from game import Move, PointsResult
import random


# Evaluates a players position
def player_evaluation(points_result: PointsResult) -> float:
    return random.random()


# Decides how promising a move is
def move_potential(move: Move) -> float:
    return move.amount - len(move.floor_tiles)
