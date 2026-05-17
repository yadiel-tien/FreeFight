import pygame
from src.core.support import resource_path
from src.settings import *

class UIWidget:
    def __init__(self, label_dict, pos, size=(400, 40)):
        # label_dict: {'zh_CN': '中文名', 'en_US': 'English Name'}
        self.label_dict = label_dict
        self.pos = pos
        self.size = size
        self.rect = pygame.Rect(pos, size)
        self.selected = False
        self.selectable = True # 是否可被导航选中
        font_path = resource_path('assets/font/SimHei.ttf')
        self.font = pygame.font.Font(font_path, 24)
        
    def get_label(self):
        from src.core.config import config
        lang = config.get('system', 'language')
        return self.label_dict.get(lang, self.label_dict.get('zh_CN', 'Unnamed'))

    def draw(self, surface, offset_y=0):
        pass

class Slider(UIWidget):
    def __init__(self, label_dict, pos, value, min_val=0.0, max_val=1.0):
        super().__init__(label_dict, pos)
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.slider_rect = pygame.Rect(pos[0] + 200, pos[1] + 15, 180, 10)
        self.dragging = False

    def update_value(self, direction):
        step = 0.05
        if direction == 'left':
            self.value = max(self.min_val, self.value - step)
        elif direction == 'right':
            self.value = min(self.max_val, self.value + step)
        return self.value

    def draw(self, surface, offset_y=0):
        color = 'orange' if self.selected else 'white'
        draw_pos = (self.pos[0], self.pos[1] - offset_y)
        
        # 标签
        txt = self.font.render(self.get_label(), True, color)
        surface.blit(txt, (draw_pos[0], draw_pos[1] + 5))
        
        # 滑块
        s_rect = self.slider_rect.copy()
        s_rect.y -= offset_y
        pygame.draw.rect(surface, (60, 60, 60), s_rect, border_radius=5)
        
        fill_width = int((self.value - self.min_val) / (self.max_val - self.min_val) * s_rect.w)
        fill_rect = pygame.Rect(s_rect.topleft, (fill_width, s_rect.h))
        pygame.draw.rect(surface, color, fill_rect, border_radius=5)
        
        handle_pos = (s_rect.x + fill_width, s_rect.centery)
        pygame.draw.circle(surface, 'white' if self.selected else color, handle_pos, 8)

class Selector(UIWidget):
    def __init__(self, label_dict, pos, options, current_index=0):
        super().__init__(label_dict, pos)
        self.options = options
        self.index = current_index

    def update_value(self, direction):
        if direction == 'left':
            self.index = (self.index - 1) % len(self.options)
        elif direction == 'right':
            self.index = (self.index + 1) % len(self.options)
        return self.options[self.index]

    def draw(self, surface, offset_y=0):
        color = 'orange' if self.selected else 'white'
        draw_pos = (self.pos[0], self.pos[1] - offset_y)
        
        txt = self.font.render(self.get_label(), True, color)
        surface.blit(txt, (draw_pos[0], draw_pos[1] + 5))
        
        val_txt = self.font.render(f"< {self.options[self.index]} >", True, color)
        surface.blit(val_txt, (draw_pos[0] + 200, draw_pos[1] + 5))

class Toggle(UIWidget):
    def __init__(self, label_dict, pos, value):
        super().__init__(label_dict, pos)
        self.value = value
        self.toggle_rect = pygame.Rect(pos[0] + 200, pos[1] + 10, 50, 22)

    def update_value(self, direction=None):
        self.value = not self.value
        return self.value

    def draw(self, surface, offset_y=0):
        color = 'orange' if self.selected else 'white'
        draw_pos = (self.pos[0], self.pos[1] - offset_y)
        
        txt = self.font.render(self.get_label(), True, color)
        surface.blit(txt, (draw_pos[0], draw_pos[1] + 5))
        
        t_rect = self.toggle_rect.copy()
        t_rect.y -= offset_y
        bg_color = (60, 60, 60) if not self.value else (180, 100, 0)
        pygame.draw.rect(surface, bg_color, t_rect, border_radius=11)
        pygame.draw.rect(surface, color, t_rect, 2, border_radius=11)
        
        circle_x = t_rect.x + (38 if self.value else 12)
        pygame.draw.circle(surface, 'white' if self.value else (200, 200, 200), (circle_x, t_rect.centery), 8)
        
        from src.core.config import config
        lang = config.get('system', 'language')
        status_text = "开" if self.value else "关"
        if lang == 'en_US': status_text = "ON" if self.value else "OFF"
        
        status_txt = self.font.render(status_text, True, color)
        surface.blit(status_txt, (t_rect.right + 15, draw_pos[1] + 5))

