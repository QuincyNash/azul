from game import Game, Move
from player import Player
import random


# Evaluates a players position
def player_evaluation(game: Game, player: Player) -> float:
    return random.random()


# Decides how promising a move is
def move_potential(move: Move) -> float:
    return move.amount - len(move.floor_tiles)
