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
        # label_list: list of label_dicts [{'zh_CN': '...', 'en_US': '...'}, ...]
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
    def get_tip_surf_multi(hints_data):
        # hints_data: [ (key_text, action_text), ... ]
        path = resource_path('assets/font/SimHei.ttf')
        # 精致字体
        font_key = pygame.font.Font(path, 14)
        font_action = pygame.font.Font(path, 16)
        font_key.set_bold(True)
        font_action.set_bold(True)
        
        surfs = []
        total_w = 0
        for keys_text, action_text in hints_data:
            # --- 渲染单个组合 (无边框极简风格) ---
            has_return = "⏎" in keys_text
            has_circle = "○" in keys_text
            has_square = "□" in keys_text
            has_triangle = "△" in keys_text
            has_menu = "≡" in keys_text
            has_view = "❐" in keys_text
            has_minus = "−" in keys_text
            has_v_arrows = "↑ ↓" in keys_text
            has_h_arrows = "← →" in keys_text
            
            display_text = keys_text
            for char in ["⏎", "○", "□", "△", "≡", "❐", "−", "↑", "↓", "←", "→"]:
                display_text = display_text.replace(char, "  ")
            
            # 分离颜色：按键高亮(250)，文字中灰(150)
            icon_color = (250, 250, 250)
            text_color = (150, 150, 150)
            
            key_img = font_key.render(display_text, True, icon_color)
            cap_width = key_img.get_width() + 6
            action_img = font_action.render(action_text, True, text_color)
            
            item_w = cap_width + 4 + action_img.get_width()
            item_surf = pygame.Surface((item_w, 40), pygame.SRCALPHA)
            
            cx, cy = cap_width // 2, 20
            if "/" in keys_text: cx = 8 
            
            # 绘制文字
            item_surf.blit(key_img, (3, (40 - key_img.get_height()) // 2))
            
            # 手动绘制完整的、带柄的图标
            color = icon_color
            if has_return:
                pygame.draw.lines(item_surf, color, False, [(cx+6, cy-6), (cx+6, cy+4), (cx-6, cy+4)], 2)
                pygame.draw.lines(item_surf, color, False, [(cx-2, cy), (cx-7, cy+4), (cx-2, cy+8)], 2)
            elif has_circle:
                pygame.draw.circle(item_surf, color, (cx, cy), 7, 2)
            elif has_square:
                pygame.draw.rect(item_surf, color, (cx-7, cy-7, 14, 14), 2)
            elif has_triangle:
                pygame.draw.lines(item_surf, color, True, [(cx, cy-8), (cx-8, cy+6), (cx+8, cy+6)], 2)
            elif has_menu:
                for i in range(-5, 6, 5): 
                    pygame.draw.line(item_surf, color, (cx-7, cy+i), (cx+7, cy+i), 2)
            elif has_view:
                pygame.draw.rect(item_surf, color, (cx-1, cy-6, 9, 9), 2)
                pygame.draw.rect(item_surf, color, (cx-8, cy-1, 9, 9), 2)
            elif has_minus:
                pygame.draw.line(item_surf, color, (cx-6, cy), (cx+6, cy), 3)
            elif has_v_arrows:
                # 完整的上下箭头
                x1, x2 = cx - 8, cx + 8
                pygame.draw.line(item_surf, color, (x1, cy+7), (x1, cy-7), 2)
                pygame.draw.lines(item_surf, color, False, [(x1-4, cy-3), (x1, cy-7), (x1+4, cy-3)], 2)
                pygame.draw.line(item_surf, color, (x2, cy-7), (x2, cy+7), 2)
                pygame.draw.lines(item_surf, color, False, [(x2-4, cy+3), (x2, cy+7), (x2+4, cy+3)], 2)
            elif has_h_arrows:
                # 完整的左右箭头
                y1, y2 = cy - 7, cy + 7
                lx_head, lx_tail = cx - 7, cx + 7
                pygame.draw.line(item_surf, color, (lx_tail, y1), (lx_head, y1), 2)
                pygame.draw.lines(item_surf, color, False, [(lx_head+3, y1-3), (lx_head, y1), (lx_head+3, y1+3)], 2)
                rx_head, rx_tail = cx + 7, cx - 7
                pygame.draw.line(item_surf, color, (rx_tail, y2), (rx_head, y2), 2)
                pygame.draw.lines(item_surf, color, False, [(rx_head-3, y2-3), (rx_head, y2), (rx_head-3, y2+3)], 2)
            
            item_surf.blit(action_img, (cap_width + 2, (40 - action_img.get_height()) // 2))
            
            surfs.append(item_surf)
            total_w += item_w + 10 
            
        total_w -= 10
        final_surf = pygame.Surface((total_w, 40), pygame.SRCALPHA)
        curr_x = 0
        for s in surfs:
            final_surf.blit(s, (curr_x, 0))
            curr_x += s.get_width() + 10
            
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
                if ctrl.nav_performed('up') and self.selected_index > 0:
                    self.selected_index -= 1
                    device_info['timer'].activate()
                elif ctrl.nav_performed('down') and self.selected_index < len(self.options) - 1:
                    self.selected_index += 1
                    device_info['timer'].activate()
                if ctrl.performed('confirm'):
                    return self.selected_index, instance_id
        return -1, None
