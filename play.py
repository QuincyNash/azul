import time
from constants import *
from typing import Union
from evaluation import load_player_eval
from game import Game
from animation import Animation
import graphics
from search import FinalResult, get_best_move, ConnectionData
from multiprocessing import Process, Pipe
import pygame
import json


if __name__ == "__main__":
    eval_version = load_player_eval(EVALUATION_VERSION)
    graphics_info = graphics.init()

    game = Game(graphics_info)
    game.from_json(json.load(open("game_state.json")))

    pygame.event.set_allowed([pygame.QUIT])
    pygame.display.set_caption("Azul")

    turn = 1
    choice = None
    new_game = game.copy()
    quit = False
    end = None
    partial = None
    animation = None
    child_connection = None
    parent_connection = None
    process = None

    game.render(player_choice=choice, partial_tile_move=partial)
    pygame.display.update()

    while not quit:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit = True

            if event.type == pygame.MOUSEBUTTONUP and turn == 0:
                if choice == "tile":
                    partial_move = game.get_hovered_partial_move()
                    if partial_move:
                        choice = "line"
                        partial = partial_move

                elif choice == "line" and partial:
                    move = game.get_hovered_move(partial)
                    if move:
                        game.make_move(turn, move)
                        new_game = game.copy()
                        game.undo_move(turn, move)

                        animation = Animation(turn, game, move, new_game, graphics_info)

                        choice, partial = None, None
                        turn = (turn + 1) % 2

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
                        if turn == 0:
                            choice = "tile"

                # If the animation is over, set the new game state for the next move
                else:
                    game = new_game.copy()
                    if turn == 0:
                        choice = "tile"

                game.render(player_choice=choice, partial_tile_move=partial)
                pygame.display.update()
            else:
                game.render(no_tiles_but_wall=True)
                animation.render()
                pygame.display.update()

                animation.update()

        elif not end:
            if game.is_round_over():
                new_game = game.copy()
                new_game.calculate_points_and_modify()

                animation = Animation(turn, game, None, new_game, graphics_info)

                game.render(player_choice=choice, partial_tile_move=partial)
                pygame.display.update()
            elif turn == 1 and not process:
                parent_connection, child_connection = Pipe()

                process = Process(
                    target=get_best_move,
                    args=(eval_version, eval_version, game, 1, COMPUTER_MOVE_TIME),
                    kwargs={"connection": child_connection},
                    daemon=True,
                )
                time.sleep(0.1)
                process.start()

            game.render(player_choice=choice, partial_tile_move=partial)
            pygame.display.update()

        if parent_connection and parent_connection.poll():
            result: ConnectionData = parent_connection.recv()

            if result["type"] == BEST_MOVE:
                data: FinalResult = result["data"]
                # print("\n", type(data.move), turn)

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

            # if result["type"] == DEPTH:
            #     print("DEPTH:", result["data"])

            # if result["type"] == EVALUATION:
            #     print("CURRENT BEST:", result["data"])

        graphics_info.clock.tick(FRAME_RATE)
