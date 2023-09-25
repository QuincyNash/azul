from constants import *
from game import Game, Move, PointChange
from collections import Counter
import random
import pytest


def test_game_init():
    game = Game(seed=0)
    assert isinstance(game, Game)


def test_game_serialize():
    game1 = Game(seed=0)
    game2 = Game(seed=0)
    random.shuffle(game2.factories)

    assert game1.serialize() == game2.serialize()


def test_game_copy():
    game = Game(seed=0)
    game_copy = game.copy()

    assert game.serialize() == game_copy.serialize()


def test_game_points():
    game = Game(seed=0)

    game.players[0].pattern_lines[2].tile = BLUE
    game.players[0].pattern_lines[2].space = 0

    five_of_a_kind_pos = [[0, 0], [1, 1], [3, 3], [4, 4]]
    vertical_line_pos = [[2, 0], [2, 1], [2, 3], [2, 4]]
    horizontal_line_pos = [[0, 2], [1, 2], [3, 2], [4, 2]]

    for x_pos, y_pos in five_of_a_kind_pos + vertical_line_pos + horizontal_line_pos:
        game.players[0].wall[x_pos][y_pos] = True

    og_game = game.copy()
    og_serialized = game.serialize()

    game2 = og_game.copy()
    game2.calculate_points(flag="normal", modify_game=True)

    game3 = og_game.copy()
    game3.players[0].wall[2][2] = True
    game3.calculate_points(flag="bonus_only", modify_game=True)

    game = og_game.copy()
    game.calculate_points(flag="include_bonus", modify_game=True)

    assert og_serialized != game.serialize()
    assert og_serialized != game2.serialize()
    assert og_serialized != game3.serialize()

    assert (
        game.players[0].points
        == FIVE_OF_A_KIND_BONUS + VERTICAL_LINE_BONUS + HORIZONTAL_LINE_BONUS + 9
    )
    assert game2.players[0].points == 9
    assert (
        game3.players[0].points
        == FIVE_OF_A_KIND_BONUS + VERTICAL_LINE_BONUS + HORIZONTAL_LINE_BONUS
    )

    game2_points = og_game.calculate_points(flag="normal")[0]

    game3 = og_game.copy()
    game3.players[0].wall[2][2] = True
    game3_points = game3.calculate_points(flag="bonus_only")[0]

    game_points = og_game.calculate_points(flag="include_bonus")[0]

    assert og_game.serialize() == og_serialized

    assert isinstance(game_points.point_changes[0], PointChange)
    assert game2_points.bonus_points == 0 and game2_points.negative_floor_points == 0
    assert (
        game3_points.bonus_points
        == FIVE_OF_A_KIND_BONUS + VERTICAL_LINE_BONUS + HORIZONTAL_LINE_BONUS
        and game3_points.negative_floor_points == 0
    )
    assert (
        game_points.bonus_points
        == FIVE_OF_A_KIND_BONUS + VERTICAL_LINE_BONUS + HORIZONTAL_LINE_BONUS
        and game_points.negative_floor_points == 0
    )
    assert (
        sum([point_change.points for point_change in game2_points.point_changes]) == 9
    )
    assert sum([point_change.points for point_change in game_points.point_changes]) == 9


def test_game_all_moves():
    game = Game()
    game.factories = [
        Counter({BLUE: 1}),
        Counter({BLACK: 1}),
        Counter({RED: 1}),
        Counter({YELLOW: 1}),
        Counter({STAR: 1}),
    ]

    for player_index in range(1):
        for line_index in range(WALL_SIZE):
            game.players[player_index].pattern_lines[line_index].tile = EMPTY
            game.players[player_index].pattern_lines[line_index].space = line_index + 1

        moves = game.all_moves(player_index)
        assert moves is not None
        assert isinstance(moves[0], Move)
        assert len(moves) == FACTORY_COUNT * (WALL_SIZE + 1)


def test_are_no_moves():
    game = Game()
    game.factories = [Counter() for _ in range(5)]
    game.center_pile = Counter()

    assert game.are_no_moves()


def test_game_state():
    game = Game(seed=0)
    moves = game.all_moves(0)

    game.make_move(0, moves[0])

    original_game = game.serialize()
    moves = game.all_moves(1)

    for move in moves:
        print(game)

        game.make_move(0, move)
        game.undo_move(0, move)

        print(move, game)
        assert game.serialize() == original_game
