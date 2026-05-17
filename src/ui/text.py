import pygame
from src.core.support import resource_path


class OptionText:
    def __init__(self, label_dict, pos, size, surface: pygame.Surface):
        self.label_dict = label_dict
        self.pos = pos
        self.selected = False
        self.screen = surface
        self.size = size
        path = resource_path('assets/font/SimHei.ttf')
        self.font_unselected = pygame.font.Font(path, size)
        self.font_selected = pygame.font.Font(path, int(size * 1.3))
        self.offset_y_factor = -0.3

    def get_text(self):
        from src.core.config import config
        lang = config.get('system', 'language')
        return self.label_dict.get(lang, self.label_dict.get('zh_CN', 'Unnamed'))

    def display(self):
        text = self.get_text()
        if self.selected:
            img = self.font_selected.render(text, False, (255, 255, 65))
            offset = pygame.math.Vector2(self.size * 0.5, img.get_height() * self.offset_y_factor)
            self.screen.blit(img, self.pos + offset)
        else:
            img = self.font_unselected.render(text, False, 'white')
            self.screen.blit(img, self.pos)


class Menu:
    def __init__(self, label_list, game_input, pos, surface: pygame.Surface, size=50):
        # label_list: list of label_dicts [{'zh_CN': '...', 'en_US': '...'}, ...]
        self.game_input = game_input
        x, y = pos
        self.options = []
        self.selected_index = 0
        self.screen = surface
        for label_dict in label_list:
            self.options.append(OptionText(label_dict, (x, y), size, self.screen))
            y += size * 1.5
        
        self.update_tip()

    def get_tip_text(self):
        from src.core.config import config
        lang = config.get('system', 'language')
        return 'A 确认' if lang == 'zh_CN' else 'A CONFIRM'

    def update_tip(self):
        self.tip = self.get_tip_surf(self.get_tip_text())
        self.tip_pos = 150, 680

    @staticmethod
    def get_tip_surf(text):
        path = resource_path('assets/font/SimHei.ttf')
        font = pygame.font.Font(path, 30)
        tip_surf = font.render(text, False, 'white')
        size = tip_surf.get_rect().inflate(20, 20).size
        surf = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.circle(surf, 'green', (20, 20), 20, 5)
        surf.blit(tip_surf, (13, 5))
        return surf

    def display(self):
        self.update_tip() # 实时更新提示语言
        for index, option in enumerate(self.options):
            option.selected = self.selected_index == index
            option.display()
        self.screen.blit(self.tip, self.tip_pos)

    def handle_input(self):
        for instance_id, device_info in self.game_input.controllers.items():
            ctrl = device_info['controller']
            if not device_info['timer'].active:
                if ctrl.nav_performed('up') and self.selected_index > 0:
                    self.selected_index -= 1
                    device_info['timer'].activate()
                elif ctrl.nav_performed('down') and self.selected_index < len(self.options) - 1:
                    self.selected_index += 1
                    device_info['timer'].activate()
                if ctrl.performed('confirm'):
                    return self.selected_index, instance_id
        return -1, None
