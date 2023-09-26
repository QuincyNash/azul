from constants import *
from typing import NamedTuple, Union, Literal, Dict
from dataclasses import dataclass
import pygame


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
        faded_image.set_alpha(65)

        images[tile] = TileImage(faded=faded_image, normal=image)

    return GraphicsInfo(canvas, clock, floor_font, main_font, images)
