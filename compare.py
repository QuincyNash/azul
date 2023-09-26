from constants import *
from typing import TypedDict
from evaluation import load_player_eval
from game import Game
from search import get_best_move
import multiprocessing
import random
import json
from tqdm import tqdm


class Score(TypedDict):
    player1_wins: int
    player2_wins: int
    ties: int


player1_eval = load_player_eval(f"v{PLAYER1_COMPARE_VERSION}")
player2_eval = load_player_eval(f"v{PLAYER2_COMPARE_VERSION}")


# Return of 0 represents draw, 1 represents player 1 win, 2 represents player 2 win
def play_game(move_time: float) -> int:
    turn = random.randint(0, 1)
    game = Game(graphics_info=None)

    while not game.is_game_over():
        if game.is_round_over():
            game.calculate_points_and_modify()
            turn = game.new_round()

        else:
            result = get_best_move(
                player1_eval,
                player2_eval,
                game,
                turn,
                move_time,
                show_progress=False,
            )
            game.make_move(turn, result.move)
            turn = (turn + 1) % 2

    game.calculate_points_and_modify(flag="bonus_only")

    score_difference = game.players[0].points - game.players[1].points
    if score_difference > 0:
        return 1
    elif score_difference < 0:
        return 2
    else:
        return 0


if __name__ == "__main__":
    player1_wins = 0
    player2_wins = 0
    ties = 0

    # Play NUM_COMPARE_ROUNDS games in parallel and record the results
    with multiprocessing.Pool() as pool:
        for result in tqdm(
            pool.imap_unordered(
                play_game, [COMPARE_COMPUTER_MOVE_TIME] * NUM_COMPARE_ROUNDS
            ),
            total=NUM_COMPARE_ROUNDS,
        ):
            if result == 0:
                ties += 1
            elif result == 1:
                player1_wins += 1
            elif result == 2:
                player2_wins += 1

    file = open("compare.json", "r+", encoding="utf-8")

    # Information stored as a dictionary of different combinations of versions eg. (v1,v2)
    current_text: Dict[str, Score] = json.load(file)

    smaller_version_number = min(PLAYER1_COMPARE_VERSION, PLAYER2_COMPARE_VERSION)
    larger_version_number = max(PLAYER1_COMPARE_VERSION, PLAYER2_COMPARE_VERSION)
    version_combination = f"v{smaller_version_number},v{larger_version_number}"

    # Add the new information to the dictionary
    if version_combination not in current_text:
        current_text[version_combination] = {
            "player1_wins": player1_wins,
            "player2_wins": player2_wins,
            "ties": ties,
        }
    else:
        current_text[version_combination]["player1_wins"] += player1_wins
        current_text[version_combination]["player2_wins"] += player2_wins
        current_text[version_combination]["ties"] += ties

    # Overwrite the existing file
    file.seek(0)
    json.dump(current_text, file, ensure_ascii=False, indent=4)
    file.truncate()

    print(
        f"Player 1 Wins: {player1_wins}",
        f"Player 2 Wins: {player2_wins}",
        f"Ties: {ties}",
        sep="\n",
    )
