from dataclasses import dataclass
from typing import Literal, List, Dict, Union
import pygame


@dataclass
class TileImage:
    faded: pygame.Surface
    normal: pygame.Surface


COMPUTER_MOVE_TIME = 1  # seconds
EVALUATION_VERSION = "v2"


COMPARE_COMPUTER_MOVE_TIME = 0.1  # seconds
NUM_COMPARE_ROUNDS = 100
PLAYER1_COMPARE_VERSION = "v2"
PLAYER2_COMPARE_VERSION = "v2"


FACTORY_COUNT = 5
NUM_EACH_TILE = 20
TILES_PER_FACTORY = 4
WALL_SIZE = 5
NEGATIVE_FLOOR_POINTS = [1, 1, 2, 2, 2]
HORIZONTAL_LINE_BONUS = 2
VERTICAL_LINE_BONUS = 7
FIVE_OF_A_KIND_BONUS = 10

ANIMATION_SECONDS = 1
PAUSE_TIME_AFTER_MOVE = 1
FRAME_RATE = 30

# Display Settings
TILE_SIZE = 25
TILE_BORDER = 1
TILE_SPACING = 5
CENTER_BORDER = 20
CENTER_GRID_SIZE = 4
FACTORY_RADIUS = 60
NUM_FLOOR_TILES = 9
FLOOR_TILE_SPACING = 10
SECTION_SPACING = 10
SCORE_HEIGHT = 50
FLOOR_NUMBER_HEIGHT = 20
FONT_FILE_NAME = "pixelized"
FLOOR_FONT_SIZE = 16
MAIN_FONT_SIZE = 25


STARTING_MARKER = "STARTING_MARKER"
EMPTY = "EMPTY"
BLUE = "BLUE"
YELLOW = "YELLOW"
RED = "RED"
BLACK = "BLACK"
STAR = "STAR"
Tile = Literal["BLUE", "YELLOW", "RED", "BLACK", "STAR"]
TILE_TYPES: list[Tile] = [BLUE, YELLOW, RED, BLACK, STAR]

BYTE_CONVERSION: Dict[Union[Tile, Literal["EMPTY"]], bytes] = {
    EMPTY: b"\x00",
    BLUE: b"\x01",
    YELLOW: b"\x02",
    RED: b"\x03",
    BLACK: b"\x04",
    STAR: b"\x05",
}
TILE_NUMBERING: Dict[Union[Tile, Literal["EMPTY"]], int] = {
    EMPTY: 0,
    BLUE: 1,
    YELLOW: 2,
    RED: 3,
    BLACK: 4,
    STAR: 5,
}

# Stores column position of tile in each row
TILE_POSITIONS: Dict[Tile, List[int]] = {
    BLUE: [0, 1, 2, 3, 4],
    YELLOW: [1, 2, 3, 4, 0],
    RED: [2, 3, 4, 0, 1],
    BLACK: [3, 4, 0, 1, 2],
    STAR: [4, 0, 1, 2, 3],
}
WALL_TILES: List[List[Tile]] = [
    [BLUE, YELLOW, RED, BLACK, STAR],
    [STAR, BLUE, YELLOW, RED, BLACK],
    [BLACK, STAR, BLUE, YELLOW, RED],
    [RED, BLACK, STAR, BLUE, YELLOW],
    [YELLOW, RED, BLACK, STAR, BLUE],
]

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_BROWN = (214, 168, 124)

PLAYER_WIDTH = (
    2 * WALL_SIZE * (TILE_SIZE + TILE_SPACING)
    - TILE_SPACING
    + 3 * SECTION_SPACING
    + 2 * TILE_BORDER
)
PLAYER_HEIGHT = (
    WALL_SIZE * (TILE_SIZE + TILE_SPACING)
    - TILE_SPACING
    + 2 * SECTION_SPACING
    + FLOOR_NUMBER_HEIGHT
    + TILE_SIZE
    + SCORE_HEIGHT
)
CENTER_SIZE = 2 * PLAYER_HEIGHT
TOTAL_WIDTH = PLAYER_WIDTH + CENTER_SIZE
TOTAL_HEIGHT = 2 * PLAYER_HEIGHT

pygame.init()
canvas = pygame.display.set_mode((TOTAL_WIDTH, TOTAL_HEIGHT))
clock = pygame.time.Clock()

FLOOR_FONT = pygame.font.Font(f"assets/fonts/{FONT_FILE_NAME}.ttf", FLOOR_FONT_SIZE)
MAIN_FONT = pygame.font.Font(f"assets/fonts/{FONT_FILE_NAME}.ttf", MAIN_FONT_SIZE)

# Load and scale images (faded and normal)
ImageFileName = Union[Tile, Literal["STARTING_MARKER"]]
IMAGES: Dict[ImageFileName, TileImage] = {}
file_names: List[ImageFileName] = [
    *TILE_TYPES,
    STARTING_MARKER,
]

for _tile in file_names:
    _image = pygame.image.load(f"assets/images/{_tile}.png")

    _image = pygame.transform.smoothscale(_image, (TILE_SIZE, TILE_SIZE))
    _faded_image = pygame.transform.smoothscale(_image, (TILE_SIZE, TILE_SIZE))
    _faded_image.set_alpha(65)

    IMAGES[_tile] = TileImage(faded=_faded_image, normal=_image)
