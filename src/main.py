import sys
import pygame

from src.ui.components.dialogue import Dialogue
from src.core.input import GameInput
from src.scenes.level import Level
from src.scenes.scene import SceneStatus, Home, RolePicker, Settings
from src.settings import *


class Game:
    def __init__(self):
        pygame.init()
        # 尝试禁用文本输入模式，减少输入法(IME)干扰
        try:
            pygame.key.stop_text_input()
        except:
            pass

        # 实际的 OS 窗口
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        # 内部逻辑画布 (始终固定在 1280x720)
        self.display_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_NAME)
        self.clock = pygame.time.Clock()
        self.game_input = GameInput()
        self.current_scene = SceneStatus.UNDEFINED
        self.next_scene = SceneStatus.HOME
        self.scene = None
        self.dialogue = Dialogue(self.game_input, self.display_surf)

    def run(self):
        while self.next_scene != SceneStatus.EXIT:

            dt = self.clock.tick(60) / 1000
            if self.next_scene != self.current_scene:
                # 销毁旧场景
                if self.scene:
                    self.scene.de_init()
                # 创建新场景，传入逻辑画布
                if self.next_scene == SceneStatus.HOME:
                    self.scene = Home(self.game_input, self.display_surf)
                elif self.next_scene == SceneStatus.CHOOSE_ROLE:
                    self.scene = RolePicker(self.game_input, self.display_surf)
                elif self.next_scene == SceneStatus.FIGHTING:
                    self.scene = Level(self.game_input, self.display_surf)
                elif self.next_scene == SceneStatus.SETTINGS:
                    self.scene = Settings(self.game_input, self.display_surf)

                # 更新场景状态
                self.current_scene = self.next_scene

            # 1. 在逻辑画布上进行绘制
            self.display_surf.fill('black')
            if not self.dialogue.showing:
                self.next_scene = self.scene.run(dt)
            
            # 处理对话框
            if self.dialogue.run():
                self.next_scene = SceneStatus.EXIT

            # 2. 将逻辑画布等比例缩放到实际窗口
            window_w, window_h = self.window.get_size()
            # 计算缩放比例，保持 16:9
            scale = min(window_w / SCREEN_WIDTH, window_h / SCREEN_HEIGHT)
            new_size = (int(SCREEN_WIDTH * scale), int(SCREEN_HEIGHT * scale))
            
            # 缩放逻辑画布
            scaled_surf = pygame.transform.smoothscale(self.display_surf, new_size)
            
            # 居中绘制到窗口，多余部分自动留黑边
            self.window.fill('black')
            dest_rect = scaled_surf.get_rect(center=(window_w // 2, window_h // 2))
            self.window.blit(scaled_surf, dest_rect)

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
