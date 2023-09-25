from constants import *
from typing import Union
from evaluation import EvaluationVersion, load_player_eval
from game import Game
from animation import Animation
from player import Player
from search import get_best_move, SearchedNode
from tqdm import tqdm
from importlib import import_module


# start = time.perf_counter()
# for i in range(10000):
#     game.all_moves(0)
# print(time.perf_counter() - start)

player1_eval = load_player_eval(PLAYER1_COMPARE_VERSION)
player2_eval = load_player_eval(PLAYER2_COMPARE_VERSION)

game = Game()

pygame.event.set_allowed([pygame.QUIT])
pygame.display.set_caption("Azul")

quit = False
end = False
turn = 0
game_round = 1
player1_wins = 0
player2_wins = 0
ties = 0

game.render(player1_wins=0, player2_wins=0, ties=0)
pygame.display.update()

while not quit:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit = True

    if not end:
        if game.is_round_over():
            game.calculate_points_and_modify()

            # Restart game if finished
            if game.is_game_over():
                game.calculate_points_and_modify(flag="bonus_only")

                score_difference = game.players[0].points - game.players[1].points
                if score_difference > 0:
                    player1_wins += 1
                elif score_difference < 0:
                    player2_wins += 1
                else:
                    ties += 1

                if game_round >= NUM_COMPARE_ROUNDS:
                    end = True
                else:
                    game = Game()
                    turn = 0
                    game_round += 1

                print(player1_wins, player2_wins, ties)

            # Restart round if finished
            else:
                # Assign turn to whoever drew the starting marker
                turn = game.new_round()

        else:
            result = get_best_move(
                player1_eval, player2_eval, game, turn, COMPARE_COMPUTER_MOVE_TIME
            )

            # print(result.score, result.nodes_searched)

            game.make_move(turn, result.move)
            turn = (turn + 1) % 2

        game.render(player1_wins=player1_wins, player2_wins=player2_wins, ties=ties)
        pygame.display.update()

        clock.tick(FRAME_RATE)
