from pytest_benchmark.fixture import BenchmarkFixture as Benchmark
from game import Game
from search import negascout
from evaluation import game_evaluation, load_player_eval


def test_moves_benchmark(benchmark: Benchmark):
    game = Game(seed=0)
    benchmark(game.all_moves, 0)


def test_state_benchmark(benchmark: Benchmark):
    game = Game(seed=0)
    benchmark(game.get_state_after_move, 0, game.all_moves(0)[0])


def test_points_benchmark(benchmark: Benchmark):
    game = Game(seed=0)
    benchmark(game.calculate_points, flag="include_bonus")


def test_negascout_benchmark(benchmark: Benchmark):
    game = Game(seed=0)
    player_eval = load_player_eval("v2")
    benchmark(negascout, player_eval, game, 0, 2, 2)


def test_evaluation_benchmark(benchmark: Benchmark):
    game = Game(seed=0)
    player_eval = load_player_eval("v2")
    benchmark(game_evaluation, game, player_eval["player_evaluation"])
