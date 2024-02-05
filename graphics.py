from __future__ import annotations
from collections import Counter
import math
from constants import *
from typing import NamedTuple, Tuple, Union, List, Literal, Dict
from dataclasses import dataclass
from game import Game, Move, PartialMove
from player import Player
from utils import Vector
import pygame
from pygame import gfxdraw


ImageFileName = Union[Tile, Literal[6]]


@dataclass
class TileImage:
    faded: pygame.Surface
    normal: pygame.Surface


class GraphicsInfo(NamedTuple):
    canvas: pygame.Surface
    clock: pygame.time.Clock
    floor_font: pygame.font.Font
    main_font: pygame.font.Font
    images: Dict[ImageFileName, TileImage]


def init() -> GraphicsInfo:
    pygame.init()
    canvas = pygame.display.set_mode((TOTAL_WIDTH, TOTAL_HEIGHT))
    clock = pygame.time.Clock()

    floor_font = pygame.font.Font(f"assets/fonts/{FONT_FILE_NAME}.ttf", FLOOR_FONT_SIZE)
    main_font = pygame.font.Font(f"assets/fonts/{FONT_FILE_NAME}.ttf", MAIN_FONT_SIZE)

    # Load and scale images (faded and normal)

    images: Dict[ImageFileName, TileImage] = {}
    file_names: List[ImageFileName] = [
        *TILE_TYPES,
        STARTING_MARKER,
    ]

    tile_names: Dict[ImageFileName, str] = {
        BLUE: "BLUE",
        YELLOW: "YELLOW",
        RED: "RED",
        BLACK: "BLACK",
        STAR: "STAR",
        STARTING_MARKER: "STARTING_MARKER",
    }

    for tile in file_names:
        image = pygame.image.load(f"assets/images/{tile_names[tile]}.png")

        image = pygame.transform.smoothscale(image, (TILE_SIZE, TILE_SIZE))
        faded_image = pygame.transform.smoothscale(image, (TILE_SIZE, TILE_SIZE))
        faded_image.set_alpha(FADED_IMAGE_ALPHA)

        images[tile] = TileImage(faded=faded_image, normal=image)

    return GraphicsInfo(canvas, clock, floor_font, main_font, images)


