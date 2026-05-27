import pygame
from src.scenes.scene import Scene, SceneStatus
from src.core.input import GameInput
from src.core.support import resource_path
from src.core.constants import SCREEN_WIDTH, SCREEN_HEIGHT
from src.ui.text import Menu
from src.ui.ui import Particles
from src.ui.components.dialogue import Dialogue
from src.core.config import config


class Home(Scene):
    def __init__(self, game_input: GameInput, surface: pygame.Surface):
        super().__init__(game_input, surface)
        image = pygame.image.load(resource_path('assets/graphics/background/background_blurred.png'))
        self.image = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.title_surf = pygame.Surface((550, 450), pygame.SRCALPHA)
        title = pygame.image.load(resource_path('assets/graphics/background/title.png'))
        self.title = pygame.transform.scale(title, (550, 450)).convert_alpha()
        self.title_surf.blit(self.title, (0, 0))
        self.menu_rect = pygame.Rect(100, 0, 200, SCREEN_HEIGHT)
        self.menu_surf = pygame.Surface(self.menu_rect.size, pygame.SRCALPHA)
        self.menu_surf.fill((0, 0, 0, 214))
        options = [
            {'zh_CN': '对战', 'en_US': 'BATTLE'},
            {'zh_CN': '操作', 'en_US': 'HOW TO PLAY'},
            {'zh_CN': '角色', 'en_US': 'CHARACTERS'},
            {'zh_CN': '选项', 'en_US': 'SETTINGS'},
            {'zh_CN': '退出', 'en_US': 'EXIT'}
        ]
        self.menu = Menu(options, game_input, (120, 200), self.screen, center_at=200, show_back=False)
        # 恢复之前的选中项
        self.menu.selected_index = getattr(game_input, 'home_menu_index', 0)
        self.sparkles = Particles(0.05, self.screen)
        self.dialogue = Dialogue(game_input, self.screen)

    def run(self, dt) -> SceneStatus:
        self.screen.blit(self.image, (0, 0))
        self.screen.blit(self.menu_surf, self.menu_rect)
        self.sparkles.update(dt)
        self.menu.display()
        self.screen.blit(self.title_surf, (500, 250))

        if self.dialogue.showing:
            if self.dialogue.run():
                return SceneStatus.EXIT
            return SceneStatus.HOME

        if dt > 0:
            return self.handle_input()
        return SceneStatus.HOME

    def handle_input(self) -> SceneStatus:
        # 快捷键：在主界面按 B (Cancel) 直接跳转到退出选项
        # 移入 handle_input 以保证和普通输入逻辑一致，避免“按键穿透”
        for device_info in self.game_input.controllers.values():
            ctrl = device_info['controller']
            if not device_info['timer'].active:
                if ctrl.ui_performed('cancel'):
                    self.menu.selected_index = len(self.menu.options) - 1
                    device_info['timer'].activate()

        res = self.menu.handle_input()
        if res[0] != -1:
            index, instance_id = res
            if index == 4:
                lang = config.get('system', 'language')
                msg = '确定要退出吗？' if lang == 'zh_CN' else 'Are you sure you want to quit?'
                self.dialogue.show(msg, self.game_input.controllers[instance_id])
            elif index == 0:
                self.game_input.last_active_id = instance_id
                self.game_input.home_menu_index = index
                return SceneStatus.CHOOSE_ROLE
            elif index == 1:
                self.game_input.last_active_id = instance_id
                self.game_input.home_menu_index = index
                return SceneStatus.HOW_TO_PLAY
            elif index == 2:
                self.game_input.last_active_id = instance_id
                self.game_input.home_menu_index = index
                return SceneStatus.EDITOR
            elif index == 3:
                self.game_input.last_active_id = instance_id
                self.game_input.home_menu_index = index
                return SceneStatus.SETTINGS
        return SceneStatus.HOME
