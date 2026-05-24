import os.path

import pygame
from enum import Enum

from src.ui.components.dialogue import Dialogue
from src.core.input import GameInput
from src.core.support import import_folder_dict, resource_path, import_pic, import_gif
from src.settings import *
from src.ui.text import Menu
from src.core.timer import Timer
from src.ui.ui import Particles
from src.ui.components.widgets import Slider, Selector, KeyBinder, Button, Toggle, Header
from src.core.config import config
from src.core.logger import logger
import src.settings as settings


class SceneStatus(Enum):
    UNDEFINED = 0
    HOME = 1
    CHOOSE_ROLE = 2
    CHOOSE_BACKGROUND = 3
    FIGHTING = 4
    SETTINGS = 5
    EXIT = 6


class Scene:
    def __init__(self, game_input: GameInput, surface: pygame.Surface):
        self.screen = surface
        self.game_input = game_input

    def run(self, dt) -> SceneStatus:
        pass

    def de_init(self):
        pass


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
            elif index == 0: return SceneStatus.CHOOSE_ROLE
            elif index == 3:
                self.game_input.last_active_id = instance_id
                self.game_input.home_menu_index = index
                return SceneStatus.SETTINGS
        return SceneStatus.HOME


class Settings(Scene):
    def __init__(self, game_input: GameInput, surface: pygame.Surface):
        super().__init__(game_input, surface)
        background = import_pic('assets/graphics/background/background_blurred.png')
        self.image = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        self.panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 400, 80, 800, 560)
        self.panel_surf = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
        self.panel_surf.fill((0, 0, 0, 240))
        
        self.box_padding = 40 
        self.content_box_rect = pygame.Rect(self.panel_rect.x + 40, self.panel_rect.y + 95, 720, 360)
        
        self.active_id = getattr(game_input, 'last_active_id', -1)
        self.is_joystick = (self.active_id != -1)
        
        path = resource_path('assets/font/SimHei.ttf')
        self.font_tab = pygame.font.Font(path, 18) 
        self.font_hint = pygame.font.Font(path, 18)
        
        self.tabs = [
            {'id': 'system', 'label': {'zh_CN': '系统设定', 'en_US': 'SYSTEM'}},
            {'id': 'audio', 'label': {'zh_CN': '声音调节', 'en_US': 'AUDIO'}},
            {'id': 'controls', 'label': {'zh_CN': '按键映射', 'en_US': 'CONTROLS'}},
            {'id': 'advanced', 'label': {'zh_CN': '高级选项', 'en_US': 'ADVANCED'}}
        ]
        
        self.tab_scroll_y = {tab['id']: 0 for tab in self.tabs}
        self.tab_target_scroll_y = {tab['id']: 0 for tab in self.tabs}
        self.current_tab_index = getattr(game_input, 'settings_tab_index', 0)
        self.selection_index = getattr(game_input, 'settings_selection_index', 0) 
        
        self.init_widgets()
        self.timer = Timer(200) 
        self.dialogue = Dialogue(game_input, self.screen)

    def init_widgets(self):
        self.tab_widgets = {tab['id']: [] for tab in self.tabs}
        self.tab_content_heights = {tab['id']: 0 for tab in self.tabs}
        x_widget, y_start = self.content_box_rect.x + 60, self.content_box_rect.y + self.box_padding
        
        y = y_start
        self.tab_widgets['system'].append(Selector({'zh_CN': '界面语言', 'en_US': 'LANGUAGE'}, (x_widget, y), ['简体中文', 'English'], 0 if config.get('system', 'language') == 'zh_CN' else 1))
        y += 60
        self.tab_widgets['system'].append(Toggle({'zh_CN': '全屏显示', 'en_US': 'FULLSCREEN'}, (x_widget, y), config.get('graphics', 'fullscreen')))
        self.tab_content_heights['system'] = y + 40 - y_start

        y = y_start
        self.tab_widgets['audio'].extend([
            Slider({'zh_CN': '主音量', 'en_US': 'MASTER'}, (x_widget, y), config.get('volume', 'master')),
            Slider({'zh_CN': '背景音乐', 'en_US': 'MUSIC'}, (x_widget, y + 50), config.get('volume', 'music')),
            Slider({'zh_CN': '游戏音效', 'en_US': 'SFX'}, (x_widget, y + 100), config.get('volume', 'sfx')),
        ])
        self.tab_content_heights['audio'] = 140
        
        y = y_start
        dev_key = 'joystick' if self.is_joystick else 'keyboard'
        ctrl = self.game_input.controllers[self.active_id]['controller'] if self.is_joystick else None
        actions = [
            ({'zh_CN': '向上/跳跃', 'en_US': 'UP / JUMP'}, 'up'), ({'zh_CN': '向下移动', 'en_US': 'MOVE DOWN'}, 'down'),
            ({'zh_CN': '向左移动', 'en_US': 'MOVE LEFT'}, 'left'), ({'zh_CN': '向右移动', 'en_US': 'MOVE RIGHT'}, 'right'),
            ({'zh_CN': '攻击', 'en_US': 'ATTACK'}, 'attack'),
            ({'zh_CN': '技能1', 'en_US': 'SKILL 1'}, 'super move 1'), ({'zh_CN': '技能2', 'en_US': 'SKILL 2'}, 'super move 2'),
            ({'zh_CN': '终结技', 'en_US': 'FINISHER'}, 'finisher'),
        ]
        for label, aid in actions:
            self.tab_widgets['controls'].append(KeyBinder(label, (x_widget, y), config.get('controls', dev_key, aid), aid, is_joystick=self.is_joystick, controller=ctrl))
            y += 50
        self.tab_content_heights['controls'] = y - y_start
            
        y = y_start
        self.tab_widgets['advanced'].extend([Button({'zh_CN': '重置窗口', 'en_US': 'RESET WINDOW'}, (x_widget, y)), Button({'zh_CN': '恢复默认', 'en_US': 'RESTORE ALL'}, (x_widget, y + 60))])
        self.tab_content_heights['advanced'] = 105
        self._refresh_selection()

    def _refresh_selection(self):
        self.game_input.settings_tab_index, self.game_input.settings_selection_index = self.current_tab_index, self.selection_index
        active_id = self.tabs[self.current_tab_index]['id']
        for tid, widgets in self.tab_widgets.items():
            for i, w in enumerate(widgets): w.selected = (tid == active_id and i == self.selection_index)

    def run(self, dt) -> SceneStatus:
        self.screen.blit(self.image, (0, 0))
        pygame.draw.rect(self.screen, 'orange', self.panel_rect.inflate(6, 6), 1)
        self.screen.blit(self.panel_surf, self.panel_rect)
        lang = config.get('system', 'language')
        
        tx = self.panel_rect.x + 50
        for i, tab in enumerate(self.tabs):
            is_active = (i == self.current_tab_index)
            rect = (tx, self.panel_rect.y + 40, 170, 35)
            pygame.draw.rect(self.screen, 'orange' if is_active else (40, 40, 40), rect, border_radius=10)
            if not is_active: pygame.draw.rect(self.screen, (80, 80, 80), rect, 1, border_radius=10)
            txt = self.font_tab.render(tab['label'].get(lang), True, (30, 30, 30) if is_active else (150, 150, 150))
            self.screen.blit(txt, txt.get_rect(center=(tx + 85, self.panel_rect.y + 40 + 17)))
            tx += 180

        active_tab_id = self.tabs[self.current_tab_index]['id']
        aw = self.tab_widgets[active_tab_id]
        viewport_h = 360
        th = self.tab_content_heights[active_tab_id] + (self.box_padding * 2)
        
        self.content_box_rect.h = min(viewport_h, th)
        pygame.draw.rect(self.screen, (100, 100, 100), self.content_box_rect, 1, border_radius=12)
        self.tab_scroll_y[active_tab_id] += (self.tab_target_scroll_y[active_tab_id] - self.tab_scroll_y[active_tab_id]) * 0.1
        
        old_clip = self.screen.get_clip()
        self.screen.set_clip(self.content_box_rect.inflate(-20, -20))
        for w in aw: w.draw(self.screen, self.tab_scroll_y[active_tab_id])
        self.screen.set_clip(old_clip)
        
        if self.is_joystick:
            active_controller = self.game_input.controllers[self.active_id]['controller']
            l_text, r_text = active_controller.get_button_name(9), active_controller.get_button_name(10)
            conf_hint, canc_hint = active_controller.get_button_name(0), active_controller.get_button_name(1)
        else:
            l_text, r_text, conf_hint, canc_hint = "Q", "E", "⏎", "ESC"

        hints_data = [
            (f"{l_text} / {r_text}", "切换标签" if lang == 'zh_CN' else "TABS"),
            ("↑ ↓", "选择" if lang == 'zh_CN' else "SELECT"),
            ("← →", "调节" if lang == 'zh_CN' else "ADJUST"),
            (conf_hint, "确定" if lang == 'zh_CN' else "CONFIRM"),
            (canc_hint, "返回" if lang == 'zh_CN' else "BACK")
        ]
        hint_surf = Menu.get_tip_surf_multi(hints_data)
        self.screen.blit(hint_surf, (self.panel_rect.centerx - hint_surf.get_width() // 2, self.panel_rect.bottom - 45))

        if self.dialogue.showing:
            if self.dialogue.run():
                cw = self.tab_widgets[active_tab_id][self.selection_index]
                if isinstance(cw, Button):
                    label = cw.get_label()
                    if '恢复' in label or 'RESTORE' in label:
                        config.reset_to_defaults()
                        self.init_widgets()
                        self.game_input.refresh_all_maps()
                    elif '重置' in label or 'RESET' in label:
                        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                        config.set(False, 'graphics', 'fullscreen')
                        self.init_widgets()
            return SceneStatus.SETTINGS

        if dt > 0: return self.handle_input()
        return SceneStatus.SETTINGS

    def handle_input(self):
        self.timer.update()
        if self.timer.active: return SceneStatus.SETTINGS
        for iid, info in self.game_input.controllers.items():
            if iid != self.active_id: continue
            ctrl = info['controller']
            active_tab_id = self.tabs[self.current_tab_index]['id']
            aw = self.tab_widgets[active_tab_id]
            cw = aw[self.selection_index]

            if isinstance(cw, KeyBinder) and cw.waiting_for_input:
                new_val = None
                for event in self.game_input.frame_events:
                    if event.type == pygame.KEYDOWN:
                        new_val = pygame.key.name(event.key)
                    elif event.type == pygame.JOYBUTTONDOWN:
                        if event.instance_id == self.active_id:
                            new_val = event.button
                if new_val is not None:
                    cw.key, cw.waiting_for_input = new_val, False
                    config.set(new_val, 'controls', 'joystick' if self.is_joystick else 'keyboard', cw.action_id)
                    self.game_input.refresh_all_maps(); self.timer.activate()
                return SceneStatus.SETTINGS

            if ctrl.ui_performed('tab_left'): 
                self.current_tab_index = (self.current_tab_index - 1) % len(self.tabs)
                self.selection_index = 0
                self._refresh_selection(); self.timer.activate()
            elif ctrl.ui_performed('tab_right'): 
                self.current_tab_index = (self.current_tab_index + 1) % len(self.tabs)
                self.selection_index = 0
                self._refresh_selection(); self.timer.activate()
            elif ctrl.ui_performed('up') and self.selection_index > 0: 
                self.selection_index -= 1
                self._refresh_selection(); self._ensure_visible(); self.timer.activate()
            elif ctrl.ui_performed('down') and self.selection_index < len(aw) - 1: 
                self.selection_index += 1
                self._refresh_selection(); self._ensure_visible(); self.timer.activate()

            elif (ctrl.ui_performed('left') or ctrl.ui_performed('right')) and isinstance(cw, (Slider, Selector)):
                val = cw.update_value('left' if ctrl.ui_performed('left') else 'right')
                self._apply_setting(cw, val); self.timer.activate()

            elif ctrl.ui_performed('confirm'):
                if isinstance(cw, Button): self.dialogue.show("执行操作?", self.game_input.controllers[self.active_id])
                elif isinstance(cw, KeyBinder): cw.waiting_for_input = True
                elif isinstance(cw, Toggle): self._apply_setting(cw, cw.update_value())
                self.timer.activate()
            elif ctrl.ui_performed('cancel'):
                config.save()
                self.game_input.home_menu_index = 3
                return SceneStatus.HOME
        return SceneStatus.SETTINGS

    def _ensure_visible(self):
        active_tab_id = self.tabs[self.current_tab_index]['id']
        w = self.tab_widgets[active_tab_id][self.selection_index]
        th = self.tab_content_heights[active_tab_id] + (self.box_padding * 2)
        if th <= 360:
            self.tab_target_scroll_y[active_tab_id] = 0
            return
        vt, vb = self.content_box_rect.y + self.box_padding, self.content_box_rect.bottom - self.box_padding
        ry = w.pos[1] - self.tab_scroll_y[active_tab_id]
        target = self.tab_target_scroll_y[active_tab_id]
        if ry < vt: target = w.pos[1] - vt
        elif ry + w.size[1] > vb: target = w.pos[1] + w.size[1] - vb
        self.tab_target_scroll_y[active_tab_id] = max(0, min(target, th - 360))

    def _apply_setting(self, widget, value):
        l = widget.get_label()
        if '语言' in l or 'LANGUAGE' in l: config.set('en_US' if value == 'English' else 'zh_CN', 'system', 'language')
        elif '音量' in l or 'VOLUME' in l: config.set(value, 'volume', 'master' if '主' in l or 'MASTER' in l else 'music' if '音乐' in l or 'MUSIC' in l else 'sfx')
        elif '全屏' in l or 'FULLSCREEN' in l: config.set(value, 'graphics', 'fullscreen'); pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), (pygame.FULLSCREEN if value else 0) | pygame.RESIZABLE)


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
        p1_dic = next((dic for dic in self.game_input.controllers.values() if dic['player_index'] == 'p1'), None)
        RoleDetailItem(p1_dic, (gap, y, w, h), self.group, self.game_input)
        
        # P2 Slot (Right Side)
        p2_dic = next((dic for dic in self.game_input.controllers.values() if dic['player_index'] == 'p2'), None)
        RoleDetailItem(p2_dic, (gap * 2 + w, y, w, h), self.group, self.game_input)

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
        for dic in self.game_input.controllers.values():
            if dic['player_name'] == self.name:
                if i == 0: self.rect, self.image = self.scaled_global_rect, pygame.transform.scale(self.image, self.scaled_global_rect.size); self.image.fill('yellow'); self.image.blit(self.scaled_role_pic, (0, 0))
                pygame.draw.rect(self.image, self.colors[dic['player_index']], self.scaled_rect, 6); i += 1
        dics = sorted(self.game_input.controllers.values(), key=lambda d: d['player_index'])
        j = 0
        for dic in dics:
            if dic['player_name'] == self.name: self.image.blit(self.indicators[dic['player_index']], self.positions[j]); j += 1
        if i == 0: self.rect, self.image = self.normal_global_rect, pygame.transform.scale(self.image, self.normal_global_rect.size); self.image.fill('orange'); pygame.draw.rect(self.image, 'black', self.normal_rect, 2); self.image.blit(self.role_pic, (0, 0))
