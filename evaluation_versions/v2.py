from game import Game, Move
from player import Player


# Evaluates a players position
def player_evaluation(game: Game, player: Player) -> float:
    return player.points


# Decides how promising a move is
def move_potential(move: Move) -> float:
    return move.amount - len(move.floor_tiles)
