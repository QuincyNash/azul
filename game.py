from __future__ import annotations
import struct
from typing import Callable, List, Tuple
from constants import *
from dataclasses import dataclass
from collections import Counter
import random
import math
import pickle
import pygame
from pygame import gfxdraw
from player import PatternLine, Player


move_counter = 0
serialize_counter = 0
points_counter = 0
make_move_counter = 0
no_move_counter = 0
Factory = Counter[Union[Tile, Literal["STARTING_MARKER"]]]


@dataclass(slots=True)
class Move:
    drawing: Tile
    amount: int
    moving_to_center: Factory
    player_index: int  # Index of player in Game.players list
    factory_index: int  # Index of factory in Game.factories list
    pattern_line: int
    floor_tiles: List[Tile]
    is_center_draw: bool
    first_draw_from_center: bool


@dataclass(slots=True)
class PointChange:
    pattern_line: int
    tile: Tile
    points: int


@dataclass(slots=True)
class PointsResult:
    point_changes: List[PointChange]
    bonus_points: int
    negative_floor_points: int


class Game:
    def __init__(self, *, seed=None) -> None:
        if seed is not None:
            random.seed(seed)

        # Counters are used for factories to store the number of occurences of each tile
        # Create factories and populate each with 4 random tiles
        self.factories: List[Factory] = [Counter() for _ in range(FACTORY_COUNT)]

        # Center pile starts empty (flagged for identification later)
        self.center_pile: Factory = Counter()
        self.center_pile[STARTING_MARKER] = 1

        self.players = [Player(index=0), Player(index=1)]

        self.new_round()

    def copy(self) -> Game:
        return pickle.loads(pickle.dumps(self, -1))

    def random_tile(self) -> Tile:
        return random.choice(TILE_TYPES)

    def get_factory_number(self, factory: Factory):
        return struct.pack(
            "!Q",
            (
                factory[RED]
                + factory[BLUE] * 8
                + factory[YELLOW] * 64
                + factory[BLACK] * 512
                + factory[STAR] * 4096
            ),
        )

    def serialize(self) -> bytes:
        result: bytes = b""

        factory_numbers = list(map(self.get_factory_number, self.factories))
        factory_numbers.sort()
        factory_numbers.append(self.get_factory_number(self.center_pile))
        result += b"".join(factory_numbers)

        for player in self.players:
            result += bytes(player.has_starting_marker)
            result += bytes(len(player.floor))
            result += bytes(player.points)
            result += b"".join(map(bytes, player.pattern_lines))
            result += b"".join(map(bytes, player.wall))

        return result

    # Round is over if factories and center pile are empty
    def is_round_over(self) -> bool:
        empty: Factory = Counter()

        for factory in [*self.factories, self.center_pile]:
            if factory != empty:
                return False

        return True

    # Game is over if any player has a full horizontal row in their wall
    def is_game_over(self) -> bool:
        for player in self.players:
            if any(all(row) for row in player.wall):
                return True

        return False

    # Reset all factories and the starting marker
    def new_round(self) -> int:
        for factory in self.factories:
            tiles = [self.random_tile() for _ in range(TILES_PER_FACTORY)]
            for tile in TILE_TYPES:
                factory[tile] = tiles.count(tile)

        self.center_pile[STARTING_MARKER] = 1

        first_player = 0 if self.players[0].has_starting_marker else 1

        self.players[0].has_starting_marker = False
        self.players[1].has_starting_marker = False

        return first_player

    def make_move(self, player_index: int, move: Move) -> None:
        player: Player = self.players[player_index]
        line = player.pattern_lines[move.pattern_line]

        # Add tiles to pattern line
        if move.amount != 0:
            line.tile = move.drawing
            line.space -= move.amount

        # Add tiles to floor. If the move is the first draw from the center, add 1 extra
        if move.first_draw_from_center:
            player.floor.insert(0, STARTING_MARKER)
            player.has_starting_marker = True
            self.center_pile[STARTING_MARKER] = 0

        player.floor.extend(move.floor_tiles)

        if move.is_center_draw:
            # Remove tiles from center
            self.center_pile[move.drawing] = 0
        else:
            # Move tiles to center
            self.center_pile.update(move.moving_to_center)
            # Remove tiles from factory
            self.factories[move.factory_index] = Counter()

    def undo_move(self, player_index: int, move: Move) -> None:
        player = self.players[player_index]
        factory = self.factories[move.factory_index]
        line = player.pattern_lines[move.pattern_line]
        line_length = move.pattern_line + 1

        # Remove tiles from pattern line
        if move.amount != 0:
            line.tile = (
                EMPTY if line_length - line.space == move.amount else move.drawing
            )
            line.space += move.amount

        # If the move is the first draw from the center, move the starting marker back to the center pile
        if move.first_draw_from_center:
            player.floor.pop(0)
            player.has_starting_marker = False
            self.center_pile[STARTING_MARKER] = 1

        if len(move.floor_tiles) > 0:
            # Add tiles back to factory
            if move.is_center_draw:
                self.center_pile[move.floor_tiles[0]] += len(move.floor_tiles)
            else:
                factory[move.floor_tiles[0]] += len(move.floor_tiles)

            # Remove tiles from floor
            player.floor = player.floor[: -len(move.floor_tiles)]

        if move.is_center_draw:
            # Add tiles back to center
            self.center_pile[move.drawing] += move.amount
        else:
            # Remove tiles from center
            self.center_pile.subtract(move.moving_to_center)
            # Add tiles back to factory
            factory[move.drawing] += move.amount
            factory.update(move.moving_to_center)

    def calculate_points_and_modify(
        self, *, flag: Literal["bonus_only", "include_bonus", "normal"] = "normal"
    ) -> None:
        self.calculate_points(flag=flag, modify_game=True)

    def calculate_points(
        self,
        *,
        flag: Literal["bonus_only", "include_bonus", "normal"] = "normal",
        modify_game=False,
    ) -> List[PointsResult]:
        results: List[PointsResult] = []

        for player in self.players:
            total_positive_points = 0
            bonus_points = 0
            floor_negative_points = 0
            point_changes: List[PointChange] = []

            # For every line, if it is full, move a tile to the wall
            wall, pattern_lines = player.wall, player.pattern_lines

            # Bonus only does not move tiles from pattern lines to the wall
            if flag != "bonus_only":
                for row_index, line in enumerate(pattern_lines):
                    if line.space == 0 and line.tile != EMPTY:
                        column_index = TILE_POSITIONS[line.tile][row_index]

                        # Add tile to wall
                        # Even if not modified, if modified, remove later
                        wall[row_index][column_index] = True

                        if modify_game:
                            # Remove tiles from pattern line
                            pattern_lines[row_index].space = row_index + 1
                            pattern_lines[row_index].tile = EMPTY

                        tile_points = 0

                        # Count the points by the number of adjacent tiles in each direction
                        for xdir, ydir in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            # Continue counting while tiles are filled
                            xpos, ypos = column_index + xdir, row_index + ydir
                            while (
                                0 <= xpos < WALL_SIZE
                                and 0 <= ypos < WALL_SIZE
                                and wall[ypos][xpos]
                            ):
                                if modify_game:
                                    player.points += 1
                                tile_points += 1
                                total_positive_points += 1

                                xpos += xdir
                                ypos += ydir

                        total_positive_points += 1

                        if modify_game:
                            # Make sure to count the tile that was placed
                            player.points += 1
                        else:
                            point_changes.append(
                                # Make sure to count the tile that was placed (+1)
                                PointChange(row_index, line.tile, tile_points + 1)
                            )

            # Calculate bonus points
            if flag in ["include_bonus", "bonus_only"]:
                for row in player.wall:
                    if all(row):
                        bonus_points += HORIZONTAL_LINE_BONUS

                for column in zip(*player.wall):
                    if all(column):
                        bonus_points += VERTICAL_LINE_BONUS

                for tile in TILE_TYPES:
                    if all(
                        player.wall[row][TILE_POSITIONS[tile][row]]
                        for row in range(WALL_SIZE)
                    ):
                        bonus_points += FIVE_OF_A_KIND_BONUS

                total_positive_points += bonus_points

                if modify_game:
                    player.points += bonus_points

            # Reset wall tiles
            for point_change in point_changes:
                wall[point_change.pattern_line][
                    TILE_POSITIONS[point_change.tile][point_change.pattern_line]
                ] = False

            if flag != "bonus_only":
                # Make sure to subtract the floor points
                # Leftover floor points count as -3
                leftover = max(len(player.floor) - len(NEGATIVE_FLOOR_POINTS), 0)
                floor_negative_points += sum(NEGATIVE_FLOOR_POINTS[: len(player.floor)])
                floor_negative_points += 3 * leftover

                # Points can't go below 0
                floor_negative_points = min(
                    floor_negative_points, total_positive_points
                )

                if modify_game:
                    player.points -= floor_negative_points
                    # And remove the floor tiles
                    player.floor = []

            results.append(
                PointsResult(point_changes, bonus_points, floor_negative_points)
            )

        return results

    def are_no_moves(self) -> bool:
        return (
            all(factory == Counter() for factory in self.factories)
            and self.center_pile == Counter()
        )

    def all_moves(self, player_index: int) -> List[Move]:
        moves: List[Move] = []
        player = self.players[player_index]

        # Consider all colors that exist on all factories including the center pile
        for index, factory in enumerate((self.center_pile, *self.factories)):
            for tile in TILE_TYPES:
                if factory[tile] != 0:
                    # Factory_copy contains every tile but the ones drawn
                    if index == 0:
                        factory_copy: Factory = Counter()
                        # If neither player has the starting marker, give it to the player who just moved
                        first_draw_from_center = (
                            not self.players[0].has_starting_marker
                            and not self.players[1].has_starting_marker
                        )
                    else:
                        factory_copy = factory.copy()
                        factory_copy[tile] = 0
                        first_draw_from_center = False

                    # Consider placing all tiles on floor
                    moves.append(
                        Move(
                            drawing=tile,
                            amount=0,
                            moving_to_center=factory_copy,
                            pattern_line=0,
                            floor_tiles=[tile] * factory[tile],
                            player_index=player_index,
                            factory_index=index - 1,
                            is_center_draw=index == 0,
                            first_draw_from_center=first_draw_from_center,
                        )
                    )

                    # Consider all possible pattern lines
                    for pattern_line in range(WALL_SIZE):
                        # Pattern line is valid if it empty or the placed tile is the same color as the other tiles. Wall also cannot contain a same-colored tile
                        line = player.pattern_lines[pattern_line]
                        wall_column = TILE_POSITIONS[tile][pattern_line]

                        if (
                            (line.tile == tile or line.tile == EMPTY)
                            and line.space > 0
                            and not player.wall[pattern_line][wall_column]
                        ):
                            # Make sure that only tiles that exist and can fit are added
                            adding_to_line = min(line.space, factory[tile])

                            moves.append(
                                Move(
                                    drawing=tile,
                                    amount=adding_to_line,
                                    moving_to_center=factory_copy,
                                    pattern_line=pattern_line,
                                    # All extras go on floor
                                    floor_tiles=[tile]
                                    * (factory[tile] - adding_to_line),
                                    factory_index=index - 1,
                                    player_index=player_index,
                                    is_center_draw=index == 0,
                                    first_draw_from_center=first_draw_from_center,
                                )
                            )

        return moves

    # Rendering location of factories
    def factory_position(self, index: int) -> pygame.math.Vector2:
        radius = CENTER_SIZE // 2 - FACTORY_RADIUS - CENTER_BORDER

        angle = 360 / FACTORY_COUNT * index - 90
        x_pos = int(radius * math.cos(math.radians(angle)))
        y_pos = int(radius * math.sin(math.radians(angle)))

        return pygame.math.Vector2(
            PLAYER_WIDTH + CENTER_SIZE // 2 + x_pos, CENTER_SIZE // 2 + y_pos
        )

    # Used for piece animation
    def get_rendering_positions(
        self,
        tile: Union[Tile, Literal["STARTING_MARKER"]],
        *,
        center_pile: bool = False,
        factory_index: int = -1,
        player_index: int = 0,
        line_index: int = 0,
        player_type: Literal["wall", "pattern_line", "floor"] = "wall",
    ) -> List[pygame.math.Vector2]:
        positions: List[pygame.math.Vector2] = []

        if factory_index != -1:
            factory_tiles: List[Tile] = []
            for tile_type in TILE_TYPES:
                factory_tiles.extend(
                    [tile_type for _ in range(self.factories[factory_index][tile_type])]
                )

            transform = self.factory_position(factory_index)

            offsets = [[-1, -1], [1, -1], [-1, 1], [1, 1]]
            for index, factory_tile in enumerate(factory_tiles):
                if factory_tile == tile:
                    x_off, y_off = offsets[index]
                    x_pos = (x_off - 1) * (TILE_SIZE // 2) + x_off * TILE_SPACING // 2
                    y_pos = (y_off - 1) * (TILE_SIZE // 2) + y_off * TILE_SPACING // 2

                    positions.append(
                        pygame.math.Vector2(transform.x + x_pos, transform.y + y_pos)
                    )

        elif center_pile:
            tiles: List[Union[Tile, Literal["STARTING_MARKER"]]] = []
            types: List[Union[Tile, Literal["STARTING_MARKER"]]] = [
                STARTING_MARKER,
                *TILE_TYPES,
            ]
            for tile_type in types:
                tiles.extend([tile_type for _ in range(self.center_pile[tile_type])])

            for y in range(CENTER_GRID_SIZE):
                for x in range(CENTER_GRID_SIZE):
                    tile_type = (
                        tiles[y * CENTER_GRID_SIZE + x]
                        if y * CENTER_GRID_SIZE + x < len(tiles)
                        else EMPTY
                    )
                    if tile_type == tile:
                        x_pos = (
                            PLAYER_WIDTH
                            + CENTER_SIZE // 2
                            - CENTER_GRID_SIZE * TILE_SIZE // 2
                            - (CENTER_GRID_SIZE - 1) * TILE_SPACING // 2
                            + (TILE_SIZE + TILE_SPACING) * x
                        )
                        y_pos = (
                            CENTER_SIZE // 2
                            - CENTER_GRID_SIZE * TILE_SIZE // 2
                            - (CENTER_GRID_SIZE - 1) * TILE_SPACING // 2
                            + (TILE_SIZE + TILE_SPACING) * y
                        )

                        positions.append(pygame.math.Vector2(x_pos, y_pos))

        else:
            return self.players[player_index].get_rendering_positions(
                tile, player_type, line_index
            )

        return positions

    def render_factory(
        self,
        factory_index: int,
        canvas: pygame.Surface,
        w_transform: int,
        h_transform: int,
        *,
        no_tiles: bool = False,
    ) -> None:
        gfxdraw.aacircle(
            canvas,
            w_transform,
            h_transform,
            FACTORY_RADIUS,
            COLOR_BLACK,
        )
        if not no_tiles:
            for tile in TILE_TYPES:
                positions = self.get_rendering_positions(
                    tile, factory_index=factory_index
                )

                for position in positions:
                    canvas.blit(
                        IMAGES[tile].normal,
                        (position.x, position.y),
                    )

    def render(
        self, *, player1_wins=-1, player2_wins=-1, ties=-1, no_tiles_but_wall=False
    ) -> None:
        canvas.fill(COLOR_WHITE)

        # Line Borders
        pygame.draw.aaline(
            canvas, COLOR_BLACK, (PLAYER_WIDTH, 0), (PLAYER_WIDTH, TOTAL_HEIGHT)
        )
        pygame.draw.aaline(
            canvas, COLOR_BLACK, (0, PLAYER_HEIGHT), (PLAYER_WIDTH, PLAYER_HEIGHT)
        )

        # Player display
        for player_index, player in enumerate(self.players):
            w_transform = TILE_BORDER + SECTION_SPACING
            h_transform = PLAYER_HEIGHT if player_index == 1 else 0
            wins = player1_wins if player_index == 0 else player2_wins

            player.render(
                canvas,
                w_transform,
                h_transform,
                no_tiles_but_wall=no_tiles_but_wall,
                wins=wins,
            )

        # Center display
        for index in range(len(self.factories)):
            pos = self.factory_position(index)

            self.render_factory(
                index,
                canvas,
                int(pos.x),
                int(pos.y),
                no_tiles=no_tiles_but_wall,
            )

        # Center pile
        # Create actual tiles, not the counter
        if not no_tiles_but_wall:
            types: List[Union[Tile, Literal["STARTING_MARKER"]]] = [
                STARTING_MARKER,
                *TILE_TYPES,
            ]

            for tile_type in types:
                positions = self.get_rendering_positions(tile_type, center_pile=True)

                for position in positions:
                    canvas.blit(
                        IMAGES[tile_type].normal,
                        (position.x, position.y),
                    )

        # Ties
        if ties != -1:
            text = MAIN_FONT.render(f"Ties: {ties}", True, COLOR_BLACK)
            text_rect = text.get_rect(
                center=(
                    PLAYER_WIDTH + CENTER_SIZE / 2,
                    CENTER_SIZE - SCORE_HEIGHT / 2,
                )
            )
            canvas.blit(text, text_rect)