class KeyBinder(UIWidget):
    def __init__(self, label_dict, pos, current_key, action_id, is_joystick=False, controller=None):
        super().__init__(label_dict, pos)
        self.key = current_key
        self.action_id = action_id
        self.waiting_for_input = False
        self.is_joystick = is_joystick
        self.controller = controller
        self.key_cap_rect = pygame.Rect(pos[0] + 200, pos[1] + 2, 160, 32)
        
        # 冲突反馈动画相关
        self.conflict_timer = 0
        self.shake_offset = 0
        self.temp_conflict_key = None

    def trigger_conflict_effect(self, attempted_key):
        # 触发 500ms 的红闪和抖动，并记录尝试设置的那个按键
        self.conflict_timer = 500 
        self.temp_conflict_key = attempted_key

    def draw(self, surface, offset_y=0):
        color = 'orange' if self.selected else 'white'
        
        # 处理显示文本
        if self.key is None:
            display_val = "---"
        elif self.is_joystick and self.controller:
            display_val = self.controller.get_button_name(self.key)
        else:
            display_val = str(self.key).upper()
            if self.is_joystick:
                display_val = f"BTN {self.key}"
        
        # 如果正在发生冲突反馈
        if self.conflict_timer > 0:
            color = (255, 50, 50) # 亮红色
            import random
            self.shake_offset = random.randint(-3, 3)
            # 抖动期间显示那个“冲突”的按键
            if self.is_joystick and self.controller:
                display_val = self.controller.get_button_name(self.temp_conflict_key)
            else:
                display_val = str(self.temp_conflict_key).upper()
                if self.is_joystick:
                    display_val = f"BTN {self.temp_conflict_key}"
            
            self.conflict_timer -= 16 
        else:
            self.shake_offset = 0
            self.temp_conflict_key = None
            if self.waiting_for_input: 
                color = 'yellow'
                display_val = "???"
            
        draw_pos = (self.pos[0] + self.shake_offset, self.pos[1] - offset_y)
        
        # 绘制标签
        txt = self.font.render(self.get_label(), True, color)
        surface.blit(txt, (draw_pos[0], draw_pos[1] + 5))
        
        k_rect = self.key_cap_rect.copy()
        k_rect.y -= offset_y
        k_rect.x += self.shake_offset
        pygame.draw.rect(surface, (40, 40, 40), k_rect, border_radius=5)
        pygame.draw.rect(surface, color, k_rect, 1, border_radius=5)
        
        val_txt = self.font.render(display_val, True, color)
        val_rect = val_txt.get_rect(center=k_rect.center)
        surface.blit(val_txt, val_rect)

class Button(UIWidget):
    def __init__(self, label_dict, pos, size=(400, 45)):
        super().__init__(label_dict, pos, size)
    
    def draw(self, surface, offset_y=0):
        color = 'orange' if self.selected else 'white'
        text_color = (20, 20, 20) if self.selected else 'white'
        
        draw_rect = self.rect.copy()
        draw_rect.y -= offset_y
        
        pygame.draw.rect(surface, color, draw_rect, 2, border_radius=5)
        if self.selected:
            surface.fill((255, 165, 0), draw_rect.inflate(-4, -4))
            
        txt = self.font.render(self.get_label(), True, text_color)
        txt_rect = txt.get_rect(center=draw_rect.center)
        surface.blit(txt, txt_rect)

class Header(UIWidget):
    def __init__(self, label_dict, pos):
        super().__init__(label_dict, pos, size=(400, 40))
        path = resource_path('assets/font/SimHei.ttf')
        self.font = pygame.font.Font(path, 18)
        self.selectable = False

    def draw(self, surface, offset_y=0):
        # Header 的实际绘制逻辑已被移至 Scene.run 中与方框同步绘制
        pass
