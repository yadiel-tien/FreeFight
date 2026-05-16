import sys

import pygame

from ui.components.dialogue import Dialogue
from core.input import GameInput
from scenes.level import Level
from scenes.scene import SceneStatus, Home, RolePicker, Settings
from settings import *


class Game:
    def __init__(self):
        pygame.init()
        self.display_surf = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_NAME)
        self.clock = pygame.time.Clock()
        self.game_input = GameInput()
        self.current_scene = SceneStatus.UNDEFINED
        self.next_scene = SceneStatus.HOME
        self.scene = None
        self.dialogue = Dialogue(self.game_input)

    def run(self):
        while self.next_scene != SceneStatus.EXIT:

            dt = self.clock.tick(60) / 1000
            if self.next_scene != self.current_scene:
                # 销毁就场景
                if self.scene:
                    self.scene.de_init()
                # 创建新场景
                if self.next_scene == SceneStatus.HOME:
                    self.scene = Home(self.game_input)
                elif self.next_scene == SceneStatus.CHOOSE_ROLE:
                    self.scene = RolePicker(self.game_input)
                elif self.next_scene == SceneStatus.FIGHTING:
                    self.scene = Level(self.game_input)
                elif self.next_scene == SceneStatus.SETTINGS:
                    self.scene = Settings(self.game_input)

                # 更新场景状态
                self.current_scene = self.next_scene

            if not self.dialogue.showing:
                self.next_scene = self.scene.run(dt)
            # 确认退出
            if self.dialogue.run():
                self.next_scene = SceneStatus.EXIT

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.dialogue.show('确定要退出吗？')
                self.game_input.update(event)
            pygame.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()
