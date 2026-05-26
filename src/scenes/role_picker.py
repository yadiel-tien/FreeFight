import os
import pygame
from src.scenes.scene import Scene, SceneStatus
from src.core.input import GameInput
from src.core.support import resource_path, import_pic, import_folder_dict, import_gif
from src.core.constants import SCREEN_WIDTH, SCREEN_HEIGHT
from src.ui.text import Menu
from src.ui.ui import Particles
from src.ui.components.dialogue import Dialogue
from src.core.config import config
from src.core.timer import Timer


class RolePicker(Scene):
    def __init__(self, game_input: GameInput, surface: pygame.Surface):
        super().__init__(game_input, surface)
        background = import_pic('assets/graphics/background/background_blurred.png')
        self.image = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.bar_rect = pygame.Rect(0, SCREEN_HEIGHT - 240, SCREEN_WIDTH, 180)
        self.bar = pygame.Surface(self.bar_rect.size, pygame.SRCALPHA)
        self.bar.fill((0, 0, 0, 214))
        self.role_menu = RoleMenu(self.game_input, self.screen)
        self.role_details = RoleDetailModule(self.game_input, self.screen)
        self.image.blit(self.bar, self.bar_rect)
        self.particles = Particles(0.05, self.screen)
        self.timer = Timer(100, lambda: setattr(self, 'start', True))
        self.start = False

    def handle_input(self):
        for iid, info in self.game_input.controllers.items():
            ctrl, cp, t = info['controller'], info['player_name'], info['timer']
            if info['player_index'] != 'p0':
                if not t.active and not info['confirmed']:
                    if ctrl.ui_performed('left'): info['player_name'] = self.role_menu.previous(cp); t.activate()
                    elif ctrl.ui_performed('right'): info['player_name'] = self.role_menu.next(cp); t.activate()
                if ctrl.ui_performed('confirm'):
                    info['confirmed'] = True
                    if self.game_input.ready_to_start(): self.timer.activate()
                if self.start: return SceneStatus.FIGHTING
                if ctrl.ui_performed('cancel') and not self.timer.active:
                    if info['confirmed']: info['confirmed'] = False
                    else: self.game_input.leave(iid); self.role_details.create_details()
            elif self.game_input.joinable:
                if ctrl.ui_performed('confirm'): self.game_input.join(iid, self.role_menu.available()); self.role_details.create_details()
                if ctrl.ui_performed('cancel') and self.game_input.joined_count() == 0:
                    self.game_input.home_menu_index = 0
                    return SceneStatus.HOME
        return SceneStatus.CHOOSE_ROLE

    def run(self, dt) -> SceneStatus:
        self.timer.update()
        self.screen.blit(self.image, (0, 0))
        self.particles.update(dt)
        self.role_menu.update()
        self.role_details.update(dt)
        if dt > 0: return self.handle_input()
        return SceneStatus.CHOOSE_ROLE


class RoleDetailModule:
    def __init__(self, game_input: GameInput, screen: pygame.Surface):
        self.group = pygame.sprite.Group()
        self.game_input, self.screen = game_input, screen
        self.create_details()

    def create_details(self):
        self.group.empty()
        w, h = 320, 420
        y = 40
        gap = (SCREEN_WIDTH - w * 2) // 3  # (1280 - 640) // 3 = 213
        
        # P1 Slot (Left Side)
        p1_info = next((info for info in self.game_input.controllers.values() if info['player_index'] == 'p1'), None)
        RoleDetailItem(p1_info, (gap, y, w, h), self.group, self.game_input)
        
        # P2 Slot (Right Side)
        p2_info = next((info for info in self.game_input.controllers.values() if info['player_index'] == 'p2'), None)
        RoleDetailItem(p2_info, (gap * 2 + w, y, w, h), self.group, self.game_input)

    def update(self, dt):
        self.group.update(dt); self.group.draw(self.screen)