# Return the possible positions for a tile of a given type
def get_player_rendering_positions(
    player: Player,
    tile: Union[Tile, Literal[6]],
    type: Literal["wall", "pattern_line", "floor"],
    line_index: int = 0,
) -> List[Vector]:
    positions: List[Vector] = []

    w_transform = 1 + SECTION_SPACING
    h_transform = PLAYER_HEIGHT if player.index == 1 else 0

    if type == "pattern_line":
        y_pos = SCORE_HEIGHT + (TILE_SIZE + TILE_SPACING) * line_index
        line = player.pattern_lines[line_index]

        for column_index in range(line_index, -1, -1):
            x_pos = (TILE_SIZE + TILE_SPACING) * (WALL_SIZE - column_index - 1)
            tile_type = (
                line.tile if line_index - column_index + 1 - line.space > 0 else EMPTY
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
            tile_type = player.floor[x] if x < len(player.floor) else EMPTY

            if tile == tile_type:
                positions.append(Vector(w_transform + x_pos, h_transform + y_pos))

    return positions


def render_player(
    player: Player,
    graphics_info: GraphicsInfo,
    w_transform: int,
    h_transform: int,
    *,
    wins: int = -1,
    no_tiles_but_wall: bool = False,
    highlight_lines: bool = False,
    partial_move: Union[PartialMove, None] = None,
) -> None:
    def draw_tile_and_border(
        x_pos: float,
        y_pos: float,
        tile: Union[ImageFileName, Literal[0]],
        *,
        faded: bool = True,
        force_tiles: bool = False,
    ) -> None:
        pygame.draw.rect(
            graphics_info.canvas,
            COLOR_BROWN,
            (
                x_pos - 1,
                y_pos - 1,
                TILE_SIZE + 2,
                TILE_SIZE + 2,
            ),
            width=1,
        )
        if tile != EMPTY and (not no_tiles_but_wall or force_tiles):
            graphics_info.canvas.blit(
                graphics_info.images[tile].faded
                if faded
                else graphics_info.images[tile].normal,
                (x_pos, y_pos),
            )

    # Floor and pattern line tiles
    types: List[Union[Tile, Literal[6]]] = [
        *TILE_TYPES,
        STARTING_MARKER,
    ]
    for tile_type in types:
        floor_positions = get_player_rendering_positions(player, tile_type, "floor")

        pattern_line_positions: List[Vector] = []
        for line_index in range(WALL_SIZE):
            pattern_line_positions.extend(
                get_player_rendering_positions(
                    player, tile_type, "pattern_line", line_index
                )
            )

        for position in floor_positions + pattern_line_positions:
            draw_tile_and_border(position.x, position.y, tile_type, faded=False)

    mouse = pygame.Vector2(pygame.mouse.get_pos())
    player.hovered_pattern_line = None

    # Pattern Lines
    for row_index in range(len(player.pattern_lines)):
        y_pos = SCORE_HEIGHT + (TILE_SIZE + TILE_SPACING) * row_index

        for column_index in range(row_index + 1):
            x_pos = (TILE_SIZE + TILE_SPACING) * (WALL_SIZE - column_index - 1)

            draw_tile_and_border(
                w_transform + x_pos, h_transform + y_pos, EMPTY, faded=False
            )

        if (
            highlight_lines
            and player.index == 0
            and partial_move
            and (
                partial_move.drawing == player.pattern_lines[row_index].tile
                or player.pattern_lines[row_index].tile == EMPTY
            )
            and player.pattern_lines[row_index].space > 0
            and player.wall[row_index][TILE_POSITIONS[partial_move.drawing][row_index]]
            == EMPTY
        ):
            rect_x = (
                w_transform
                + (TILE_SIZE + TILE_SPACING) * (WALL_SIZE - row_index - 1)
                - 2
            )
            rect_y = h_transform + y_pos - 2
            rect_w = (TILE_SIZE + TILE_SPACING) * (row_index + 1) - 4
            rect_h = TILE_SIZE + TILE_SPACING - 4

            if (
                rect_x <= mouse.x <= rect_x + rect_w
                and rect_y <= mouse.y <= rect_y + rect_h
            ):
                player.hovered_pattern_line = row_index
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)

            pygame.draw.rect(
                graphics_info.canvas,
                COLOR_RED,
                (
                    rect_x,
                    rect_y,
                    rect_w,
                    rect_h,
                ),
                width=2,
            )

    # Wall
    for y in range(WALL_SIZE):
        for x in range(WALL_SIZE):
            x_pos = (
                (TILE_SIZE + TILE_SPACING) * (WALL_SIZE + x)
                - TILE_SPACING
                + 1
                + SECTION_SPACING
            )
            y_pos = SCORE_HEIGHT + (TILE_SIZE + TILE_SPACING) * y

            draw_tile_and_border(
                w_transform + x_pos,
                h_transform + y_pos,
                WALL_TILES[y][x],
                faded=not player.wall[y][x],
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

        text = graphics_info.floor_font.render(f"-{number}", True, BLACK)
        text_rect = text.get_rect(
            center=(
                w_transform + x_pos + TILE_SIZE / 2,
                h_transform + y_pos - FLOOR_NUMBER_HEIGHT / 2,
            )
        )
        graphics_info.canvas.blit(text, text_rect)

    if highlight_lines and player.index == 0:
        rect_x = w_transform - 2
        rect_y = h_transform + PLAYER_HEIGHT - TILE_SIZE - SECTION_SPACING - 2
        rect_w = (TILE_SIZE + FLOOR_TILE_SPACING) * NUM_FLOOR_TILES - 4
        rect_h = TILE_SIZE + 3

        if (
            rect_x <= mouse.x <= rect_x + rect_w
            and rect_y <= mouse.y <= rect_y + rect_h
        ):
            player.hovered_pattern_line = -1
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)

        pygame.draw.rect(
            graphics_info.canvas,
            COLOR_RED,
            (rect_x, rect_y, rect_w, rect_h),
            width=2,
        )

    # Score
    text = graphics_info.main_font.render(f"Score: {player.points}", True, BLACK)
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
    graphics_info.canvas.blit(text, text_rect)

    # Wins
    if wins != -1:
        text = graphics_info.main_font.render(f"Wins: {wins}", True, BLACK)
        text_rect = text.get_rect(
            midleft=(
                SECTION_SPACING,
                h_transform + SCORE_HEIGHT / 2,
            )
        )
        graphics_info.canvas.blit(text, text_rect)


