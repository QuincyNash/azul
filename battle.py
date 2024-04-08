from constants import *
from typing import Union
from evaluation import load_player_eval
from game import Game
from animation import Animation
import graphics
from search import ConnectionData, FinalResult, get_best_move
from multiprocessing import Process, Pipe
import pygame
import json
import time


if __name__ == "__main__":
    graphics_info = graphics.init()
    game = Game()
    game.from_json(json.load(open("game_state.json", "r")))

    pygame.event.set_allowed([pygame.QUIT])
    pygame.display.set_caption("Azul")

    quit = False
    end = False
    animation: Union[Animation, None] = None
    new_game = game.copy()
    serialized_game = game.serialize()
    process = None
    child_connection = None
    parent_connection = None
    turn = 0
    player1_wins = 0
    player2_wins = 0

    eval_version = load_player_eval(EVALUATION_VERSION)
    graphics.render_game(game, graphics_info)
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
                        end = True
                    else:
                        turn = game.new_round()

                # If the animation is over, set the new game state for the next move
                else:
                    game = new_game.copy()

                graphics.render_game(game, graphics_info)
                pygame.display.update()
                time.sleep(PAUSE_TIME_AFTER_MOVE)

            # Update and render animation
            else:
                graphics.render_game(game, graphics_info, no_tiles_but_wall=True)
                animation.render()
                pygame.display.update()

                animation.update()

        elif not end:
            # Start the wall tiling animation
            if game.is_round_over():
                new_game = game.copy()
                new_game.calculate_points_and_modify()

                animation = Animation(turn, game, None, new_game, graphics_info)

                graphics.render_game(game, graphics_info)
                pygame.display.update()

            # Start the move animation
            elif not process:
                parent_connection, child_connection = Pipe()

                process = Process(
                    target=get_best_move,
                    args=(eval_version, eval_version, game, turn, COMPUTER_MOVE_TIME),
                    kwargs={"connection": child_connection},
                    daemon=True,
                )
                process.start()

        if parent_connection and parent_connection.poll():
            result: ConnectionData = parent_connection.recv()

            if result["type"] == BEST_MOVE:
                data: FinalResult = result["data"]

                game.make_move(turn, data.move)
                new_game = game.copy()
                game.undo_move(turn, data.move)

                animation = Animation(turn, game, data.move, new_game, graphics_info)
                if process and parent_connection and child_connection:
                    process.kill()
                    parent_connection.close()
                    child_connection.close()
                    process, child_connection, parent_connection = None, None, None

                turn = (turn + 1) % 2

            graphics.render_game(game, graphics_info)
            pygame.display.update()

        graphics_info.clock.tick(FRAME_RATE)
