from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from math import ceil, exp
from typing import Set
from constants import *
from game import Game, Move, PointsResult
from player import Player


@dataclass
class TileDifficulty:
    probability: float
    moves: int
    floor_tiles: int


def future_point_importance(game: Game):
    longest_line = 0
    for player in game.players:
        longest_line = max(longest_line, max(map(sum, player.wall)))

    return ENDGAME_IMPORTANCE_SCORES[longest_line]


def point_eval(points_result: PointsResult) -> int:
    return (
        sum(
            (change.points if change.completed else 0)
            for change in points_result.point_changes
        )
        - points_result.negative_floor_points
        + points_result.bonus_points
    )


def moves_left_in_round(game: Game) -> int:
    max_moves = 0
    min_moves = 0

    for index, factory in enumerate([*game.factories, game.center_pile]):
        count = len(factory) - factory[STARTING_MARKER]
        max_moves += count

        if count > 0 and index != FACTORY_COUNT:
            min_moves += 1

    if max_moves == len(game.center_pile) - game.center_pile[STARTING_MARKER]:
        return ceil(count / 2)

    min_moves += max(len(game.center_pile) - game.center_pile[STARTING_MARKER], 3)
    min_moves = min(min_moves, max_moves)
    average_moves = (max_moves + min_moves) // 2

    return average_moves // 2


# Estimates the probabiliy of acquiring n groups of some number of tiles out of a pool of tile groups
def acquire_sigmoid(n: int, total: int) -> float:
    a, b = REGRESSION_CONSTANTS[total - 1]

    return 1 - 1 / (1 + b * exp(-a * n))


def combine_difficulties(
    diff1: TileDifficulty, diff2: TileDifficulty
) -> TileDifficulty:
    prob_sum = diff1.probability + diff2.probability
    probability = prob_sum - diff1.probability * diff2.probability

    return TileDifficulty(probability, diff1.moves, diff1.floor_tiles)


# Returns result as a dictionary with the probabililty of tgetting the tiles and the number of moves required, combined with any expected point loss from floor tiles
def difficulty_to_acquire(tile: Tile, amount: int, game: Game) -> TileDifficulty:
    total_tile_count = sum(
        factory[tile] for factory in [*game.factories, game.center_pile]
    )

    tile_abundance_counts = Counter()
    for factory in [*game.factories, game.center_pile]:
        tile_abundance_counts[factory[tile]] += 1
    del tile_abundance_counts[0]

    if total_tile_count < amount:
        return TileDifficulty(probability=0, moves=1, floor_tiles=0)

    found = False
    for num_moves in range(1, amount + 1):
        partitions = PARTITIONS[amount][num_moves]
        possibilities: List[TileDifficulty] = []

        for partition in partitions:
            if all(tile_abundance_counts[n] >= partition[n] for n in partition):
                found = True
                probability = 1

                for n in partition:
                    probability *= acquire_sigmoid(
                        partition[n], tile_abundance_counts[n]
                    )

                possibilities.append(
                    TileDifficulty(
                        probability=probability, moves=num_moves, floor_tiles=0
                    )
                )

        if found:
            break

    if len(possibilities) == 2:
        return combine_difficulties(possibilities[0], possibilities[1])
    elif len(possibilities) == 1:
        return possibilities[0]
    else:
        abundance_array = [
            key for key, value in tile_abundance_counts.items() for _ in range(value)
        ]
        smallest_floor_tiles = 99999999
        best_moves = 0
        best_probability = 0

        for r in range(1, len(abundance_array) + 1):
            for combination in combinations(abundance_array, r):
                floor_tiles = sum(combination) - amount

                if floor_tiles > 0 and floor_tiles < smallest_floor_tiles:
                    smallest_floor_tiles = floor_tiles
                    best_moves = r

                    counter = Counter(combination)
                    probability = 1
                    for n in counter:
                        probability *= acquire_sigmoid(
                            counter[n], tile_abundance_counts[n]
                        )
                    best_probability = probability
                    if smallest_floor_tiles == 1:
                        break
            if smallest_floor_tiles == 1:
                break

        return TileDifficulty(
            probability=best_probability,
            moves=best_moves,
            floor_tiles=smallest_floor_tiles,
        )


