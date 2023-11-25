from game import Move, PointChange, PointsResult


def future_point_change_score(change: PointChange) -> float:
    if change.completed:
        return 0

    if change.points == 1:
        return 0.01
    elif change.points == 2:
        score = 0.6
    elif change.points == 3:
        score = 1.2
    elif change.points == 4:
        score = 1.8
    elif change.points == 5:
        score = 2.5
    else:
        score = 3

    score /= change.space_left

    return score


# Evaluates a players position
def player_evaluation(points_result: PointsResult) -> float:
    basic_points = (
        sum(
            (change.points if change.completed else 0)
            for change in points_result.point_changes
        )
        - points_result.negative_floor_points
        + points_result.bonus_points
    )

    # Only count future point increases that are greater than 1 as helpful
    future_points = sum(map(future_point_change_score, points_result.point_changes))

    return basic_points + future_points


# Decides how promising a move is
def move_potential(move: Move) -> float:
    return move.amount - len(move.floor_tiles)
