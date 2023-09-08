from constants import *
from typing import Union
from evaluation import load_player_eval
from game import Game
from animation import Animation
from player import Player
from search import get_best_move, SearchedNode
from tqdm import tqdm
import pickle
import time


if __name__ == "__main__":
    # start = time.time()
    # for i in range(10000):
    #     game.all_moves(0)
    # print(time.time() - start)

    game = Game(seed=0)

    pygame.event.set_allowed([pygame.QUIT])
    pygame.display.set_caption("Azul")

    quit = False
    end = False
    new_game = game.copy()
    animation: Union[Animation, None] = None
    turn = 0
    player1_wins = 0
    player2_wins = 0

    eval_version = load_player_eval(PLAYER1_COMPARE_VERSION)

    game.render()
    pygame.display.update()

    while not quit:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit = True

        if end:
            score_difference = game.players[0].points - game.players[1].points
            if score_difference > 0:
                player1_wins += 1
            elif score_difference < 0:
                player2_wins += 1

            game = Game()
            end = False
            turn = 0
            animation = None

        if animation:
            if animation.finished:
                animation = None

                # If the animation is over and the round is over, start a new round
                if game.is_round_over():
                    game = new_game.copy()

                    # If the game is over, calcuolate the final score and end the game
                    if game.is_game_over():
                        game.calculate_points(flag="bonus_only")
                        end = True
                    else:
                        turn = game.new_round()

                # If the animation is over, set the new game state for the next move
                else:
                    game = new_game.copy()

                game.render()
                pygame.display.update()
                time.sleep(PAUSE_TIME_AFTER_MOVE)

            # Update and render animation
            else:
                game.render(no_tiles_but_wall=True)
                animation.render()
                pygame.display.update()

                animation.update()

        else:
            # Start the wall tiling animation
            if not end and game.is_round_over():
                new_game = game.copy()
                new_game.calculate_points()

                animation = Animation(turn, game, None, new_game)

                game.render()
                pygame.display.update()

            # Start the move animation
            elif not end:
                result = get_best_move(
                    eval_version, eval_version, game, turn, COMPUTER_MOVE_TIME
                )

                # print(result.score, result.nodes_searched)

                new_game = game.get_state_after_move(turn, result.move)
                animation = Animation(turn, game, result.move, new_game)
                turn = (turn + 1) % 2

            game.render()
            pygame.display.update()

        clock.tick(FRAME_RATE)
