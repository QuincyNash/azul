from typing import Literal, List, Dict, Tuple, Union


COMPUTER_MOVE_TIME = 5  # seconds
EVALUATION_VERSION = "v4"


COMPARE_COMPUTER_MOVE_TIME = 0.1  # seconds
NUM_COMPARE_ROUNDS = 500
PLAYER1_COMPARE_VERSION = "v3"
PLAYER2_COMPARE_VERSION = "v2"

FACTORY_COUNT = 5
NUM_EACH_TILE = 20
TILES_PER_FACTORY = 4
WALL_SIZE = 5
NEGATIVE_FLOOR_POINTS = [1, 1, 2, 2, 2, 3, 3]
HORIZONTAL_LINE_BONUS = 2
VERTICAL_LINE_BONUS = 7
FIVE_OF_A_KIND_BONUS = 10
# Measures the importance of future points based on the longest line in the game
ENDGAME_IMPORTANCE_SCORES: List[float] = [1, 0.9, 0.7, 0.5, 0.1]

ANIMATION_SECONDS = 1
PAUSE_TIME_AFTER_MOVE = 1
FRAME_RATE = 30

# Display Settings
TILE_SIZE = 35
TILE_SPACING = 8
CENTER_BORDER = 20
CENTER_GRID_SIZE = 4
FACTORY_RADIUS = 75
NUM_FLOOR_TILES = 9
FLOOR_TILE_SPACING = 8
SECTION_SPACING = 10
SCORE_HEIGHT = 50
FLOOR_NUMBER_HEIGHT = 20
FONT_FILE_NAME = "pixelized"
FLOOR_FONT_SIZE = 15
MAIN_FONT_SIZE = 25
FADED_IMAGE_ALPHA = 65

# Data piping constants
CURRENT_BEST = "current_best"
BEST_MOVE = "best_move"
DEPTH = "depth"
EVALUATION = "evaluation"
DataType = Literal["current_best", "best_move", "depth", "evaluation"]

EMPTY = 0
BLUE = 1
YELLOW = 2
RED = 3
BLACK = 4
STAR = 5
STARTING_MARKER = 6
Tile = Literal[1, 2, 3, 4, 5]
TILE_TYPES: List[Tile] = [BLUE, YELLOW, RED, BLACK, STAR]

BYTE_CONVERSION: Dict[Union[Tile, Literal[0]], bytes] = {
    EMPTY: b"\x00",
    BLUE: b"\x01",
    YELLOW: b"\x02",
    RED: b"\x03",
    BLACK: b"\x04",
    STAR: b"\x05",
}
TILE_NAMES: Dict[Union[Tile, Literal[0, 6]], str] = {
    0: "EMPTY",
    1: "BLUE",
    2: "YELLOW",
    3: "RED",
    4: "BLACK",
    5: "STAR",
    6: "STARTING_MARKER",
}
TILE_NUMBERS: Dict[str, Union[Tile, Literal[0, 6]]] = {
    "EMPTY": 0,
    "BLUE": 1,
    "YELLOW": 2,
    "RED": 3,
    "BLACK": 4,
    "STAR": 5,
    "STARTING_MARKER": 6,
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

# Extra Information
# Stored as dictionary where the first key is the total number of tiles in the partition, and the second key is the number of partitions
# The partition itself is a dictionary with the number of tile draws of each size
PARTITIONS: Dict[int, Dict[int, List[Dict[int, int]]]] = {
    1: {1: [{1: 1}]},
    2: {1: [{2: 1}], 2: [{1: 2}]},
    3: {1: [{3: 1}], 2: [{1: 1, 2: 1}], 3: [{1: 3}]},
    4: {1: [{4: 1}], 2: [{3: 1, 1: 1}, {2: 2}], 3: [{2: 1, 1: 2}], 4: [{1: 4}]},
    5: {
        1: [{5: 1}],
        2: [{4: 1, 1: 1}, {3: 1, 2: 1}],
        3: [{3: 1, 1: 2}, {2: 2, 1: 1}],
        4: [{2: 1, 1: 3}],
        5: [{1: 5}],
    },
}
REGRESSION_CONSTANTS: List[Tuple[float, float]] = [
    (0, 1),
    (2.233, 21.77),
    (2.051, 28.61),
    (1.691, 33.85),
    (1.583, 106.5),
]

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (150, 150, 150)
COLOR_BROWN = (214, 168, 124)
COLOR_RED = (255, 0, 0)

PLAYER_WIDTH = (
    2 * WALL_SIZE * (TILE_SIZE + TILE_SPACING) - TILE_SPACING + 3 * SECTION_SPACING + 2
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

# Cleanup global variables
del Literal, List, Dict, Union
