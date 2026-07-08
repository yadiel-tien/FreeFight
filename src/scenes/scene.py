import pygame
from enum import Enum
from src.core.input import GameInput


class SceneStatus(Enum):
    UNDEFINED = 0
    HOME = 1
    CHOOSE_ROLE = 2
    CHOOSE_BACKGROUND = 3
    FIGHTING = 4
    SETTINGS = 5
    EXIT = 6
    EDITOR = 7
    HOW_TO_PLAY = 8
    CONVERTER = 9


class Scene:
    def __init__(self, game_input: GameInput, surface: pygame.Surface):
        self.screen = surface
        self.game_input = game_input

    def run(self, dt) -> SceneStatus:
        pass

    def de_init(self):
        pass
