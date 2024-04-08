from __future__ import annotations
from constants import *
from dataclasses import dataclass
from typing import List, Union
from utils import Vector


@dataclass(slots=True)
class PatternLine:
    tile: Union[Tile, Literal[0]]
    space: int

    def __bytes__(self) -> bytes:
        return BYTE_CONVERSION[self.tile] + bytes(self.space)


@dataclass(slots=True)
class PlayerBonuses:
    row: List[bool]
    col: List[bool]
    diagonal: List[bool]


class Player:
    def __init__(self, index: int) -> None:
        # Index of player in Game.players list
        self.index = index

        self.points = 0
        self.has_starting_marker = False

        # Value of -1 represents the floor line
        self.hovered_pattern_line: Union[int, None] = None

        # Create five pattern lines in a triangle formation
        self.pattern_lines: List[PatternLine] = [
            PatternLine(tile=EMPTY, space=i + 1) for i in range(WALL_SIZE)
        ]

        # Create 5x5 wall with unfilled tiles
        self.wall = [[False for _ in range(WALL_SIZE)] for _ in range(WALL_SIZE)]

        # Tiles that are not placed in a pattern line
        self.floor: List[Union[Tile, Literal[6]]] = []

        # Keeps track of completed bonuses so they aren't double counted
        self.bonuses: PlayerBonuses = PlayerBonuses(
            [False for _ in range(WALL_SIZE)],
            [False for _ in range(WALL_SIZE)],
            [False for _ in range(WALL_SIZE)],
        )

    # Printable version of Player
    def __str__(self) -> str:
        return f"Player(points={self.points}, has_starting_marker={self.has_starting_marker}, floor_count={len(self.floor)})"

    # Return the possible positions for a tile of a given type
    def get_rendering_positions(
        self,
        tile: Union[Tile, Literal[6]],
        type: Literal["wall", "pattern_line", "floor"],
        line_index: int = 0,
    ) -> List[Vector]:
        positions: List[Vector] = []

        w_transform = 1 + SECTION_SPACING
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
                    positions.append(Vector(w_transform + x_pos, h_transform + y_pos))

        elif type == "wall" and tile != STARTING_MARKER:
            x = TILE_POSITIONS[tile][line_index]

            x_pos = (
                (TILE_SIZE + TILE_SPACING) * (WALL_SIZE + x)
                - TILE_SPACING
                + 1
                + SECTION_SPACING
            )
            y_pos = SCORE_HEIGHT + (TILE_SIZE + TILE_SPACING) * line_index

            positions.append(Vector(w_transform + x_pos, h_transform + y_pos))

        elif type == "floor":
            for x in range(NUM_FLOOR_TILES):
                x_pos = (TILE_SIZE + FLOOR_TILE_SPACING) * x
                y_pos = PLAYER_HEIGHT - TILE_SIZE - SECTION_SPACING
                tile_type = self.floor[x] if x < len(self.floor) else EMPTY

                if tile == tile_type:
                    positions.append(Vector(w_transform + x_pos, h_transform + y_pos))

        return positions