# Rendering location of factories
def game_factory_position(index: int) -> Vector:
    radius = CENTER_SIZE // 2 - FACTORY_RADIUS - CENTER_BORDER

    angle = 360 / FACTORY_COUNT * index - 90
    x_pos = int(radius * math.cos(math.radians(angle)))
    y_pos = int(radius * math.sin(math.radians(angle)))

    return Vector(PLAYER_WIDTH + CENTER_SIZE // 2 + x_pos, CENTER_SIZE // 2 + y_pos)


# Used for piece animation
def get_game_rendering_positions(
    game: Game,
    tile: Union[Tile, Literal[6]],
    *,
    center_pile: bool = False,
    factory_index: int = -1,
    player_index: int = 0,
    line_index: int = 0,
    player_type: Literal["wall", "pattern_line", "floor"] = "wall",
) -> List[Vector]:
    positions: List[Vector] = []

    if factory_index != -1:
        factory_tiles: List[Tile] = []
        for tile_type in TILE_TYPES:
            factory_tiles.extend(
                [tile_type for _ in range(game.factories[factory_index][tile_type])]
            )

        transform = game_factory_position(factory_index)

        offsets = [[-1, -1], [1, -1], [-1, 1], [1, 1]]
        for index, factory_tile in enumerate(factory_tiles):
            if factory_tile == tile:
                x_off, y_off = offsets[index]
                x_pos = (x_off - 1) * (TILE_SIZE // 2) + x_off * TILE_SPACING // 2
                y_pos = (y_off - 1) * (TILE_SIZE // 2) + y_off * TILE_SPACING // 2

                positions.append(Vector(transform.x + x_pos, transform.y + y_pos))

    elif center_pile:
        tiles: List[Union[Tile, Literal[6]]] = []
        types: List[Union[Tile, Literal[6]]] = [
            STARTING_MARKER,
            *TILE_TYPES,
        ]
        for tile_type in types:
            tiles.extend([tile_type for _ in range(game.center_pile[tile_type])])

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

                    positions.append(Vector(x_pos, y_pos))

    else:
        return game.players[player_index].get_rendering_positions(
            tile, player_type, line_index
        )

    return positions


def render_tile(
    graphics_info: GraphicsInfo,
    tile: Union[Tile, Literal[6]],
    position: Vector,
    *,
    faded=False,
):
    if faded:
        graphics_info.canvas.blit(
            graphics_info.images[tile].faded, (position.x, position.y)
        )
    else:
        graphics_info.canvas.blit(
            graphics_info.images[tile].normal, (position.x, position.y)
        )


def render_tile_outline(
    graphics_info: GraphicsInfo,
    position: Vector,
    color: Tuple[int, int, int],
    alpha: int,
) -> None:
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    alpha_color = color + (alpha,)

    pygame.draw.rect(surface, alpha_color, (0, 0, TILE_SIZE, TILE_SIZE), 2)

    graphics_info.canvas.blit(surface, (position.x, position.y))


def render_factory(
    game: Game,
    graphics_info: GraphicsInfo,
    factory_index: int,
    w_transform: int,
    h_transform: int,
    *,
    no_tiles: bool = False,
    player_choice: Literal["tile", "line", None] = None,
    highlighted_tile: Union[Tile, None] = None,
    is_tile_hovered: bool = False,
) -> None:
    gfxdraw.aacircle(
        graphics_info.canvas,
        w_transform,
        h_transform,
        FACTORY_RADIUS,
        COLOR_BLACK,
    )

    if not no_tiles:
        for tile in TILE_TYPES:
            positions = get_game_rendering_positions(
                game, tile, factory_index=factory_index
            )

            for position in positions:
                render_tile(
                    graphics_info,
                    tile,
                    position,
                    faded=is_tile_hovered and highlighted_tile != tile,
                )

                if player_choice is not None:
                    color = COLOR_RED if player_choice == "tile" else COLOR_GRAY

                    alpha = (
                        FADED_IMAGE_ALPHA
                        if is_tile_hovered and highlighted_tile != tile
                        else 255
                    )
                    render_tile_outline(graphics_info, position, color, alpha)


def get_hovered_partial_move(game: Game) -> Union[PartialMove, None]:
    mouse = Vector(*pygame.mouse.get_pos())
    hover_tile: Union[Tile, None] = None
    hover_factory: Union[int, None] = None

    for factory_index in [*range(FACTORY_COUNT), -1]:
        for tile in TILE_TYPES:
            if factory_index == -1:
                positions = get_game_rendering_positions(game, tile, center_pile=True)
            else:
                positions = get_game_rendering_positions(
                    game, tile, factory_index=factory_index
                )
            for position in positions:
                if (
                    position.x <= mouse.x <= position.x + TILE_SIZE
                    and position.y <= mouse.y <= position.y + TILE_SIZE
                ):
                    hover_tile = tile
                    hover_factory = factory_index

    if hover_factory is None or hover_tile is None:
        return None

    if hover_factory == -1:
        return PartialMove(
            drawing=hover_tile,
            amount=game.center_pile[hover_tile],
            moving_to_center=Counter(),
            player_index=0,
            factory_index=hover_factory,
            is_center_draw=True,
            first_draw_from_center=game.center_pile[STARTING_MARKER] == 1,
        )
    else:
        modified_factory = game.factories[hover_factory].copy()
        modified_factory[hover_tile] = 0

        return PartialMove(
            drawing=hover_tile,
            amount=game.factories[hover_factory][hover_tile],
            moving_to_center=modified_factory,
            player_index=0,
            factory_index=hover_factory,
            is_center_draw=False,
            first_draw_from_center=False,
        )


def get_hovered_move(game: Game, partial_move: PartialMove) -> Union[Move, None]:
    pattern_line = game.players[0].hovered_pattern_line

    if pattern_line is None:
        return None

    if pattern_line == -1:
        amount = 0
        floor_amount = partial_move.amount
    else:
        amount = min(
            game.players[0].pattern_lines[pattern_line].space, partial_move.amount
        )
        floor_amount = partial_move.amount - amount

    return Move(
        drawing=partial_move.drawing,
        amount=amount,
        moving_to_center=partial_move.moving_to_center,
        player_index=0,
        factory_index=partial_move.factory_index,
        pattern_line=pattern_line,
        floor_tiles=[partial_move.drawing] * floor_amount,
        is_center_draw=partial_move.is_center_draw,
        first_draw_from_center=partial_move.first_draw_from_center,
    )


def render_game(
    game: Game,
    graphics_info: GraphicsInfo,
    *,
    player1_wins=-1,
    player2_wins=-1,
    ties=-1,
    no_tiles_but_wall=False,
    player_choice: Literal["tile", "line", None] = None,
    partial_tile_move: Union[PartialMove, None] = None,
) -> None:
    graphics_info.canvas.fill(COLOR_WHITE)

    if player_choice is not None and partial_tile_move is None:
        partial_move = get_hovered_partial_move(game)

        if partial_move is None:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)

    else:
        partial_move = partial_tile_move
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    # Line Borders
    pygame.draw.aaline(
        graphics_info.canvas,
        COLOR_BLACK,
        (PLAYER_WIDTH, 0),
        (PLAYER_WIDTH, TOTAL_HEIGHT),
    )
    pygame.draw.aaline(
        graphics_info.canvas,
        COLOR_BLACK,
        (0, PLAYER_HEIGHT),
        (PLAYER_WIDTH, PLAYER_HEIGHT),
    )

    # Player display
    for player_index, player in enumerate(game.players):
        w_transform = 1 + SECTION_SPACING
        h_transform = PLAYER_HEIGHT if player_index == 1 else 0
        wins = player1_wins if player_index == 0 else player2_wins

        render_player(
            player,
            graphics_info,
            w_transform,
            h_transform,
            no_tiles_but_wall=no_tiles_but_wall,
            wins=wins,
            highlight_lines=player_choice == "line",
            partial_move=partial_tile_move,
        )

    # Factory Display
    for index in range(len(game.factories)):
        pos = game_factory_position(index)

        highlighted_tile = None
        if partial_move and partial_move.factory_index == index:
            highlighted_tile = partial_move.drawing

        render_factory(
            game,
            graphics_info,
            index,
            int(pos.x),
            int(pos.y),
            no_tiles=no_tiles_but_wall,
            player_choice=player_choice,
            highlighted_tile=highlighted_tile,
            is_tile_hovered=partial_move is not None,
        )

    # Center pile
    # Create actual tiles, not the counter
    if not no_tiles_but_wall:
        types: List[Union[Tile, Literal[6]]] = [
            STARTING_MARKER,
            *TILE_TYPES,
        ]

        for tile_type in types:
            positions = get_game_rendering_positions(game, tile_type, center_pile=True)

            for position in positions:
                faded = partial_move is not None and (
                    partial_move.factory_index != -1
                    or partial_move.drawing != tile_type
                )
                if (
                    partial_move
                    and partial_move.factory_index == -1
                    and tile_type == STARTING_MARKER
                ):
                    faded = False

                render_tile(graphics_info, tile_type, position, faded=faded)

                if player_choice is not None:
                    color = COLOR_RED if player_choice == "tile" else COLOR_GRAY
                    alpha = FADED_IMAGE_ALPHA if faded else 255

                    render_tile_outline(graphics_info, position, color, alpha)

    # Ties
    if ties != -1:
        text = graphics_info.main_font.render(f"Ties: {ties}", True, COLOR_BLACK)
        text_rect = text.get_rect(
            center=(
                PLAYER_WIDTH + CENTER_SIZE / 2,
                CENTER_SIZE - SCORE_HEIGHT / 2,
            )
        )
        graphics_info.canvas.blit(text, text_rect)
