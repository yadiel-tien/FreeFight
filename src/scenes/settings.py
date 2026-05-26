import pygame
from src.scenes.scene import Scene, SceneStatus
from src.core.input import GameInput
from src.core.support import resource_path, import_pic
from src.core.constants import SCREEN_WIDTH, SCREEN_HEIGHT
from src.ui.text import Menu
from src.ui.components.dialogue import Dialogue
from src.ui.components.widgets import Slider, Selector, KeyBinder, Button, Toggle
from src.core.config import config
from src.core.timer import Timer


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
