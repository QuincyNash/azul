from __future__ import annotations
from constants import *
from player import Player, PatternLine
from typing import List, Union, Literal
from dataclasses import dataclass
from collections import Counter
import struct
import random
import pickle


move_counter = 0
serialize_counter = 0
points_counter = 0
make_move_counter = 0
no_move_counter = 0
Factory = Counter[Union[Tile, Literal[6]]]


@dataclass(slots=True)
class PartialMove:
    drawing: Tile
    amount: int
    moving_to_center: Factory
    player_index: int  # Index of player in Game.players list
    factory_index: int  # Index of factory in Game.factories list, if center pile, then index is -1
    is_center_draw: bool
    first_draw_from_center: bool


@dataclass(slots=True)
class Move(PartialMove):
    pattern_line: int
    floor_tiles: List[Tile]


@dataclass(slots=True)
class PointChange:
    pattern_line: int
    tile: Tile
    points: int
    space_left: int
    completed: bool


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

        self.players = [
            Player(index=0),
            Player(index=1),
        ]

        self.new_round()

    def copy(self) -> Game:
        copied_game: Game = pickle.loads(pickle.dumps(self, -1))

        return copied_game

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

    def factory_to_readable_factory(self, factory: Factory) -> Dict[str, int]:
        result: Dict[str, int] = {}

        for tile, count in factory.items():
            result[TILE_NAMES[tile]] = count

        return result

    def readable_factory_to_factory(self, readable_factory: Dict[str, int]) -> Factory:
        result: Factory = Counter()

        for tile, count in readable_factory.items():
            # Tiles in factory cannot be empty
            result[TILE_NUMBERS[tile]] = count  # type: ignore

        return result

    def to_json(self, current_turn: Literal[0, 1]) -> dict:
        result: dict = {}

        for index, player in enumerate(self.players):
            result[f"player{index + 1}"] = {
                "pattern_lines": [
                    {"tile": TILE_NAMES[line.tile], "space": line.space}
                    for line in player.pattern_lines
                ],
                "wall": [
                    ["FULL" if filled else "EMPTY" for filled in row]
                    for row in player.wall
                ],
                "floor": list(map(TILE_NAMES.get, player.floor)),
                "points": player.points,
                "has_starting_marker": player.has_starting_marker,
            }

        result["factories"] = list(
            map(self.factory_to_readable_factory, self.factories)
        )
        result["center_pile"] = self.factory_to_readable_factory(self.center_pile)
        result["turn"] = current_turn + 1

        return result

    def from_json(self, json: dict) -> None:
        for index, player_json in enumerate([json["player1"], json["player2"]]):
            player = self.players[index]

            # If the user tries to load an invalid json file, an error will be thrown
            player.pattern_lines = [
                PatternLine(tile=TILE_NUMBERS[line["tile"]], space=line["space"])  # type: ignore
                for line in player_json["pattern_lines"]
            ]
            player.wall = [
                [True if filled == "FULL" else False for filled in row]
                for row in player_json["wall"]
            ]
            player.floor = list(map(TILE_NUMBERS.get, player_json["floor"]))  # type: ignore

            player.points = player_json["points"]
            player.has_starting_marker = player_json["has_starting_marker"]

        self.factories = list(map(self.readable_factory_to_factory, json["factories"]))
        self.center_pile = self.readable_factory_to_factory(json["center_pile"])

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
    def new_round(self) -> Literal[0, 1]:
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

    def calculate_potential_points(
        self, wall: List[List[bool]], tile: Tile, row_index: int
    ) -> int:
        column_index = TILE_POSITIONS[tile][row_index]
        potential_points = 1  # Count the tile that was placed
        horizontal_movement = False

        # Count all placed tiles in each row and column
        for xdir, ydir in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            # Continue counting while tiles are filled and exist
            xpos, ypos = column_index + xdir, row_index + ydir
            while 0 <= xpos < WALL_SIZE and 0 <= ypos < WALL_SIZE and wall[ypos][xpos]:
                potential_points += 1
                xpos += xdir
                ypos += ydir
                # There is a tile left or right of the placed tile, so count the placed tile twice
                if xdir != 0:
                    horizontal_movement = True

        return potential_points + horizontal_movement

    def calculate_bonus_points(self, wall: List[List[bool]]) -> int:
        bonus_points = 0

        for row in wall:
            if all(row):
                bonus_points += HORIZONTAL_LINE_BONUS

        for column in zip(*wall):
            if all(column):
                bonus_points += VERTICAL_LINE_BONUS

        for tile in TILE_TYPES:
            if all(wall[row][TILE_POSITIONS[tile][row]] for row in range(WALL_SIZE)):
                bonus_points += FIVE_OF_A_KIND_BONUS

        return bonus_points

    def calculate_negative_floor_points(
        self, floor: List[Union[Tile, Literal[6]]]
    ) -> int:
        # Floor points are stored in NEGATIVE_FLOOR_POINTS (sum the first n which are occupied)
        return sum(NEGATIVE_FLOOR_POINTS[: len(floor)])

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
            old_player_points = player.points
            point_changes: List[PointChange] = []

            # For every line, if it is full, move a tile to the wall
            wall, pattern_lines = player.wall, player.pattern_lines

            # Bonus only does not move tiles from pattern lines to the wall
            if flag != "bonus_only":
                for row_index, line in enumerate(pattern_lines):
                    if line.space == 0 and line.tile != EMPTY:
                        column_index = TILE_POSITIONS[line.tile][row_index]

                        # Add tile to wall even if not modified, if modified, remove later
                        wall[row_index][column_index] = True

                        potential_points = self.calculate_potential_points(
                            wall, line.tile, row_index
                        )
                        total_positive_points += potential_points

                        if modify_game:
                            player.points += potential_points
                            # Remove tiles from pattern line
                            pattern_lines[row_index].space = row_index + 1
                            pattern_lines[row_index].tile = EMPTY
                        else:
                            point_changes.append(
                                PointChange(
                                    row_index,
                                    line.tile,
                                    potential_points,
                                    space_left=0,
                                    completed=True,
                                )
                            )

                    # Pattern line is not full but contains some tiles, so calculate the potential points once the row is complete
                    elif line.tile != EMPTY and not modify_game:
                        potential_points = self.calculate_potential_points(
                            wall, line.tile, row_index
                        )
                        point_changes.append(
                            PointChange(
                                row_index,
                                line.tile,
                                potential_points,
                                space_left=line.space,
                                completed=False,
                            )
                        )

            # Calculate bonus points
            if flag in ["include_bonus", "bonus_only"]:
                bonus_points = self.calculate_bonus_points(player.wall)
                total_positive_points += bonus_points

                if modify_game:
                    player.points += bonus_points

            # Reset wall tiles
            for point_change in point_changes:
                wall[point_change.pattern_line][
                    TILE_POSITIONS[point_change.tile][point_change.pattern_line]
                ] = False

            if flag != "bonus_only":
                # Points can't go below 0
                floor_negative_points = min(
                    self.calculate_negative_floor_points(player.floor),
                    total_positive_points
                    + old_player_points,  # Negative points cannot go below the previous points of the player added to the new positive points
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
                            pattern_line=-1,
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
