from game import Game, Move, PointsResult
from player import Player


# Evaluates a players position
def player_evaluation(game: Game, player: Player, points_result: PointsResult) -> float:
    return (
        sum(
            (change.points if change.completed else 0)
            for change in points_result.point_changes
        )
        - points_result.negative_floor_points
        + points_result.bonus_points
    )


# Decides how promising a move is
def move_potential(move: Move) -> float:
    return move.amount - len(move.floor_tiles)
