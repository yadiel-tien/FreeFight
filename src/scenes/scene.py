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
        # 背景图
        image = pygame.image.load(resource_path('assets/graphics/background/background_blurred.png'))
        self.image = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        # 文字半透明背景
        self.title_surf = pygame.Surface((550, 450), pygame.SRCALPHA)
        title = pygame.image.load(resource_path('assets/graphics/background/title.png'))
        self.title = pygame.transform.scale(title, (550, 450)).convert_alpha()
        self.title_surf.blit(self.title, (0, 0))
        # 菜单背景
        self.menu_rect = pygame.Rect(100, 0, 200, SCREEN_HEIGHT)
        self.menu_surf = pygame.Surface(self.menu_rect.size, pygame.SRCALPHA)
        self.menu_surf.fill((0, 0, 0, 214))
        # 菜单
        options = [
            {'zh_CN': '对战', 'en_US': 'BATTLE'},
            {'zh_CN': '操作', 'en_US': 'HOW TO PLAY'},
            {'zh_CN': '角色', 'en_US': 'CHARACTERS'},
            {'zh_CN': '选项', 'en_US': 'SETTINGS'},
            {'zh_CN': '退出', 'en_US': 'EXIT'}
        ]
        self.menu = Menu(options, game_input, (120, 200), self.screen, center_at=200, show_back=False)
        # 粒子
        self.sparkles = Particles(0.05, self.screen)

        self.dialogue = Dialogue(game_input, self.screen)

    def run(self, dt) -> SceneStatus:
        if self.dialogue.showing:
            if self.dialogue.run():
                return SceneStatus.EXIT
        else:
            self.screen.blit(self.image, (0, 0))
            self.screen.blit(self.menu_surf, self.menu_rect)
            self.sparkles.update(dt)
            self.menu.display()
            self.screen.blit(self.title_surf, (500, 250))

            res = self.menu.handle_input()
            if res[0] != -1:
                index, instance_id = res
                if index == 4:
                    lang = config.get('system', 'language')
                    msg = '确定要退出吗？' if lang == 'zh_CN' else 'Are you sure you want to quit?'
                    self.dialogue.show(msg)
                elif index == 0:
                    return SceneStatus.CHOOSE_ROLE
                elif index == 3:
                    # 记录是哪个设备触发了设置
                    self.game_input.last_active_id = instance_id
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
        
        # 滚动相关
        self.scroll_y = 0
        self.target_scroll_y = 0
        self.max_scroll_y = 0
        
        # 加载字体
        path = resource_path('assets/font/SimHei.ttf')
        self.font_tab = pygame.font.Font(path, 18) 
        self.font_hint = pygame.font.Font(path, 18)
        
        # 标签定义
        self.tabs = [
            {'id': 'system', 'label': {'zh_CN': '系统设定', 'en_US': 'SYSTEM'}},
            {'id': 'audio', 'label': {'zh_CN': '声音调节', 'en_US': 'AUDIO'}},
            {'id': 'controls', 'label': {'zh_CN': '按键映射', 'en_US': 'CONTROLS'}},
            {'id': 'advanced', 'label': {'zh_CN': '高级选项', 'en_US': 'ADVANCED'}}
        ]
        self.current_tab_index = 0
        
        # 始终聚焦在内容区
        self.selection_index = 0 
        
        self.init_widgets()
        self.timer = Timer(200) 
        self.dialogue = Dialogue(game_input, self.screen)

    def init_widgets(self):
        self.tab_widgets = {tab['id']: [] for tab in self.tabs}
        self.tab_selection_indices = {tab['id']: 0 for tab in self.tabs}
        self.tab_content_heights = {tab['id']: 0 for tab in self.tabs}
        
        x_widget = self.content_box_rect.x + 60
        y_start_base = self.content_box_rect.y + self.box_padding
        
        # --- 标签1：系统 ---
        y = y_start_base
        self.tab_widgets['system'].append(Selector({'zh_CN': '界面语言', 'en_US': 'LANGUAGE'}, (x_widget, y), ['简体中文', 'English'], 
                                   0 if config.get('system', 'language') == 'zh_CN' else 1))
        y += 60
        self.tab_widgets['system'].append(Toggle({'zh_CN': '全屏显示', 'en_US': 'FULLSCREEN'}, (x_widget, y), config.get('graphics', 'fullscreen')))
        y += 40
        self.tab_content_heights['system'] = y - y_start_base

        # --- 标签2：音频 ---
        y = y_start_base
        self.tab_widgets['audio'].extend([
            Slider({'zh_CN': '主音量', 'en_US': 'MASTER'}, (x_widget, y), config.get('volume', 'master')),
            Slider({'zh_CN': '背景音乐', 'en_US': 'MUSIC'}, (x_widget, y + 50), config.get('volume', 'music')),
            Slider({'zh_CN': '游戏音效', 'en_US': 'SFX'}, (x_widget, y + 100), config.get('volume', 'sfx')),
        ])
        y += 140
        self.tab_content_heights['audio'] = y - y_start_base
        
        # --- 标签3：按键 ---
        y = y_start_base
        device_key = 'joystick' if self.is_joystick else 'keyboard'
        active_controller = self.game_input.controllers[self.active_id]['controller'] if self.is_joystick else None
        actions = [
            ({'zh_CN': '向上移动', 'en_US': 'MOVE UP'}, 'up'),
            ({'zh_CN': '向下移动', 'en_US': 'MOVE DOWN'}, 'down'),
            ({'zh_CN': '向左移动', 'en_US': 'MOVE LEFT'}, 'left'),
            ({'zh_CN': '向右移动', 'en_US': 'MOVE RIGHT'}, 'right'),
            ({'zh_CN': '跳跃', 'en_US': 'JUMP'}, 'jump'),
            ({'zh_CN': '攻击', 'en_US': 'ATTACK'}, 'attack'),
            ({'zh_CN': '技能1', 'en_US': 'SKILL 1'}, 'super move 1'),
            ({'zh_CN': '技能2', 'en_US': 'SKILL 2'}, 'super move 2'),
            ({'zh_CN': '终结技', 'en_US': 'FINISHER'}, 'finisher'),
        ]
        for label_dict, action_id in actions:
            current_val = config.get('controls', device_key, action_id)
            self.tab_widgets['controls'].append(KeyBinder(label_dict, (x_widget, y), current_val, action_id, 
                                               is_joystick=self.is_joystick, controller=active_controller))
            y += 50
        self.tab_content_heights['controls'] = y - y_start_base
            
        # --- 标签4：高级 ---
        y = y_start_base
        self.tab_widgets['advanced'].extend([
            Button({'zh_CN': '重置窗口大小', 'en_US': 'RESET WINDOW'}, (x_widget, y)),
            Button({'zh_CN': '恢复默认设置', 'en_US': 'RESTORE ALL'}, (x_widget, y + 60))
        ])
        y += 105
        self.tab_content_heights['advanced'] = y - y_start_base

        self._refresh_selection()

    def _refresh_selection(self):
        active_tab_id = self.tabs[self.current_tab_index]['id']
        for tab_id, widgets in self.tab_widgets.items():
            for i, w in enumerate(widgets):
                w.selected = (tab_id == active_tab_id and i == self.selection_index)

    @property
    def widgets(self):
        return self.tab_widgets[self.tabs[self.current_tab_index]['id']]

    def run(self, dt) -> SceneStatus:
        if self.dialogue.showing:
            res = self.dialogue.run()
            if res:
                current_widget = self.widgets[self.selection_index]
                if current_widget.get_label().startswith(('恢复', 'RESTORE')):
                    config.reset_to_defaults()
                    self.init_widgets()
                    self.game_input.refresh_all_maps()
                elif current_widget.get_label().startswith(('重置', 'RESET')):
                    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
            return SceneStatus.SETTINGS

        self.screen.blit(self.image, (0, 0))
        
        # 1. 绘制面板
        pygame.draw.rect(self.screen, 'orange', self.panel_rect.inflate(6, 6), 1)
        self.screen.blit(self.panel_surf, self.panel_rect)
        
        # 2. 标签栏 (圆角矩形)
        lang = config.get('system', 'language')
        tab_x = self.panel_rect.x + 50
        tab_w = 170
        tab_h = 35
        for i, tab in enumerate(self.tabs):
            tab_text = tab['label'].get(lang)
            is_active = (i == self.current_tab_index)
            rect = (tab_x, self.panel_rect.y + 40, tab_w, tab_h)
            if is_active:
                pygame.draw.rect(self.screen, 'orange', rect, border_radius=10)
                text_color = (30, 30, 30)
            else:
                pygame.draw.rect(self.screen, (40, 40, 40), rect, border_radius=10)
                pygame.draw.rect(self.screen, (80, 80, 80), rect, 1, border_radius=10)
                text_color = (150, 150, 150)
            txt_surf = self.font_tab.render(tab_text, True, text_color)
            txt_rect = txt_surf.get_rect(center=(tab_x + tab_w // 2, self.panel_rect.y + 40 + tab_h // 2))
            self.screen.blit(txt_surf, txt_rect)
            tab_x += tab_w + 10

        # 3. 动态方框高度计算
        active_tab_id = self.tabs[self.current_tab_index]['id']
        active_widgets = self.tab_widgets[active_tab_id]
        max_box_h = 360
        total_needed_h = self.tab_content_heights[active_tab_id] + (self.box_padding * 2)
        box_h = min(max_box_h, total_needed_h)
        self.content_box_rect.h = box_h
        pygame.draw.rect(self.screen, (100, 100, 100), self.content_box_rect, 1, border_radius=12)
        
        # 4. 滚动内容
        self.scroll_y += (self.target_scroll_y - self.scroll_y) * 0.1
        self.max_scroll_y = max(0, total_needed_h - box_h)
        
        old_clip = self.screen.get_clip()
        clip_rect = self.content_box_rect.inflate(-20, -20)
        self.screen.set_clip(clip_rect)
        for widget in active_widgets:
            widget.draw(self.screen, self.scroll_y)
        self.screen.set_clip(old_clip)
        
        # 5. 绘制底部提示
        if self.is_joystick:
            active_controller = self.game_input.controllers[self.active_id]['controller']
            l_text = "L1" if active_controller.type == 'ps' else "L" if active_controller.type == 'nintendo' else "LB"
            r_text = "R1" if active_controller.type == 'ps' else "R" if active_controller.type == 'nintendo' else "RB"
            confirm_hint = active_controller.get_button_name(0)
        else:
            l_text, r_text = "Q", "E"
            confirm_hint = "⏎"

        tab_hint = f"{l_text} {r_text}"
        esc_hint = "ESC"
        
        # 使用 Menu 的多项渲染逻辑来保持一致
        hints_data = [
            (tab_hint, "切换标签" if lang == 'zh_CN' else "TABS"),
            ("↑ ↓", "选择" if lang == 'zh_CN' else "SELECT"),
            (confirm_hint, "确定" if lang == 'zh_CN' else "CONFIRM"),
            ("← →", "调节" if lang == 'zh_CN' else "ADJUST"),
            (esc_hint, "返回" if lang == 'zh_CN' else "BACK")
        ]
        
        hint_surf = Menu.get_tip_surf_multi(hints_data)
        # 在设置面板底部水平居中
        hint_pos = (self.panel_rect.centerx - hint_surf.get_width() // 2, self.panel_rect.bottom - 45)
        self.screen.blit(hint_surf, hint_pos)

        return self.handle_input()

    def handle_input(self):
        self.timer.update()
        if self.timer.active: return SceneStatus.SETTINGS

        for instance_id, device_info in self.game_input.controllers.items():
            ctrl = device_info['controller']
            
            active_tab_id = self.tabs[self.current_tab_index]['id']
            active_widgets = self.tab_widgets[active_tab_id]
            current_widget = active_widgets[self.selection_index]
            
            # 按键绑定模式 (独占输入)
            if isinstance(current_widget, KeyBinder) and current_widget.waiting_for_input:
                if instance_id != self.active_id and self.active_id != -1:
                    continue # 只有激活设备能改键
                
                device_key = 'joystick' if self.is_joystick else 'keyboard'
                new_val = None
                for event in pygame.event.get(pygame.KEYDOWN):
                    new_val = pygame.key.name(event.key)
                for event in pygame.event.get(pygame.JOYBUTTONDOWN):
                    if event.instance_id == self.active_id:
                        new_val = event.button
                if new_val is not None:
                    conflict_action = self._check_key_conflict(device_key, new_val, current_widget.action_id)
                    if conflict_action:
                        config.set(None, 'controls', device_key, conflict_action)
                        config.set(new_val, 'controls', device_key, current_widget.action_id)
                        self.init_widgets()
                    else:
                        current_widget.key = new_val
                        config.set(new_val, 'controls', device_key, current_widget.action_id)
                    
                    self.game_input.refresh_all_maps()
                    current_widget.waiting_for_input = False
                    self.timer.activate()
                return SceneStatus.SETTINGS

            # --- 全局切页控制 ---
            if ctrl.performed('tab_left') or ctrl.nav_performed('tab_left'):
                self.current_tab_index = (self.current_tab_index - 1) % len(self.tabs)
                self.target_scroll_y = 0
                self.selection_index = 0
                self._refresh_selection()
                self.timer.activate()
                return SceneStatus.SETTINGS
            elif ctrl.performed('tab_right') or ctrl.nav_performed('tab_right'):
                self.current_tab_index = (self.current_tab_index + 1) % len(self.tabs)
                self.target_scroll_y = 0
                self.selection_index = 0
                self._refresh_selection()
                self.timer.activate()
                return SceneStatus.SETTINGS

            # --- 上下选择内容 ---
            if ctrl.nav_performed('up') and self.selection_index > 0:
                self.selection_index -= 1
                self._refresh_selection()
                self._ensure_visible()
                self.timer.activate()
                return SceneStatus.SETTINGS
            elif ctrl.nav_performed('down') and self.selection_index < len(active_widgets) - 1:
                self.selection_index += 1
                self._refresh_selection()
                self._ensure_visible()
                self.timer.activate()
                return SceneStatus.SETTINGS

            # --- 左右调节数值 ---
            perf_left = ctrl.nav_performed('left')
            perf_right = ctrl.nav_performed('right')
            if perf_left or perf_right:
                direction = 'left' if perf_left else 'right'
                if isinstance(current_widget, (Slider, Selector)):
                    val = current_widget.update_value(direction)
                    self._apply_setting(current_widget, val)
                    self.timer.activate()
                    return SceneStatus.SETTINGS

            # --- 确认与返回 ---
            if ctrl.performed('confirm'):
                if isinstance(current_widget, Button):
                    lang = config.get('system', 'language')
                    msg = "确定要执行此操作吗？" if lang == 'zh_CN' else "Are you sure?"
                    self.dialogue.show(msg)
                    self.timer.activate()
                elif isinstance(current_widget, KeyBinder):
                    current_widget.waiting_for_input = True
                    self.timer.activate()
                elif isinstance(current_widget, Toggle):
                    val = current_widget.update_value()
                    self._apply_setting(current_widget, val)
                    self.timer.activate()
                return SceneStatus.SETTINGS
            
            if ctrl.performed('cancel'):
                config.save()
                self.game_input.refresh_all_maps()
                return SceneStatus.HOME

        return SceneStatus.SETTINGS

    def _check_key_conflict(self, device_key, new_key, current_action):
        all_controls = config.get('controls', device_key)
        for action, key in all_controls.items():
            if action != current_action and str(key) == str(new_key):
                return action
        return None

    def _ensure_visible(self):
        active_widgets = self.tab_widgets[self.tabs[self.current_tab_index]['id']]
        widget = active_widgets[self.selection_index]
        view_top = self.content_box_rect.y + self.box_padding
        view_bottom = self.content_box_rect.bottom - self.box_padding
        rel_y = widget.pos[1] - self.scroll_y
        if rel_y < view_top:
            self.target_scroll_y = widget.pos[1] - view_top
        elif rel_y + widget.size[1] > view_bottom:
            self.target_scroll_y = widget.pos[1] + widget.size[1] - view_bottom
        self.target_scroll_y = max(0, min(self.target_scroll_y, self.max_scroll_y))

    def _apply_setting(self, widget, value):
        label = widget.get_label()
        # 语言切换 (检查中英文关键字以确保在任何语言下都能识别)
        if '语言' in label or 'LANGUAGE' in label:
            new_lang = 'en_US' if value == 'English' else 'zh_CN'
            config.set(new_lang, 'system', 'language')
        
        # 音量调节
        elif '音量' in label or 'VOLUME' in label:
            if '主' in label or 'MASTER' in label: config.set(value, 'volume', 'master')
            elif '音乐' in label or 'MUSIC' in label: config.set(value, 'volume', 'music')
            elif '音效' in label or 'SFX' in label: config.set(value, 'volume', 'sfx')
            
        # 全屏切换
        elif '全屏' in label or 'FULLSCREEN' in label: 
            config.set(value, 'graphics', 'fullscreen')
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), (pygame.FULLSCREEN if value else 0) | pygame.RESIZABLE)


class RolePicker(Scene):
    def __init__(self, game_input: GameInput, surface: pygame.Surface):
        super().__init__(game_input, surface)
        # 背景图
        background = import_pic('assets/graphics/background/background_blurred.png')
        self.image = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        # 文字半透明背景
        self.bar_rect = pygame.Rect(0, SCREEN_HEIGHT - 240, SCREEN_WIDTH, 180)
        self.bar = pygame.Surface(self.bar_rect.size, pygame.SRCALPHA)
        self.bar.fill((0, 0, 0, 214))  # 半透明
        self.role_menu = RoleMenu(self.game_input, self.screen)  # 可选角色
        self.role_details = RoleDetailModule(self.game_input, self.screen)  # 角色详情
        self.image.blit(self.bar, self.bar_rect)
        self.particles = Particles(0.05, self.screen)
        self.timer = Timer(100, lambda: setattr(self, 'start', True))
        self.start = False

    def handle_input(self):
        for instance_id, device_info in self.game_input.controllers.items():
            ctrl = device_info['controller']
            current_player = device_info['player_name']
            timer = device_info['timer']

            if device_info['player_index'] != 'p0':  # 已加入游戏
                # 左右选择人物
                if not timer.active and not device_info['confirmed']:  # 选定后不能移动
                    if ctrl.nav_performed('left'):
                        device_info['player_name'] = self.role_menu.previous(current_player)
                        timer.activate()
                    elif ctrl.nav_performed('right'):
                        device_info['player_name'] = self.role_menu.next(current_player)
                        timer.activate()

                # 确认选择
                if ctrl.performed('confirm'):
                    device_info['confirmed'] = True

                    # 检查是否具备开始条件,超过2个玩家，全部准备好
                    if self.game_input.ready_to_start():
                        self.timer.activate()  # 启动计时器

                # 满足条件后稍等片刻进入游戏
                if self.start:
                    return SceneStatus.FIGHTING

                # 取消操作
                if ctrl.performed('cancel') and not self.timer.active:
                    if device_info['confirmed']:  # 取消确认
                        device_info['confirmed'] = False
                    else:  # 退出游戏控制
                        self.game_input.leave(instance_id)
                        self.role_details.create_details()  # 刷新显示

            # 加入游戏
            elif self.game_input.joinable:
                if ctrl.performed('confirm'):
                    self.game_input.join(instance_id, self.role_menu.available())
                    self.role_details.create_details()  # 刷新显示
                # 返回上一级
                if ctrl.performed('cancel') and self.game_input.joined_count() == 0:
                    return SceneStatus.HOME
        return SceneStatus.CHOOSE_ROLE

    def run(self, dt) -> SceneStatus:
        self.timer.update()
        self.screen.blit(self.image, (0, 0))
        self.particles.update(dt)
        self.role_menu.update()
        self.role_details.update(dt)
        return self.handle_input()


class RoleDetailModule:
    def __init__(self, game_input: GameInput, screen: pygame.Surface):
        self.group = pygame.sprite.Group()
        self.game_input = game_input
        self.place_holder = None
        self.screen = screen
        self.create_details()

    def create_details(self):
        self.group.empty()
        num = self.game_input.joined_count()
        y, w, h = 40, 280, 420  # 默认尺寸
        if num > 2:  # 数量太多，缩小尺寸
            y, w, h = 100, 200, 300  # 缩小后尺寸
        if num < 4:
            gap = (SCREEN_WIDTH - w * (num + 1)) // (num + 2)
        else:
            gap = (SCREEN_WIDTH - w * 4) // 5
        x = gap
        for i in range(1, 5):
            for dic in self.game_input.controllers.values():
                if dic['player_index'] == f'p{i}':
                    RoleDetailItem(dic, (x, y, w, h), self.group)
                    x += gap + w
                    break

        # 加入提示
        self.place_holder = RoleDetailItem(None, (x, y, w, h), self.group) if num < 4 else None

    def update(self, dt):
        self.group.update(dt)
        self.group.draw(self.screen)


class RoleDetailItem(pygame.sprite.Sprite):
    def __init__(self, device_info, rect: tuple, groups: pygame.sprite.Group):
        super().__init__(groups)
        self.device_info = device_info
        self.name = ''
        self.half_length = None
        self.full_length_pics = None
        self.full_length_index = 0
        self.full_length_pic = None
        self.indicators = import_folder_dict('assets/graphics/icons/indicator')
        check_icon = import_pic('assets/graphics/icons/check.png')
        self.check_icon = pygame.transform.scale(check_icon, (60, 60))
        self.earth_icon = import_pic('assets/graphics/icons/earth.png')
        self.update_player_pics()
        self.rect = pygame.Rect(rect)

        self.alpha_background = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.image = pygame.surface.Surface(self.rect.size, pygame.SRCALPHA)

        # 加入提示
        from src.core.config import config
        lang = config.get('system', 'language')
        hint = self.device_info['controller'].get_button_name(0) if self.device_info else "⏎"
        action = '加入游戏' if lang == 'zh_CN' else 'JOIN'

        self.text_surf = Menu.get_tip_surf(hint, action)
        rect = self.text_surf.get_rect(midbottom=self.rect.midbottom).move(0, -50)
        self.text_offset = rect.x - self.rect.x, rect.y - self.rect.y

    def draw_indicator(self):
        if self.device_info:
            size = self.rect.w * 0.25
            indicator = pygame.transform.scale(self.indicators[self.device_info['player_index']], (size, size))
            self.image.blit(indicator, (0, self.rect.h - size))

    def draw_check_mark(self):
        if self.device_info and self.device_info['confirmed']:
            self.image.blit(self.check_icon, (self.rect.w - 60, self.rect.h - 60))

    def draw_tip(self):
        self.image.blit(self.text_surf, self.text_offset)

    def update_player_pics(self):
        self.name = self.device_info['player_name'] if self.device_info else 'unselected'
        if self.name == 'unselected':
            self.half_length = self.earth_icon
            self.full_length_pics = None
        else:
            self.half_length = import_pic(f'assets/graphics/sprites/{self.name}/half_length.png')
            self.full_length_pics = import_gif(f'assets/graphics/sprites/{self.name}/idle.gif')

    def draw_background(self):
        if self.device_info and self.device_info['confirmed']:
            self.alpha_background.fill('orange')
            self.alpha_background.set_alpha(214)
        else:
            self.alpha_background.fill('black')
            self.alpha_background.set_alpha(114)
        half = pygame.transform.scale(self.half_length, self.rect.size)
        self.alpha_background.blit(half, (0, 0))
        self.image.blit(self.alpha_background, (0, 0))

    # 更新动画
    def update_full_length_pic(self, dt):
        self.full_length_index += dt * 4
        if self.full_length_index >= len(self.full_length_pics):
            self.full_length_index = 0
        if not self.full_length_pics:
            self.full_length_pic = None
        else:
            original = self.full_length_pics[int(self.full_length_index)]
            self.full_length_pic = pygame.transform.flip(original, True, False)

    def draw_foreground(self):
        # 全身像转为标准尺寸
        # 缩放 rect 并保持 midbottom 对齐
        full_rect = self.rect.scale_by(0.7)
        full_rect.midbottom = self.rect.midbottom
        # 按缩放后的 rect 大小调整图像
        full = pygame.transform.scale(self.full_length_pic, full_rect.size)
        # 计算偏移量，并将图像绘制到 self.image 上
        full_offset = full_rect.x - self.rect.x, full_rect.y - self.rect.y
        # 半身像转为标准尺寸

        self.image.blit(full, full_offset)

    def update(self, dt):
        self.update_player_pics()
        self.image.fill((0, 0, 0, 0))
        self.alpha_background.fill('black')
        self.draw_background()
        if self.name != 'unselected':
            self.update_full_length_pic(dt)
            self.draw_foreground()
            self.draw_indicator()
            self.draw_check_mark()
        else:
            self.draw_tip()


class RoleMenu:
    def __init__(self, game_input: GameInput, surface: pygame.Surface):
        self.group = pygame.sprite.Group()
        self.game_input = game_input
        self.names: list[str] = [d for d in os.listdir(resource_path('assets/graphics/sprites')) if
                                 not d.startswith('.')]
        self.create_options()
        self.screen = surface

    def create_options(self) -> None:
        w = len(self.names) * 110
        x, y = (SCREEN_WIDTH - w) // 2, 500
        for name in self.names:
            RoleOption(name, (x, y), self.game_input, self.group)
            x += 110

    def update(self) -> None:
        self.group.update()
        self.group.draw(self.screen)

    # 获取一个尚无人选择的角色
    def available(self) -> str:
        for name in self.names:
            if all(ctrl['player_name'] != name for ctrl in self.game_input.controllers.values()):
                return name

    def next(self, name: str) -> str:
        index = self.names.index(name)
        if index < len(self.names) - 1:
            index += 1
        return self.names[index]

    def previous(self, name: str) -> str:
        index = self.names.index(name)
        if index > 0:
            index -= 1
        return self.names[index]


class RoleOption(pygame.sprite.Sprite):
    def __init__(self, name: str, pos: tuple, game_input: GameInput, groups: pygame.sprite.Group):
        super().__init__(groups)
        self.name = name
        self.original = import_pic(f'assets/graphics/sprites/{name}/headshot.png')
        self.indicators = import_folder_dict('assets/graphics/icons/indicator')
        self.game_input = game_input
        self.normal_rect = pygame.Rect((0, 0, 100, 250))
        self.scaled_rect = self.normal_rect.scale_by(1.05)  # 保持中心缩放
        self.scaled_rect.topleft = self.normal_rect.topleft  # 对齐左上角
        self.normal_global_rect = self.normal_rect.move(pos)
        self.scaled_global_rect = self.normal_global_rect.scale_by(1.05)

        self.role_pic = pygame.transform.scale(self.original, self.normal_rect.size)
        self.scaled_role_pic = pygame.transform.scale(self.original, self.scaled_rect.size)
        self.colors = {'p1': 'green', 'p2': 'cyan', 'p3': 'purple', 'p4': 'magenta'}
        self.positions = [(0, 0), (65, 0), (0, 220), (65, 220)]
        self.image = pygame.surface.Surface(self.normal_rect.size)
        self.rect = None

    def update(self) -> None:
        # 绘制选中状态
        i = 0
        for dic in self.game_input.controllers.values():
            player_index = dic['player_index']
            if dic['player_name'] == self.name:
                if i == 0:
                    self.draw_scaled()
                pygame.draw.rect(self.image, self.colors[player_index], self.scaled_rect, 6)  # 边框
                i += 1
        self.draw_indicator()
        # 未选中状态
        if i == 0:
            self.draw_unselected()

    def draw_indicator(self) -> None:
        # 绘制标签
        i = 0
        dics: list[dict[str:any]] = sorted(self.game_input.controllers.values(), key=lambda d: d['player_index'])
        for dic in dics:
            if dic['player_name'] == self.name:
                player_index = dic['player_index']
                self.image.blit(self.indicators[player_index], self.positions[i])
                i += 1

    def draw_scaled(self) -> None:
        self.rect = self.scaled_global_rect
        self.image = pygame.transform.scale(self.image, self.rect.size)
        self.image.fill('yellow')
        self.image.blit(self.scaled_role_pic, (0, 0))  # 图片

    def draw_unselected(self) -> None:
        self.rect = self.normal_global_rect
        self.image = pygame.transform.scale(self.image, self.rect.size)
        pygame.transform.scale(self.image, self.rect.size)
        self.image.fill('orange')
        pygame.draw.rect(self.image, 'black', self.normal_rect, 2)  # 边框
        self.image.blit(self.role_pic, (0, 0))  # 图片
