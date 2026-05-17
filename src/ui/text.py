import pygame
from src.core.support import resource_path
from src.settings import SCREEN_WIDTH


class OptionText:
    def __init__(self, label_dict, pos, size, surface: pygame.Surface):
        self.label_dict = label_dict
        self.pos = pos
        self.selected = False
        self.screen = surface
        self.size = size
        
        # 加载中文字体 (SimHei)
        zh_path = resource_path('assets/font/SimHei.ttf')
        self.font_zh_unselected = pygame.font.Font(zh_path, size)
        self.font_zh_selected = pygame.font.Font(zh_path, int(size * 1.3))
        # 开启中文加粗
        self.font_zh_unselected.set_bold(True)
        self.font_zh_selected.set_bold(True)
        
        # 加载英文字体 (Impact)
        en_path = resource_path('assets/font/impact.ttf')
        self.font_en_unselected = pygame.font.Font(en_path, size)
        self.font_en_selected = pygame.font.Font(en_path, int(size * 1.3))
        
        self.offset_y_factor = -0.3

    def get_text(self):
        from src.core.config import config
        lang = config.get('system', 'language')
        return self.label_dict.get(lang, self.label_dict.get('zh_CN', 'Unnamed'))

    def display(self):
        text = self.get_text()
        from src.core.config import config
        lang = config.get('system', 'language')
        
        # 根据语言选择对应的字体对象
        if lang == 'zh_CN':
            font_u = self.font_zh_unselected
            font_s = self.font_zh_selected
        else:
            font_u = self.font_en_unselected
            font_s = self.font_en_selected

        if self.selected:
            img = font_s.render(text, True, (255, 255, 65))
            offset = pygame.math.Vector2(self.size * 0.5, img.get_height() * self.offset_y_factor)
            self.screen.blit(img, self.pos + offset)
        else:
            img = font_u.render(text, True, 'white')
            self.screen.blit(img, self.pos)


