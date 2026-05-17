import pygame

from src.ui.components.dialogue import Dialogue
from src.entities.player import Player
from src.scenes.scene import Scene, SceneStatus
from src.entities.sprites import DynamicBackGround


class Level(Scene):
    def __init__(self, game_input, surface: pygame.Surface):
        super().__init__(game_input, surface)
        self.dialogue = Dialogue(game_input, self.screen)
        self.display_sprites = pygame.sprite.Group()
        self.create_player()
        DynamicBackGround(self.display_sprites)

    def create_player(self):
        for info in self.game_input.controllers.values():
            if info['player_index'] != 'p0':
                Player(info, self.display_sprites, self.dialogue, self.screen)

    def run(self, dt):
        # 1. 始终渲染场景内容
        for sprite in sorted(self.display_sprites, key=lambda item: item.rect.y):
            # 如果 dialogue 显示，传入 dt=0 使其静止，否则正常更新
            sprite.update(0 if self.dialogue.showing else dt)
            self.screen.blit(sprite.image, sprite.rect)

        # 2. 处理场景内部弹窗
        if self.dialogue.showing:
            if self.dialogue.run():
                self.game_input.home_menu_index = 0
                return SceneStatus.HOME
        else:
            # 监听系统级退出请求 (ESC 或 手柄菜单键)
            # 使用 ui_performed 确保这些键不受玩家战斗设置影响
            for instance_id, device_info in self.game_input.controllers.items():
                ctrl = device_info['controller']
                if ctrl.ui_performed('cancel') or ctrl.ui_performed('menu'):
                    from src.core.config import config
                    lang = config.get('system', 'language')
                    msg = '确定要退出游戏吗？' if lang == 'zh_CN' else 'Quit match?'
                    self.dialogue.show(msg, device_info)
                    
        return SceneStatus.FIGHTING

    def de_init(self):
        self.game_input.reset()