def rank_option(
    option: TileDifficulty,
    points: float,
) -> float:
    return option.probability / option.moves * points


# Evaluates a players position
def player_evaluation(game: Game, player: Player, points_result: PointsResult) -> float:
    moves_left = moves_left_in_round(game)

    # If the game is almost completely over (last turn for current player), return the pure points
    if points_result.last_round + moves_left == 1:
        return point_eval(points_result)

    added_tiles: List[Tuple[int, int]] = []

    # Move completed lines over
    for row in range(WALL_SIZE):
        tile = player.pattern_lines[row].tile
        if player.pattern_lines[row].space == 0 and tile != EMPTY:
            player.wall[row][TILE_POSITIONS[tile][row]] = True
            added_tiles.append((TILE_POSITIONS[tile][row], row))

    chaining_wall = [[col for col in row] for row in player.wall]
    for row in range(WALL_SIZE):
        tile = player.pattern_lines[row].tile
        if tile != EMPTY:
            chaining_wall[row][TILE_POSITIONS[tile][row]] = True

    choices: List[Tuple[TileDifficulty, float]] = []
    for row in range(WALL_SIZE):
        line = player.pattern_lines[row]

        if line.tile != EMPTY and line.space != 0:
            chaining_wall[row][TILE_POSITIONS[line.tile][row]] = False
            chaining_points = game.calculate_potential_points(
                chaining_wall, line.tile, row
            )
            chaining_wall[row][TILE_POSITIONS[line.tile][row]] = True

            basic_points = game.calculate_potential_points(player.wall, line.tile, row)
            points = (chaining_points + basic_points) / 2

            difficulty = difficulty_to_acquire(line.tile, line.space, game)

            floor_points = game.calculate_negative_floor_points(
                difficulty.floor_tiles + len(player.floor) + 1
            ) - game.calculate_negative_floor_points(
                len(player.floor)
            )  # +1 here is to encourage the algorithm to take a less risky option that doesn't involve going down, since this calculation is not perfect, because it doesn't consider points already lost or about to be lost on the floor

            choices.append((difficulty, points - floor_points))
            chaining_wall[row][TILE_POSITIONS[line.tile][row]] = True
        else:
            row_options: List[Tuple[TileDifficulty, float, Tile]] = []
            for tile in TILE_TYPES:
                if not player.wall[row][TILE_POSITIONS[tile][row]]:
                    chaining_points = game.calculate_potential_points(
                        chaining_wall, tile, row
                    )
                    basic_points = game.calculate_potential_points(
                        player.wall, tile, row
                    )
                    points = (chaining_points + basic_points) / 2

                    difficulty = difficulty_to_acquire(tile, row + 1, game)

                    floor_points = game.calculate_negative_floor_points(
                        difficulty.floor_tiles
                        + len(player.floor)
                        + (1 if difficulty.floor_tiles > 0 else 0)
                    ) - game.calculate_negative_floor_points(len(player.floor))

                    row_options.append((difficulty, points - floor_points, tile))

            if len(row_options) > 0:
                best_option = max(row_options, key=lambda x: rank_option(x[0], x[1]))
                if best_option[0].probability > 0:
                    choices.append(best_option[:2])
                    chaining_wall[row][TILE_POSITIONS[best_option[2]][row]] = True

    best_score: float = 0.0
    for r in range(1, len(choices) + 1):
        for combination in combinations(choices, r):
            move_sum = sum(choice.moves for choice, _ in combination)
            points_sum = sum(
                rank_option(choice, points) for choice, points in combination
            )

            if move_sum <= moves_left:
                best_score = max(best_score, points_sum)

    # Reset completed lines over
    for added_x, added_y in added_tiles:
        player.wall[added_y][added_x] = False

    return player.points + best_score


# Decides how promising a move is
def move_potential(move: Move) -> float:
    return move.amount - len(move.floor_tiles)