class Menu:
    def __init__(self, label_list, game_input, pos, surface: pygame.Surface, size=50, center_at=None, show_back=True):
        self.game_input = game_input
        x, y = pos
        self.options = []
        self.selected_index = 0
        self.screen = surface
        self.center_at = center_at if center_at is not None else SCREEN_WIDTH // 2
        self.show_back = show_back
        for label_dict in label_list:
            self.options.append(OptionText(label_dict, (x, y), size, self.screen))
            y += size * 1.5
        
        self.update_tip()

    def get_tip_text(self):
        from src.core.config import config
        lang = config.get('system', 'language')
        
        nav_hint = "↑ ↓"
        nav_text = "选择" if lang == 'zh_CN' else "SELECT"
        
        conf_hint = self.game_input.get_confirm_hint(lang)
        conf_text = "确定" if lang == 'zh_CN' else "CONFIRM"
        
        res = [(nav_hint, nav_text), (conf_hint, conf_text)]
        
        if self.show_back:
            menu_hint = self.game_input.get_menu_hint(lang)
            menu_text = "返回" if lang == 'zh_CN' else "BACK"
            res.append((menu_hint, menu_text))
        
        return res

    def update_tip(self):
        hints_data = self.get_tip_text()
        self.tip = self.get_tip_surf_multi(hints_data)
        # 居中显示在指定的中心点，位置调高一点 (从 680 调到 620)
        self.tip_pos = (self.center_at - self.tip.get_width() // 2, 620)

    @staticmethod
    def draw_single_key(surface, x, y, key_text, font):
        """绘制单个按键或图标 (微调比例以对齐文字)，返回宽度"""
        color = (250, 250, 250)
        cy = y + 10 # 逻辑中心 y
        
        # 1. 识别并绘制特殊符号 (缩小约 15-20%)
        if key_text == "⏎":
            pygame.draw.lines(surface, color, False, [(x+13, cy-5), (x+13, cy+3), (x+5, cy+3)], 2)
            pygame.draw.lines(surface, color, False, [(x+8, cy), (x+4, cy+3), (x+8, cy+6)], 2)
            return 18
        elif key_text == "○":
            pygame.draw.circle(surface, color, (x + 8, cy), 6, 2)
            return 16
        elif key_text == "□":
            pygame.draw.rect(surface, color, (x + 2, cy - 6, 12, 12), 2)
            return 16
        elif key_text == "△":
            pygame.draw.lines(surface, color, True, [(x + 8, cy - 7), (x + 1, cy + 5), (x + 15, cy + 5)], 2)
            return 16
        elif key_text == "≡":
            for i in range(-4, 5, 4): pygame.draw.line(surface, color, (x+2, cy+i), (x+14, cy+i), 2)
            return 16
        elif key_text == "❐":
            pygame.draw.rect(surface, color, (x+6, cy-5, 7, 7), 2)
            pygame.draw.rect(surface, color, (x, cy-1, 7, 7), 2)
            return 16
        elif key_text == "−":
            pygame.draw.line(surface, color, (x+3, cy), (x+13, cy), 2)
            return 16
        elif key_text == "↑ ↓":
            pygame.draw.line(surface, color, (x+3, cy+6), (x+3, cy-6), 2)
            pygame.draw.lines(surface, color, False, [(x, cy-3), (x+3, cy-6), (x+6, cy-3)], 2)
            pygame.draw.line(surface, color, (x+13, cy-6), (x+13, cy+6), 2)
            pygame.draw.lines(surface, color, False, [(x+10, cy+3), (x+13, cy+6), (x+16, cy+3)], 2)
            return 20
        elif key_text == "← →":
            pygame.draw.line(surface, color, (x+12, cy-6), (x+2, cy-6), 2)
            pygame.draw.lines(surface, color, False, [(x+5, cy-8), (x+2, cy-6), (x+5, cy-4)], 2)
            pygame.draw.line(surface, color, (x+16, cy+6), (x+6, cy+6), 2)
            pygame.draw.lines(surface, color, False, [(x+13, cy+4), (x+16, cy+6), (x+13, cy+8)], 2)
            return 20
        else:
            # 普通文本
            img = font.render(key_text, True, color)
            surface.blit(img, (x, y + (20 - img.get_height()) // 2))
            return img.get_width()

    @staticmethod
    def get_tip_surf_multi(hints_data):
        # hints_data: [ (key_text, action_text), ... ]
        path = resource_path('assets/font/SimHei.ttf')
        # 调大动作文字，调小图标字体，使比例均衡
        font_key = pygame.font.Font(path, 14)
        font_action = pygame.font.Font(path, 18)
        font_key.set_bold(True)
        font_action.set_bold(True)
        
        items = []
        total_w = 0
        
        symbols = ["⏎", "○", "□", "△", "≡", "❐", "−", "↑ ↓", "← →"]
        
        for keys_text, action_text in hints_data:
            # 1. 解析 keys_text (支持混合符号，如 "⏎ / A")
            # 简单的分词逻辑：按空格分割，保留符号
            tokens = []
            temp = keys_text
            while temp:
                found = False
                for sym in symbols:
                    if temp.startswith(sym):
                        tokens.append(sym)
                        temp = temp[len(sym):].lstrip()
                        found = True
                        break
                if not found:
                    # 取下一个词
                    space_idx = temp.find(" ")
                    if space_idx == -1:
                        tokens.append(temp)
                        temp = ""
                    else:
                        tokens.append(temp[:space_idx])
                        temp = temp[space_idx:].lstrip()
            
            # 2. 预渲染动作文本
            action_img = font_action.render(action_text, True, (150, 150, 150))
            
            # 3. 计算该组合的总宽度并绘制
            # 先创建一个足够宽的 temp 表面
            temp_surf = pygame.Surface((500, 40), pygame.SRCALPHA)
            curr_x = 0
            for i, token in enumerate(tokens):
                curr_x += Menu.draw_single_key(temp_surf, curr_x, 10, token, font_key)
                if i < len(tokens) - 1: curr_x += 4 # 词间距
            
            curr_x += 8 # 键与动作间距
            temp_surf.blit(action_img, (curr_x, (40 - action_img.get_height()) // 2))
            curr_x += action_img.get_width()
            
            # 裁剪并保存
            final_item = pygame.Surface((curr_x, 40), pygame.SRCALPHA)
            final_item.blit(temp_surf, (0, 0))
            items.append(final_item)
            total_w += curr_x + 25 # 组合间距
            
        if not items: return pygame.Surface((1, 1), pygame.SRCALPHA)
        
        total_w -= 25
        final_surf = pygame.Surface((total_w, 40), pygame.SRCALPHA)
        curr_x = 0
        for item in items:
            final_surf.blit(item, (curr_x, 0))
            curr_x += item.get_width() + 25
            
        return final_surf

    @staticmethod
    def get_tip_surf(keys_text, action_text):
        return Menu.get_tip_surf_multi([(keys_text, action_text)])

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
                if ctrl.ui_performed('up') and self.selected_index > 0:
                    self.selected_index -= 1
                    device_info['timer'].activate()
                elif ctrl.ui_performed('down') and self.selected_index < len(self.options) - 1:
                    self.selected_index += 1
                    device_info['timer'].activate()
                if ctrl.ui_performed('confirm'):
                    return self.selected_index, instance_id
        return -1, None
