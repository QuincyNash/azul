from __future__ import annotations
from constants import *
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Union, Callable
import pygame


if TYPE_CHECKING:
    from game import Game, TileImage


@dataclass(slots=True)
class PatternLine:
    tile: Union[Tile, Literal["EMPTY"]]
    space: int

    def __bytes__(self) -> bytes:
        return BYTE_CONVERSION[self.tile] + bytes(self.space)


class Player:
    def __init__(self, index: int) -> None:
        # Index of player in Game.players list
        self.index = index

        self.points = 0
        self.has_starting_marker = False

        # Create five pattern lines in a triangle formation
        self.pattern_lines: List[PatternLine] = [
            PatternLine(tile=EMPTY, space=i + 1) for i in range(WALL_SIZE)
        ]

        # Create 5x5 wall with unfilled tiles
        self.wall = [[False for _ in range(WALL_SIZE)] for _ in range(WALL_SIZE)]

        # Tiles that are not placed in a pattern line
        self.floor: List[Union[Tile, Literal["STARTING_MARKER"]]] = []

    # Printable version of Player
    def __str__(self) -> str:
        return f"Player(points={self.points}, has_starting_marker={self.has_starting_marker}, floor_count={len(self.floor)})"

    # Return the possible positions for a tile of a given type
    def get_rendering_positions(
        self,
        tile: Union[Tile, Literal["STARTING_MARKER"]],
        type: Literal["wall", "pattern_line", "floor"],
        line_index: int = 0,
    ) -> List[pygame.math.Vector2]:
        positions: List[pygame.math.Vector2] = []

        w_transform = TILE_BORDER + SECTION_SPACING
        h_transform = PLAYER_HEIGHT if self.index == 1 else 0

        if type == "pattern_line":
            y_pos = SCORE_HEIGHT + (TILE_SIZE + TILE_SPACING) * line_index
            line = self.pattern_lines[line_index]

            for column_index in range(line_index, -1, -1):
                x_pos = (TILE_SIZE + TILE_SPACING) * (WALL_SIZE - column_index - 1)
                tile_type = (
                    line.tile
                    if line_index - column_index + 1 - line.space > 0
                    else EMPTY
                )
                if tile == tile_type:
                    positions.append(
                        pygame.math.Vector2(w_transform + x_pos, h_transform + y_pos)
                    )

        elif type == "wall" and tile != STARTING_MARKER:
            x = TILE_POSITIONS[tile][line_index]

            x_pos = (
                (TILE_SIZE + TILE_SPACING) * (WALL_SIZE + x)
                - TILE_SPACING
                + TILE_BORDER
                + SECTION_SPACING
            )
            y_pos = SCORE_HEIGHT + (TILE_SIZE + TILE_SPACING) * line_index

            positions.append(
                pygame.math.Vector2(w_transform + x_pos, h_transform + y_pos)
            )

        elif type == "floor":
            for x in range(NUM_FLOOR_TILES):
                x_pos = (TILE_SIZE + FLOOR_TILE_SPACING) * x
                y_pos = PLAYER_HEIGHT - TILE_SIZE - SECTION_SPACING
                tile_type = self.floor[x] if x < len(self.floor) else EMPTY

                if tile == tile_type:
                    positions.append(
                        pygame.math.Vector2(w_transform + x_pos, h_transform + y_pos)
                    )

        return positions

    def render(
        self,
        canvas: pygame.Surface,
        w_transform: int,
        h_transform: int,
        *,
        wins: int = -1,
        no_tiles_but_wall: bool = False,
    ) -> None:
        def draw_tile_and_border(
            x_pos: float,
            y_pos: float,
            tile: Union[ImageFileName, Literal["EMPTY"]],
            *,
            faded: bool = True,
            force_tiles: bool = False,
        ) -> None:
            pygame.draw.rect(
                canvas,
                COLOR_BROWN,
                (
                    x_pos - TILE_BORDER,
                    y_pos - TILE_BORDER,
                    TILE_SIZE + TILE_BORDER * 2,
                    TILE_SIZE + TILE_BORDER * 2,
                ),
                width=TILE_BORDER,
            )
            if tile != EMPTY and (not no_tiles_but_wall or force_tiles):
                canvas.blit(
                    IMAGES[tile].faded if faded else IMAGES[tile].normal,
                    (x_pos, y_pos),
                )

        # Floor and pattern line tiles
        types: List[Union[Tile, Literal["STARTING_MARKER"]]] = [
            *TILE_TYPES,
            STARTING_MARKER,
        ]
        for tile_type in types:
            floor_positions = self.get_rendering_positions(tile_type, "floor")

            pattern_line_positions: List[pygame.math.Vector2] = []
            for line_index in range(WALL_SIZE):
                pattern_line_positions.extend(
                    self.get_rendering_positions(tile_type, "pattern_line", line_index)
                )

            for position in floor_positions + pattern_line_positions:
                draw_tile_and_border(position.x, position.y, tile_type, faded=False)

        # Pattern Lines
        for row_index in range(len(self.pattern_lines)):
            y_pos = SCORE_HEIGHT + (TILE_SIZE + TILE_SPACING) * row_index

            for column_index in range(row_index + 1):
                x_pos = (TILE_SIZE + TILE_SPACING) * (WALL_SIZE - column_index - 1)

                draw_tile_and_border(
                    w_transform + x_pos, h_transform + y_pos, EMPTY, faded=False
                )

        # Wall
        for y in range(WALL_SIZE):
            for x in range(WALL_SIZE):
                x_pos = (
                    (TILE_SIZE + TILE_SPACING) * (WALL_SIZE + x)
                    - TILE_SPACING
                    + TILE_BORDER
                    + SECTION_SPACING
                )
                y_pos = SCORE_HEIGHT + (TILE_SIZE + TILE_SPACING) * y

                draw_tile_and_border(
                    w_transform + x_pos,
                    h_transform + y_pos,
                    WALL_TILES[y][x],
                    faded=not self.wall[y][x],
                    force_tiles=True,
                )

        # Floor
        for x in range(NUM_FLOOR_TILES):
            x_pos = (TILE_SIZE + FLOOR_TILE_SPACING) * x
            y_pos = PLAYER_HEIGHT - TILE_SIZE - SECTION_SPACING

            draw_tile_and_border(
                w_transform + x_pos, h_transform + y_pos, EMPTY, faded=False
            )

            number = NEGATIVE_FLOOR_POINTS[x] if x < len(NEGATIVE_FLOOR_POINTS) else 3

            text = FLOOR_FONT.render(f"-{number}", True, BLACK)
            text_rect = text.get_rect(
                center=(
                    w_transform + x_pos + TILE_SIZE / 2,
                    h_transform + y_pos - FLOOR_NUMBER_HEIGHT / 2,
                )
            )
            canvas.blit(text, text_rect)

        # Score
        text = MAIN_FONT.render(f"Score: {self.points}", True, BLACK)
        if wins == -1:
            text_rect = text.get_rect(
                center=(
                    PLAYER_WIDTH / 2,
                    h_transform + SCORE_HEIGHT / 2,
                )
            )
        else:
            text_rect = text.get_rect(
                midright=(
                    PLAYER_WIDTH - SECTION_SPACING,
                    h_transform + SCORE_HEIGHT / 2,
                )
            )
        canvas.blit(text, text_rect)

        # Wins
        if wins != -1:
            text = MAIN_FONT.render(f"Wins: {wins}", True, BLACK)
            text_rect = text.get_rect(
                midleft=(
                    SECTION_SPACING,
                    h_transform + SCORE_HEIGHT / 2,
                )
            )
            canvas.blit(text, text_rect)