class RoleDetailItem(pygame.sprite.Sprite):
    def __init__(self, device_info, rect: tuple, groups: pygame.sprite.Group, game_input: GameInput = None):
        super().__init__(groups)
        self.device_info, self.name = device_info, ''
        self.half_length, self.full_length_pics, self.full_length_index, self.full_length_pic = None, None, 0, None
        self.indicators = import_folder_dict('assets/graphics/icons/indicator')
        self.check_icon = pygame.transform.scale(import_pic('assets/graphics/icons/check.png'), (60, 60))
        self.earth_icon = import_pic('assets/graphics/icons/earth.png')
        self.update_player_pics()
        self.rect = pygame.Rect(rect)
        self.alpha_background, self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA), pygame.Surface(self.rect.size, pygame.SRCALPHA)
        lang = config.get('system', 'language')
        if self.device_info:
            ctrl = self.device_info['controller']
            if hasattr(ctrl, 'get_button_name'): hint = ctrl.get_button_name(0)
            else: hint = "⏎"
        elif game_input:
            available_hints = []
            for d in game_input.controllers.values():
                if d['player_index'] == 'p0':
                    c = d['controller']
                    if hasattr(c, 'get_button_name'): available_hints.append(c.get_button_name(0))
                    else: available_hints.append("⏎")
            hint = " / ".join(sorted(list(set(available_hints)))) if available_hints else "---"
        else: hint = "⏎"
        self.text_surf = Menu.get_tip_surf(hint, '加入游戏' if lang == 'zh_CN' else 'JOIN')
        t_rect = self.text_surf.get_rect(midbottom=self.rect.midbottom).move(0, -50)
        self.text_offset = t_rect.x - self.rect.x, t_rect.y - self.rect.y

    def update_player_pics(self):
        self.name = self.device_info['player_name'] if self.device_info else 'unselected'
        if self.name == 'unselected': self.half_length, self.full_length_pics = self.earth_icon, None
        else: self.half_length, self.full_length_pics = import_pic(f'assets/graphics/sprites/{self.name}/half_length.png'), import_gif(f'assets/graphics/sprites/{self.name}/idle.gif')

    def update(self, dt):
        self.update_player_pics()
        self.image.fill((0, 0, 0, 0))
        self.alpha_background.fill('orange' if self.device_info and self.device_info['confirmed'] else 'black')
        self.alpha_background.set_alpha(214 if self.device_info and self.device_info['confirmed'] else 114)
        self.alpha_background.blit(pygame.transform.scale(self.half_length, self.rect.size), (0, 0))
        self.image.blit(self.alpha_background, (0, 0))
        if self.name != 'unselected':
            if self.full_length_pics:
                self.full_length_index = (self.full_length_index + dt * 4) % len(self.full_length_pics)
                self.full_length_pic = pygame.transform.flip(self.full_length_pics[int(self.full_length_index)], True, False)
                f_rect = self.rect.scale_by(0.7); f_rect.midbottom = self.rect.midbottom
                self.image.blit(pygame.transform.scale(self.full_length_pic, f_rect.size), (f_rect.x - self.rect.x, f_rect.y - self.rect.y))
            if self.device_info:
                size = self.rect.w * 0.25
                self.image.blit(pygame.transform.scale(self.indicators[self.device_info['player_index']], (size, size)), (0, self.rect.h - size))
                if self.device_info['confirmed']: self.image.blit(self.check_icon, (self.rect.w - 60, self.rect.h - 60))
        else: self.image.blit(self.text_surf, self.text_offset)


class RoleMenu:
    def __init__(self, game_input: GameInput, surface: pygame.Surface):
        self.group, self.game_input, self.screen = pygame.sprite.Group(), game_input, surface
        self.names = [d for d in os.listdir(resource_path('assets/graphics/sprites')) if not d.startswith('.')]
        w, x, y = len(self.names) * 110, (SCREEN_WIDTH - len(self.names) * 110) // 2, 500
        for name in self.names: RoleOption(name, (x, y), self.game_input, self.group); x += 110
    def update(self) -> None: self.group.update(); self.group.draw(self.screen)
    def available(self) -> str:
        for name in self.names:
            if all(ctrl['player_name'] != name for ctrl in self.game_input.controllers.values()): return name
    def next(self, name: str) -> str: return self.names[min(len(self.names)-1, self.names.index(name)+1)]
    def previous(self, name: str) -> str: return self.names[max(0, self.names.index(name)-1)]


class RoleOption(pygame.sprite.Sprite):
    def __init__(self, name: str, pos: tuple, game_input: GameInput, groups: pygame.sprite.Group):
        super().__init__(groups)
        self.name, self.game_input = name, game_input
        self.original = import_pic(f'assets/graphics/sprites/{name}/headshot.png')
        self.indicators = import_folder_dict('assets/graphics/icons/indicator')
        self.normal_rect, self.scaled_rect = pygame.Rect((0, 0, 100, 250)), pygame.Rect((0, 0, 100, 250)).scale_by(1.05)
        self.normal_global_rect, self.scaled_global_rect = self.normal_rect.move(pos), self.normal_rect.move(pos).scale_by(1.05)
        self.role_pic, self.scaled_role_pic = pygame.transform.scale(self.original, self.normal_rect.size), pygame.transform.scale(self.original, self.scaled_rect.size)
        self.colors, self.positions = {'p1': 'green', 'p2': 'cyan', 'p3': 'purple', 'p4': 'magenta'}, [(0, 0), (65, 0), (0, 220), (65, 220)]
        self.image, self.rect = pygame.surface.Surface(self.normal_rect.size), None
    def update(self) -> None:
        i = 0
        for info in self.game_input.controllers.values():
            if info['player_name'] == self.name:
                if i == 0: self.rect, self.image = self.scaled_global_rect, pygame.transform.scale(self.image, self.scaled_global_rect.size); self.image.fill('yellow'); self.image.blit(self.scaled_role_pic, (0, 0))
                pygame.draw.rect(self.image, self.colors[info['player_index']], self.scaled_rect, 6); i += 1
        sorted_controllers = sorted(self.game_input.controllers.values(), key=lambda d: d['player_index'])
        j = 0
        for info in sorted_controllers:
            if info['player_name'] == self.name: self.image.blit(self.indicators[info['player_index']], self.positions[j]); j += 1
        if i == 0: self.rect, self.image = self.normal_global_rect, pygame.transform.scale(self.image, self.normal_global_rect.size); self.image.fill('orange'); pygame.draw.rect(self.image, 'black', self.normal_rect, 2); self.image.blit(self.role_pic, (0, 0))
