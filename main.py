from constants import *
from typing import Union
from evaluation import load_player_eval
from game import Game
from animation import Animation
from search import get_best_move
import time


if __name__ == "__main__":
    # start = time.perf_counter()
    # for i in range(10000):
    #     game.all_moves(0)
    # print(time.perf_counter() - start)

    game = Game(seed=10)

    pygame.event.set_allowed([pygame.QUIT])
    pygame.display.set_caption("Azul")

    quit = False
    end = False
    animation: Union[Animation, None] = None
    new_game = game.copy()
    serialized_game = game.serialize()
    turn = 0
    player1_wins = 0
    player2_wins = 0

    eval_version = load_player_eval(EVALUATION_VERSION)

    game.render()
    pygame.display.update()

    while not quit:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit = True

        if not end and animation:
            if animation.finished:
                animation = None

                # If the animation is over and the round is over, start a new round
                if game.is_round_over():
                    game = new_game.copy()

                    # If the game is over, calcuolate the final score and end the game
                    if game.is_game_over():
                        game.calculate_points_and_modify(flag="bonus_only")
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

        elif not end:
            # Start the wall tiling animation
            if game.is_round_over():
                new_game = game.copy()
                new_game.calculate_points_and_modify()

                animation = Animation(turn, game, None, new_game)

                game.render()
                pygame.display.update()

            # Start the move animation
            else:
                result = get_best_move(
                    eval_version, eval_version, game, turn, COMPUTER_MOVE_TIME
                )

                print(result.score, result.nodes_searched, result.transposition_lookups)

                game.make_move(turn, result.move)
                new_game = game.copy()
                game.undo_move(turn, result.move)

                animation = Animation(turn, game, result.move, new_game)
                turn = (turn + 1) % 2

            game.render()
            pygame.display.update()

        clock.tick(FRAME_RATE)
