from constants import *
from game import Game, Move
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

    game2 = game.copy()
    game2.calculate_points(flag="normal")

    game3 = game.copy()
    game3.players[0].wall[2][2] = True
    game3.calculate_points(flag="bonus_only")

    game.calculate_points(flag="include_bonus")

    assert (
        game.players[0].points
        == FIVE_OF_A_KIND_BONUS + VERTICAL_LINE_BONUS + HORIZONTAL_LINE_BONUS + 9
    )
    assert game2.players[0].points == 9
    assert (
        game3.players[0].points
        == FIVE_OF_A_KIND_BONUS + VERTICAL_LINE_BONUS + HORIZONTAL_LINE_BONUS
    )


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


def test_game_get_state_after_move():
    game = Game()
    game.factories = [
        Counter({BLUE: 2}),
        Counter({BLACK: 1}),
        Counter({RED: 1}),
        Counter({YELLOW: 1}),
        Counter({STAR: 1}),
    ]
    move = game.all_moves(0)[1]

    game2 = Game()
    game2.factories = [
        Counter(),
        Counter({BLACK: 1}),
        Counter({RED: 1}),
        Counter({YELLOW: 1}),
        Counter({STAR: 1}),
    ]
    game2.players[0].pattern_lines[0].tile = BLUE
    game2.players[0].pattern_lines[0].space = 0
    game2.players[0].floor = [BLUE]

    game = game.get_state_after_move(0, move)

    assert game.serialize() == game2.serialize()
