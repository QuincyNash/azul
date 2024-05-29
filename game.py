from __future__ import annotations
import json
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
    factory_index: (
        int  # Index of factory in Game.factories list, if center pile, then index is -1
    )
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
    last_round: bool


class Game:
    def __init__(self, *, seed=None) -> None:
        if seed is not None:
            random.seed(seed)

        # Counters are used for factories to store the number of occurences of each tile
        # Create factories and populate each with 4 random tiles
        self.factories: List[Factory] = [Counter() for _ in range(FACTORY_COUNT)]

        self.is_first_round = True

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

    def write_to_file(self, current_turn: Literal[0, 1]) -> None:
        with open(f"game_state.json", "w") as file:
            json.dump(self.to_json(current_turn), file)

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

    def serialize(self, points_results: List[PointsResult]) -> str:
        basic_points = 0
        for player_index in [0, 1]:
            points = (
                sum(
                    (change.points if change.completed else 0)
                    for change in points_results[player_index].point_changes
                )
                - points_results[player_index].negative_floor_points
                + points_results[player_index].bonus_points
            )
            points *= -1 if player_index == 1 else 1
            basic_points += points

        def get_point_change(player_index: int, row: int) -> Union[PointChange, None]:
            for change in points_results[player_index].point_changes:
                if change.pattern_line == row:
                    return change

            return None

        inputs: List[int] = [basic_points]

        for player_index, player in enumerate(self.players):
            for tile in TILE_TYPES:
                for factory in [*self.factories, self.center_pile]:
                    inputs.append(factory[tile])
            inputs.append(self.center_pile[STARTING_MARKER])

            for row, line in enumerate(player.pattern_lines):
                inputs.append(line.space)
                inputs.append(int(line.tile))

                point_change = get_point_change(player_index, row)
                if point_change and not point_change.completed:
                    potential_points = point_change.points
                else:
                    potential_points = 0

                inputs.append(potential_points)

            for row in player.wall:
                inputs.extend(map(int, row))

            inputs.append(len(player.floor))
            inputs.append(int(player.has_starting_marker))

        most_tiles_in_row = 0
        for test_player in self.players:
            for row in range(WALL_SIZE):
                tiles_in_row = sum(test_player.wall[row])
                most_tiles_in_row = max(most_tiles_in_row, tiles_in_row)
        inputs.append(WALL_SIZE - most_tiles_in_row)

        return ",".join(map(str, inputs))

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
                count = tiles.count(tile)
                if count > 0:
                    factory[tile] = count

        self.center_pile[STARTING_MARKER] = 1

        first_player = 0 if self.players[0].has_starting_marker else 1

        self.players[0].has_starting_marker = False
        self.players[1].has_starting_marker = False

        self.is_first_round = False

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
            del self.center_pile[STARTING_MARKER]

        player.floor.extend(move.floor_tiles)

        if move.is_center_draw:
            # Remove tiles from center
            del self.center_pile[move.drawing]
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
        vertical_movement = False

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
                if ydir != 0:
                    vertical_movement = True

        return potential_points + (
            1 if horizontal_movement and vertical_movement else 0
        )

    def calculate_potential_bonus_points(
        self, player: Player, wall: List[List[bool]], tile: Tile, row_index: int
    ) -> int:
        column_index = TILE_POSITIONS[tile][row_index]

        # Add tile to wall temporarily to calculate bonus points
        wall[row_index][column_index] = True
        bonus_points = self.calculate_bonus_points(player, wall, modify_player=False)
        wall[row_index][column_index] = False

        return bonus_points

    def calculate_bonus_points(
        self, player: Player, wall: List[List[bool]], modify_player: bool = True
    ) -> int:
        bonus_points = 0

        for row_index, row in enumerate(wall):
            if not player.bonuses.row[row_index] and all(row):
                bonus_points += HORIZONTAL_LINE_BONUS
                if modify_player:
                    player.bonuses.row[row_index] = True

        for column_index, column in enumerate(zip(*wall)):
            if not player.bonuses.col[column_index] and all(column):
                bonus_points += VERTICAL_LINE_BONUS
                if modify_player:
                    player.bonuses.col[column_index] = True

        for tile_index, tile in enumerate(TILE_TYPES):
            if not player.bonuses.diagonal[tile_index] and all(
                wall[row][TILE_POSITIONS[tile][row]] for row in range(WALL_SIZE)
            ):
                bonus_points += FIVE_OF_A_KIND_BONUS
                if modify_player:
                    player.bonuses.diagonal[tile_index] = True

        return bonus_points

    def calculate_negative_floor_points(self, floor_length: int) -> int:
        # Floor points are stored in NEGATIVE_FLOOR_POINTS (sum the first n which are occupied)
        return sum(NEGATIVE_FLOOR_POINTS[:floor_length])

    def calculate_points_and_modify(self) -> None:
        self.calculate_points(modify_game=True)

    def calculate_points(
        self,
        *,
        modify_game=False,
    ) -> List[PointsResult]:
        results: List[PointsResult] = []
        last_round = False

        for player in self.players:
            total_positive_points = 0
            bonus_points = 0
            floor_negative_points = 0
            old_player_points = player.points
            point_changes: List[PointChange] = []

            # For every line, if it is full, move a tile to the wall
            pattern_lines = player.pattern_lines
            new_wall = [[value for value in row] for row in player.wall]

            # Bonus only does not move tiles from pattern lines to the wall
            for row_index, line in enumerate(pattern_lines):
                if line.space == 0 and line.tile != EMPTY:
                    column_index = TILE_POSITIONS[line.tile][row_index]

                    # Add tile to wall even if not modified, modification doesn't matter since original is copied
                    new_wall[row_index][column_index] = True

                    potential_points = self.calculate_potential_points(
                        new_wall, line.tile, row_index
                    )
                    total_positive_points += potential_points

                    if modify_game:
                        player.points += potential_points
                        # Remove tiles from pattern line
                        pattern_lines[row_index].space = row_index + 1
                        pattern_lines[row_index].tile = EMPTY

                    else:
                        # If a horizontal line will be filled, the game as about to be over
                        if player.wall[row_index].count(False) <= 1:
                            last_round = True

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
                        new_wall, line.tile, row_index
                    ) + self.calculate_potential_bonus_points(
                        player, new_wall, line.tile, row_index
                    )  # Also count the additional points from the bonus

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
            bonus_points = self.calculate_bonus_points(player, new_wall, modify_game)
            total_positive_points += bonus_points

            if modify_game:
                player.points += bonus_points

            # Points can't go below 0
            floor_negative_points = min(
                self.calculate_negative_floor_points(len(player.floor)),
                total_positive_points
                + old_player_points,  # Negative points cannot go below the previous points of the player added to the new positive points
            )

            if modify_game:
                player.points -= floor_negative_points
                player.wall = new_wall
                # And remove the floor tiles
                player.floor = []

            results.append(
                PointsResult(point_changes, bonus_points, floor_negative_points, False)
            )

        if last_round:
            for result in results:
                result.last_round = True

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
                        del factory_copy[tile]
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
