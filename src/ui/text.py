import pygame
from core.support import resource_path


class OptionText:
    def __init__(self, text, pos, size):
        self.pos = pos
        self.selected = False
        self.screen = pygame.display.get_surface()
        path = resource_path('assets/font/SimHei.ttf')
        unselected_text = pygame.font.Font(path, size)
        selected_text = pygame.font.Font(path, int(size * 1.3))
        self.unselected_image = unselected_text.render(text, False, 'white')
        self.selected_image = selected_text.render(text, False, (255, 255, 65))
        offset_y = -self.unselected_image.get_height() * 0.3
        self.offset = pygame.math.Vector2(size * 0.5, offset_y)

    def display(self):
        if self.selected:
            self.screen.blit(self.selected_image, self.pos + self.offset)
        else:
            self.screen.blit(self.unselected_image, self.pos)


class Menu:
    def __init__(self, text_list, game_input, pos, size=50):
        self.game_input = game_input
        x, y = pos
        self.options = []
        self.selected_index = 0
        for text in text_list:
            self.options.append(OptionText(text, (x, y), size))
            y += size * 1.5
        self.screen = pygame.display.get_surface()
        self.tip = self.get_tip_surf('A 确认')
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
        for index, option in enumerate(self.options):
            option.selected = self.selected_index == index
            option.display()
        self.screen.blit(self.tip, self.tip_pos)

    def handle_input(self):
        for device_info in self.game_input.controllers.values():
            ctrl = device_info['controller']
            if not device_info['timer'].active:
                if ctrl.performed('up') and self.selected_index > 0:
                    self.selected_index -= 1
                    device_info['timer'].activate()
                elif ctrl.performed('down') and self.selected_index < len(self.options) - 1:
                    self.selected_index += 1
                    device_info['timer'].activate()
                if ctrl.performed('confirm'):
                    return self.selected_index
        return -1
