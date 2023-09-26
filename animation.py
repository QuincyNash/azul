from __future__ import annotations
from dataclasses import dataclass
from constants import *
from typing import TYPE_CHECKING, Union, Literal
import pygame


if TYPE_CHECKING:
    from graphics import GraphicsInfo
    from game import Game, Move


# Stores the data about a tile that is being animated
@dataclass
class AnimatingTile:
    tile: Union[Tile, Literal[6]]
    position: pygame.math.Vector2
    new_position: pygame.math.Vector2

    def __post_init__(self) -> None:
        self.movement = (self.new_position - self.position) / (
            ANIMATION_SECONDS * FRAME_RATE
        )


class Animation:
    def __init__(
        self,
        player_index: int,
        old_game: Game,
        move: Union[Move, None],
        new_game: Game,
        graphics_info: GraphicsInfo,
    ) -> None:
        # Unpack graphics variables
        if graphics_info:
            (
                self.canvas,
                self.clock,
                self.floor_font,
                self.main_font,
                self.images,
            ) = graphics_info

        self.old_game = old_game
        self.move = move
        self.player_index = player_index
        self.new_game = new_game

        self.frame_count = 0
        self.finished = False

        self.tiles: List[AnimatingTile] = []

        # Move tiles from pattern lines to wall
        if not move:
            for player_index in [0, 1]:
                for line_index in range(WALL_SIZE):
                    line = self.old_game.players[player_index].pattern_lines[line_index]

                    if line.space == 0 and line.tile != EMPTY:
                        old_position = old_game.get_rendering_positions(
                            line.tile,
                            player_index=player_index,
                            player_type="pattern_line",
                            line_index=line_index,
                        )[-1]
                        new_position = new_game.get_rendering_positions(
                            line.tile,
                            player_index=player_index,
                            player_type="wall",
                            line_index=line_index,
                        )[0]
                        self.tiles.append(
                            AnimatingTile(line.tile, old_position, new_position)
                        )

        else:
            if len(move.floor_tiles) > 0:
                for tile in TILE_TYPES:
                    if move.is_center_draw:
                        positions = old_game.get_rendering_positions(
                            tile, center_pile=True
                        )
                    else:
                        positions = old_game.get_rendering_positions(
                            tile, factory_index=move.factory_index
                        )

                    new_positions = new_game.get_rendering_positions(
                        tile, player_index=move.player_index, player_type="floor"
                    )

                    # Exclude tiles that already existed on the floor
                    num_old_tiles = old_game.players[move.player_index].floor.count(
                        tile
                    )
                    new_positions = new_positions[num_old_tiles:]

                    # Make sure that these are new positions, because positions list has tiles that aren't going on the floor
                    for index in range(len(new_positions)):
                        self.tiles.append(
                            AnimatingTile(tile, positions[index], new_positions[index])
                        )

            if move.first_draw_from_center:
                # Animate starting marker
                position = old_game.get_rendering_positions(
                    STARTING_MARKER, center_pile=True
                )[0]
                new_position = new_game.get_rendering_positions(
                    STARTING_MARKER, player_index=move.player_index, player_type="floor"
                )[0]
                self.tiles.append(
                    AnimatingTile(STARTING_MARKER, position, new_position)
                )

                # Animate tiles that were already on the floor
                for tile in TILE_TYPES:
                    positions = old_game.get_rendering_positions(
                        tile, player_index=move.player_index, player_type="floor"
                    )
                    new_positions = new_game.get_rendering_positions(
                        tile, player_index=move.player_index, player_type="floor"
                    )

                    for index in range(len(positions)):
                        self.tiles.append(
                            AnimatingTile(tile, positions[index], new_positions[index])
                        )

            # Animate the drawn tiles to pattern lines
            if move.is_center_draw:
                positions = old_game.get_rendering_positions(
                    move.drawing, center_pile=True
                )
            else:
                positions = old_game.get_rendering_positions(
                    move.drawing, factory_index=move.factory_index
                )
            new_positions = new_game.get_rendering_positions(
                move.drawing,
                player_index=move.player_index,
                player_type="pattern_line",
                line_index=move.pattern_line,
            )
            for index in range(len(positions) - len(move.floor_tiles)):
                self.tiles.append(
                    AnimatingTile(
                        move.drawing,
                        positions[index + len(move.floor_tiles)],
                        new_positions[index],
                    )
                )

            # Move tiles from the factory to the center pile
            if not move.is_center_draw:
                for tile in TILE_TYPES:
                    if tile != move.drawing:
                        positions = old_game.get_rendering_positions(
                            tile, factory_index=move.factory_index
                        )
                        new_positions = new_game.get_rendering_positions(
                            tile, center_pile=True
                        )
                        num_old_tiles = old_game.center_pile[tile]
                        new_positions = new_positions[num_old_tiles:]

                        for index in range(len(positions)):
                            self.tiles.append(
                                AnimatingTile(
                                    tile,
                                    positions[index],
                                    new_positions[index],
                                )
                            )

            # Animate center pile shuffling
            for tile in TILE_TYPES:
                positions = old_game.get_rendering_positions(tile, center_pile=True)
                new_positions = new_game.get_rendering_positions(tile, center_pile=True)

                max_index = min(len(positions), len(new_positions))

                for index in range(max_index):
                    self.tiles.append(
                        AnimatingTile(
                            tile,
                            positions[index],
                            new_positions[index],
                        )
                    )

        self.render_all_other_tiles()

    # Renders any tiles that aren't moving
    def render_all_other_tiles(
        self,
    ):
        types: List[Union[Tile, Literal[6]]] = [
            STARTING_MARKER,
            *TILE_TYPES,
        ]
        taken_positions = [tile.position for tile in self.tiles]

        for tile in types:
            positions: List[pygame.math.Vector2] = []

            positions.extend(
                self.old_game.get_rendering_positions(tile, center_pile=True)
            )

            for factory_index in range(FACTORY_COUNT):
                positions.extend(
                    self.old_game.get_rendering_positions(
                        tile,
                        factory_index=factory_index,
                    )
                )

            for player_index in [0, 1]:
                positions.extend(
                    self.old_game.get_rendering_positions(
                        tile, player_index=player_index, player_type="floor"
                    )
                )

                for line_index in range(WALL_SIZE):
                    positions.extend(
                        self.old_game.get_rendering_positions(
                            tile,
                            player_index=player_index,
                            player_type="pattern_line",
                            line_index=line_index,
                        )
                    )

            for position in positions:
                if position not in taken_positions:
                    self.tiles.append(AnimatingTile(tile, position, position))

    # Updates the animation details of all tiles
    def update(self) -> None:
        if self.frame_count == ANIMATION_SECONDS * FRAME_RATE:
            self.finished = True
        else:
            for tile in self.tiles:
                tile.position += tile.movement

            self.frame_count += 1

    def render(self):
        for tile in self.tiles:
            self.canvas.blit(
                self.images[tile.tile].normal,
                (tile.position.x, tile.position.y),
            )
