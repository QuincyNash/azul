from constants import *
from pytest_benchmark.fixture import BenchmarkFixture as Benchmark
from game import Game
from search import negascout
from evaluation import game_evaluation, load_player_eval


def test_negascout(benchmark: Benchmark):
    game = Game(seed=0)
    benchmark(negascout, load_player_eval(EVALUATION_VERSION), game, 0, 2, 2)


def test_serialize(benchmark: Benchmark):
    game = Game(seed=0)
    benchmark(game.serialize)


def test_no_moves(benchmark: Benchmark):
    game = Game(seed=0)
    benchmark(game.are_no_moves)


def test_moves(benchmark: Benchmark):
    game = Game(seed=0)
    benchmark(game.all_moves, 0)


def test_make_move(benchmark: Benchmark):
    game = Game(seed=0)
    benchmark(game.make_move, 0, game.all_moves(0)[0])


def test_undo_move(benchmark: Benchmark):
    game = Game(seed=0)
    benchmark(game.undo_move, 0, game.all_moves(0)[0])


def test_points(benchmark: Benchmark):
    game = Game(seed=0)
    func = lambda: game.calculate_points()
    benchmark(func)


def test_evaluation(benchmark: Benchmark):
    game = Game(seed=0)
    points_result = game.calculate_points()
    player_eval = load_player_eval("v4")
    benchmark(
        game_evaluation,
        game,
        game.players[0],
        points_result,
        player_eval["player_evaluation"],
    )
