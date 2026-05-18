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
        # 全局对话框 (仅用于点击窗口 X 按钮的强行退出)
        self.dialogue = Dialogue(self.game_input, self.display_surf)

    def run(self):
        while self.next_scene != SceneStatus.EXIT:

            dt = self.clock.tick(60) / 1000
            
            # 1. 场景切换逻辑
            if self.next_scene != self.current_scene:
                if self.scene:
                    self.scene.de_init()
                if self.next_scene == SceneStatus.HOME:
                    self.scene = Home(self.game_input, self.display_surf)
                elif self.next_scene == SceneStatus.CHOOSE_ROLE:
                    self.scene = RolePicker(self.game_input, self.display_surf)
                elif self.next_scene == SceneStatus.FIGHTING:
                    self.scene = Level(self.game_input, self.display_surf)
                elif self.next_scene == SceneStatus.SETTINGS:
                    self.scene = Settings(self.game_input, self.display_surf)
                self.current_scene = self.next_scene

            # 2. 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # 点击窗口关闭按钮，默认由键盘设备处理
                    self.dialogue.show('确定要退出吗？', self.game_input.controllers[-1])
                self.game_input.update(event)
            
            # 持续更新输入状态 (处理长按计时等)
            self.game_input.update_timers(dt)

            # 3. 渲染流程：
            # A. 清空画布
            self.display_surf.fill('black')
            
            # B. 检查是否有弹窗显示 (全局或场景内部)
            scene_dialogue_showing = hasattr(self.scene, 'dialogue') and self.scene.dialogue.showing
            is_paused = self.dialogue.showing or scene_dialogue_showing
            
            # C. 绘制场景层 (传入 dt=0 实现暂停效果)
            # 即使在暂停状态下，也要运行场景逻辑以保持渲染
            res = self.scene.run(0 if is_paused else dt)
            
            # 核心修复：无论是否处于暂停状态，如果场景返回了非当前场景的状态，必须立刻响应
            if res != self.current_scene:
                self.next_scene = res
            
            # D. 处理全局弹窗层 (仅处理窗口关闭请求)
            if self.dialogue.showing:
                if self.dialogue.run():
                    self.next_scene = SceneStatus.EXIT

            # 4. 最终渲染到实际窗口
            window_w, window_h = self.window.get_size()
            scale = min(window_w / SCREEN_WIDTH, window_h / SCREEN_HEIGHT)
            new_size = (int(SCREEN_WIDTH * scale), int(SCREEN_HEIGHT * scale))
            scaled_surf = pygame.transform.smoothscale(self.display_surf, new_size)
            
            self.window.fill('black')
            dest_rect = scaled_surf.get_rect(center=(window_w // 2, window_h // 2))
            self.window.blit(scaled_surf, dest_rect)

            pygame.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()
