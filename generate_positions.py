import multiprocessing
from typing import List, Tuple
from evaluation import load_player_eval
from game import Game
from search import get_best_move
import random
from tqdm import tqdm


def play(_: None):
    data_points: List[Tuple[str, float]] = []

    v3_eval = load_player_eval("v3")
    v4_eval = load_player_eval("v4")

    turn = random.randint(0, 1)
    game = Game()

    while not game.is_game_over():
        if game.is_round_over():
            game.calculate_points_and_modify()
            turn = game.new_round()

        else:
            if turn == 0:
                time = 1
            else:
                time = 0.1

            result = get_best_move(
                v4_eval,
                v3_eval,
                game,
                turn,
                time,
                show_progress=False,
            )

            game.make_move(turn, result.move)

            if turn == 0:
                data_point = (game.serialize(game.calculate_points()), result.score)
                data_points.append(data_point)

                # print(data_point[1])

            turn = (turn + 1) % 2

    return data_points


def write_data_points(data_points: List[Tuple[str, float]]):
    file = open("data_points.txt", "w")
    file.writelines(
        [f"{data_point[0]} {data_point[1]}\n" for data_point in data_points]
    )
    file.close()


if __name__ == "__main__":
    num_games = 1000

    data_points: List[Tuple[str, float]] = []

    try:
        with multiprocessing.Pool() as pool:
            progress_bar = tqdm(
                pool.imap(
                    play,
                    [None] * num_games,
                ),
                total=num_games,
                postfix={"Data points": len(data_points)},
            )

            for result in progress_bar:
                data_points.extend(result)

                progress_bar.set_postfix({"Data points": len(data_points)})

        print(f"SAVING {len(data_points)} DATA POINTS", data_points)
        write_data_points(data_points)

    except Exception as error:
        print(error)

        print(f"SAVING {len(data_points)} DATA POINTS")
        write_data_points(data_points)
