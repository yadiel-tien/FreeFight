import os
import sys
import json
import pygame
from src.scenes.scene import Scene, SceneStatus
from src.core.support import resource_path, import_gifs_dict

class Editor(Scene):
    def __init__(self, game_input, surface):
        super().__init__(game_input, surface)
        self.sprite_base_path = resource_path("assets/graphics/sprites")
        self.characters = sorted([d for d in os.listdir(self.sprite_base_path) 
                                 if os.path.isdir(os.path.join(self.sprite_base_path, d))])
        
        self.char_index = 0
        self.status_list = []
        self.status_index = 0
        self.frame_index = 0
        self.frames = []
        self.original_frames = []
        
        # 碰撞配置数据
        self.collision_data = {}
        
        # 编辑状态
        self.to_right = True # 模拟面向
        self.drag_start = None
        self.drag_current = None
        
        # Mac 触控板友好：Q/W/E 按键切换模式，统一使用鼠标左键拖拽绘制
        self.active_box_type = 'hurtbox' # 'hurtbox', 'hitbox', 'pushbox'
        
        # 下拉菜单 (Dropdown) 状态
        self.dropdown_rect = pygame.Rect(20, 120, 200, 36)
        self.dropdown_expanded = False
        self.save_feedback_timer = 0
        
        # 退出确认弹窗状态与按钮区域
        self.show_exit_dialog = False
        self.exit_btn_confirm_rect = pygame.Rect(1280 // 2 - 170, 720 // 2 + 25, 150, 36)
        self.exit_btn_cancel_rect = pygame.Rect(1280 // 2 + 20, 720 // 2 + 25, 150, 36)
        
        # 复制成功提示的计时器
        self.copy_feedback_timer = 0
        
        # 招式动作判定配置，用于自动初始化默认 Hitbox
        self.attack_moves = ['attack', 'combo', 'dash attack', 'jump attack', 'super move 1', 'super move 2', 'super move 3', 'finisher']
        
        # 物理双色主题支持：Cyber深黑网格 vs 舒适白昼灰网格 (真·全局主题大换肤)
        self.theme_mode = 'dark'
        self.THEMES = {
            'dark': {
                'bg': (15, 15, 18),
                'grid': (26, 26, 32),
                'highlight': (38, 38, 46),
                'panel': (26, 26, 32),
                'panel_border': (46, 46, 56),
                'text': (245, 245, 250),
                'text_muted': (140, 140, 152)
            },
            'light': {
                'bg': (240, 240, 245),
                'grid': (220, 220, 228),
                'highlight': (185, 185, 200),
                'panel': (255, 255, 255),
                'panel_border': (215, 215, 225),
                'text': (30, 30, 35),
                'text_muted': (110, 110, 125)
            }
        }
        
        # AAA级 全局自适应色彩系统
        theme = self.THEMES['dark']
        self.BG_COLOR = theme['bg']
        self.PANEL_COLOR = theme['panel']
        self.PANEL_BORDER = theme['panel_border']
        self.GRID_COLOR = theme['grid']
        self.GRID_HIGHLIGHT = theme['highlight']
        self.TEXT_COLOR = theme['text']
        self.TEXT_MUTED = theme['text_muted']
        self.HURTBOX_COLOR = (46, 213, 115)   # 🟢 霓虹薄荷绿
        self.HITBOX_COLOR = (255, 71, 87)     # 🔴 霓虹珊瑚红
        self.PUSHBOX_COLOR = (30, 144, 255)   # 🔵 霓虹极光蓝
        self.RECT_BORDER_COLOR = (116, 125, 140) # 图片定位框
        self.GROUND_COLOR = (165, 177, 194)   # 地平参考线
        self.ACCENT_COLOR = (106, 115, 250)   # 按钮高亮紫
        
        # 字体导入与兼容
        font_path = resource_path('assets/font/SimHei.ttf')
        if os.path.exists(font_path):
            self.font_small = pygame.font.Font(font_path, 15)
            self.font_medium = pygame.font.Font(font_path, 19)
            self.font_large = pygame.font.Font(font_path, 25)
        else:
            self.font_small = pygame.font.SysFont("Arial", 15)
            self.font_medium = pygame.font.SysFont("Arial", 19)
            self.font_large = pygame.font.SysFont("Arial", 25, bold=True)
            
        # 初始化 Inspector 面板 (招式与角色全局数值配置模块)
        from src.scenes.editor_inspector import EditorInspector
        self.inspector = EditorInspector(
            self.font_small, self.font_medium, self.font_large,
            self.ACCENT_COLOR, self.TEXT_COLOR, self.TEXT_MUTED,
            self.PANEL_COLOR, self.PANEL_BORDER
        )
        
        self.load_character()

    def load_character(self):
        if not self.characters:
            return
        
        self.char_name = self.characters[self.char_index]
        self.char_dir = os.path.join(self.sprite_base_path, self.char_name)
        
        # 查找所有 GIF 动画，排除风格化临时生成的 _anime
        self.status_list = sorted([os.path.splitext(f)[0] for f in os.listdir(self.char_dir) 
                                  if f.lower().endswith('.gif') and not f.lower().endswith('_anime.gif')])
        
        self.status_index = 0
        self.frame_index = 0
        
        # 优先读取现有的 config.json
        self.json_path = os.path.join(self.char_dir, "config.json")

        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.collision_data = json.load(f)
            except Exception as e:
                print(f"读取 config.json 失败: {e}")
                self.collision_data = {}
        else:
            self.collision_data = {}

        # 确保包含 character_stats 和 move_stats 配置
        if "character_stats" not in self.collision_data:
            self.collision_data["character_stats"] = {
                "max_health": 1000,
                "speed": 150,
                "gravity": 800,
                "jump_strength": 500
            }
        if "move_stats" not in self.collision_data:
            self.collision_data["move_stats"] = {
                "attack": {"damage": 50, "knockback": 10, "startup": 0.0, "recovery": 0.08, "cost": 0},
                "combo": {"damage": 30, "knockback": 5, "startup": 0.0, "recovery": 0.06, "cost": 0},
                "dash attack": {"damage": 60, "knockback": 20, "startup": 0.0, "recovery": 0.12, "cost": 0},
                "jump attack": {"damage": 40, "knockback": 15, "startup": 0.0, "recovery": 0.0, "cost": 0},
                "super move 1": {"damage": 150, "knockback": 40, "startup": 0.35, "recovery": 0.45, "cost": 30},
                "super move 2": {"damage": 200, "knockback": 50, "startup": 0.50, "recovery": 0.60, "cost": 40},
                "super move 3": {"damage": 180, "knockback": 45, "startup": 0.25, "recovery": 0.35, "cost": 30},
                "finisher": {"damage": 300, "knockback": 100, "startup": 0.70, "recovery": 0.80, "cost": 100}
            }
            
        self.load_animation()

    def load_animation(self):
        if not self.status_list:
            self.frames = []
            return
            
        status = self.status_list[self.status_index]
        gif_path = os.path.join(self.char_dir, f"{status}.gif")
        
        try:
            from PIL import Image
            img = Image.open(gif_path)
            self.original_frames = []
            for index in range(img.n_frames):
                img.seek(index)
                frame = img.convert('RGBA')
                pygame_image = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
                self.original_frames.append(pygame_image)
                
            # 按 0.5 比例进行缩放
            self.frames = []
            for frame in self.original_frames:
                w, h = frame.get_size()
                scaled = pygame.transform.scale(frame, (int(w * 0.5), int(h * 0.5)))
                self.frames.append(scaled)
        except Exception as e:
            print(f"加载动画出错: {e}")
            self.frames = []
            
        self.frame_index = 0

    def generate_default_boxes(self, status, frame_idx):
        """
        数据驱动：根据游戏原有物理规则计算默认 box 区域，自动赋初值
        """
        if not self.frames:
            return {"hurtbox": None, "hitbox": None, "pushbox": None}
            
        char_surf = self.frames[frame_idx]
        w, h = char_surf.get_size()
        
        # 1. 🟢 默认 Hurtbox (受击盒)：宽度 40%，高度 80%，居中
        hurt_w = int(w * 0.4)
        hurt_h = int(h * 0.8)
        hurt_x = w // 2 - hurt_w // 2
        hurt_y = h // 2 - hurt_h // 2
        default_hurt = [hurt_x, hurt_y, hurt_w, hurt_h]
        
        # 2. 🔵 默认 Pushbox (推挤盒)：宽度 30%，高度 75%，居中贴地
        push_w = int(w * 0.3)
        push_h = int(h * 0.75)
        push_x = w // 2 - push_w // 2
        push_y = h - push_h
        default_push = [push_x, push_y, push_w, push_h]
        
        # 3. 🔴 默认 Hitbox (攻击盒)：只有在活跃攻击帧内产生
        default_hit = None
        if status in self.attack_moves:
            total_frames = len(self.frames)
            
            # 判断是否是攻击判定活跃帧
            is_active = False
            if status in ['attack', 'combo', 'dash attack', 'jump attack']:
                start_frame = max(0, min(1, total_frames - 1))
                end_frame = max(0, total_frames - 1)
                is_active = (start_frame <= frame_idx <= end_frame)
            else:
                start_frame = int(total_frames * 0.3)
                end_frame = max(start_frame, int(total_frames * 0.9))
                is_active = (start_frame <= frame_idx <= end_frame)
                
            if is_active:
                # 设定招式大小比例
                if status in ['super move 1', 'super move 2', 'super move 3', 'finisher']:
                    hw = int(w * 0.7)
                    hh = int(h * 0.4)
                else:
                    hw = int(w * 0.25)
                    hh = int(h * 0.2)
                    
                y_offset = 0
                if status == 'jump attack':
                    y_offset = 20
                elif status == 'head hit':
                    y_offset = -30
                    
                # 按照 right 朝向 (to_right=True) 计算默认拳脚点
                bx = w // 2 + 10
                by = h // 2 - hh // 2 + y_offset
                default_hit = [bx, by, hw, hh]
                
        return {
            "hurtbox": default_hurt,
            "hitbox": default_hit,
            "pushbox": default_push
        }

    def get_current_boxes(self):
        status = self.status_list[self.status_index]
        frame_key = f"frame_{self.frame_index}"
        
        if status not in self.collision_data:
            self.collision_data[status] = {}
            
        # 如果当前帧在 JSON 中无配置，则使用物理公式初始化默认值 (数据驱动赋初值)
        if frame_key not in self.collision_data[status]:
            self.collision_data[status][frame_key] = self.generate_default_boxes(status, self.frame_index)
        else:
            # 兼容处理缺失的 pushbox 键
            if "pushbox" not in self.collision_data[status][frame_key]:
                defaults = self.generate_default_boxes(status, self.frame_index)
                self.collision_data[status][frame_key]["pushbox"] = defaults["pushbox"]
                
        return self.collision_data[status][frame_key]

    def save_data(self):
        try:
            # 1. 自动删除已被删除的 GIF 对应的动作键
            existing_statuses = list(self.collision_data.keys())
            for status in existing_statuses:
                if status in ["character_stats", "move_stats"]:
                    continue
                if status not in self.status_list:
                    del self.collision_data[status]
            
            # 2. 自动净化各动作的帧数：使 JSON 中的 frame 数量与实际 GIF 帧数绝对一致
            for status in self.status_list:
                gif_path = os.path.join(self.char_dir, f"{status}.gif")
                if os.path.exists(gif_path):
                    try:
                        from PIL import Image
                        with Image.open(gif_path) as img:
                            actual_frames_count = img.n_frames
                    except Exception as e:
                        print(f"净化扫描读取 GIF 失败 [{status}]: {e}")
                        continue
                    
                    if status not in self.collision_data:
                        self.collision_data[status] = {}
                        
                    # 2.1 删除多余的帧数据 (当实际 GIF 帧数变少时)
                    existing_frames = list(self.collision_data[status].keys())
                    for key in existing_frames:
                        if key.startswith("frame_"):
                            try:
                                f_idx = int(key.split("_")[1])
                                if f_idx >= actual_frames_count:
                                    del self.collision_data[status][key]
                            except:
                                pass
                                
                    # 2.2 自动补齐缺失的帧数据 (当实际 GIF 帧数增加时)
                    for f_idx in range(actual_frames_count):
                        frame_key = f"frame_{f_idx}"
                        if frame_key not in self.collision_data[status]:
                            self.collision_data[status][frame_key] = self.generate_default_boxes(status, f_idx)
                            
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.collision_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存 JSON 失败: {e}")
            return False

    def copy_current_box_to_all_frames(self):
        status = self.status_list[self.status_index]
        current_boxes = self.get_current_boxes()
        box_data = current_boxes.get(self.active_box_type)
        
        for i in range(len(self.frames)):
            frame_key = f"frame_{i}"
            if frame_key not in self.collision_data[status]:
                self.collision_data[status][frame_key] = {"hurtbox": None, "hitbox": None, "pushbox": None}
            self.collision_data[status][frame_key][self.active_box_type] = box_data
            
        # 复制完成后直接执行自动保存并记录已复制提示的计时器
        if self.save_data():
            self.copy_feedback_timer = pygame.time.get_ticks()

    def handle_event(self, event):
        # 0. 如果显示退出弹窗，拦截并处理弹窗交互
        if self.show_exit_dialog:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                m_pos = event.pos
                if self.exit_btn_confirm_rect.collidepoint(m_pos):
                    pygame.quit()
                    sys.exit(0)
                elif self.exit_btn_cancel_rect.collidepoint(m_pos):
                    self.show_exit_dialog = False
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_y, pygame.K_RETURN]:
                    pygame.quit()
                    sys.exit(0)
                elif event.key in [pygame.K_n, pygame.K_ESCAPE]:
                    self.show_exit_dialog = False
            return # 消耗并拦截所有其他操作



        # 1. 如果下拉列表展开，先由下拉列表处理点击
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            m_pos = event.pos
            if self.dropdown_expanded:
                # 遍历下拉列表选项
                for idx, char in enumerate(self.characters):
                    opt_rect = pygame.Rect(self.dropdown_rect.x, self.dropdown_rect.bottom + idx * 30, self.dropdown_rect.w, 30)
                    if opt_rect.collidepoint(m_pos):
                        self.char_index = idx
                        self.load_character()
                        self.dropdown_expanded = False
                        return # 消耗掉该点击事件
                
                # 如果点在外部，直接关闭下拉框
                if not self.dropdown_rect.collidepoint(m_pos):
                    self.dropdown_expanded = False
                    
            else:
                # 检查是否点击了下拉框头部
                if self.dropdown_rect.collidepoint(m_pos):
                    self.dropdown_expanded = True
                    return

        # 2. 正常快捷键事件
        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            is_ctrl = (mods & pygame.KMOD_CTRL) or (mods & pygame.KMOD_META)
            
            if event.key == pygame.K_ESCAPE:
                if self.drag_start:
                    self.drag_start = None
                    self.drag_current = None
                else:
                    self.show_exit_dialog = True
            # A / D 或 左右键切换帧 (Left / Right)
            elif event.key == pygame.K_a and not is_ctrl:
                if self.frames:
                    self.frame_index = (self.frame_index - 1) % len(self.frames)
            elif event.key == pygame.K_LEFT:
                if self.frames:
                    self.frame_index = (self.frame_index - 1) % len(self.frames)
            elif event.key == pygame.K_d:
                if self.frames:
                    self.frame_index = (self.frame_index + 1) % len(self.frames)
            elif event.key == pygame.K_RIGHT:
                if self.frames:
                    self.frame_index = (self.frame_index + 1) % len(self.frames)
            # W / S 或 上下键切换动作状态 (Up / Down)
            elif event.key == pygame.K_w:
                if self.status_list:
                    self.status_index = (self.status_index - 1) % len(self.status_list)
                    self.load_animation()
            elif event.key == pygame.K_UP:
                if self.status_list:
                    self.status_index = (self.status_index - 1) % len(self.status_list)
                    self.load_animation()
            elif event.key == pygame.K_s and not is_ctrl:
                if self.status_list:
                    self.status_index = (self.status_index + 1) % len(self.status_list)
                    self.load_animation()
            elif event.key == pygame.K_DOWN:
                if self.status_list:
                    self.status_index = (self.status_index + 1) % len(self.status_list)
                    self.load_animation()
            # 数字键 1 / 2 / 3 切换三种 box 绘制类型
            elif event.key == pygame.K_1:
                self.active_box_type = 'hurtbox'
            elif event.key == pygame.K_2:
                self.active_box_type = 'hitbox'
            elif event.key == pygame.K_3:
                self.active_box_type = 'pushbox'
            elif event.key == pygame.K_f:
                self.to_right = not self.to_right
            # Ctrl + S 或 Command + S 保存当前配置
            elif event.key == pygame.K_s and is_ctrl:
                if self.save_data():
                    self.save_feedback_timer = pygame.time.get_ticks()
                    print("碰撞数据保存成功！")
            elif event.key in [pygame.K_c, pygame.K_DELETE]:
                boxes = self.get_current_boxes()
                boxes[self.active_box_type] = None
                if self.save_data():
                    self.save_feedback_timer = pygame.time.get_ticks()
            # R 键同步复制当前选中的碰撞盒类型到所有帧 (直接复制并提示)
            elif event.key == pygame.K_r:
                self.copy_current_box_to_all_frames()
            # B 键切换编辑网格背景主题 (深色 / 浅色 - 全局大换肤)
            elif event.key == pygame.K_b:
                self.theme_mode = 'light' if self.theme_mode == 'dark' else 'dark'
                theme = self.THEMES[self.theme_mode]
                self.BG_COLOR = theme['bg']
                self.GRID_COLOR = theme['grid']
                self.GRID_HIGHLIGHT = theme['highlight']
                self.PANEL_COLOR = theme['panel']
                self.PANEL_BORDER = theme['panel_border']
                self.TEXT_COLOR = theme['text']
                self.TEXT_MUTED = theme['text_muted']
                
                # 同步更新至子模块 Inspector 面板
                self.inspector.theme_mode = self.theme_mode
                self.inspector.TEXT_COLOR = self.TEXT_COLOR
                self.inspector.TEXT_MUTED = self.TEXT_MUTED
                self.inspector.PANEL_COLOR = self.PANEL_COLOR
                self.inspector.PANEL_BORDER = self.PANEL_BORDER

        # 3. 鼠标左键框选绘制与数值面板交互
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.frames and not self.dropdown_expanded:
                # 确定点击位置在右侧 Inspector 区域内
                if event.pos[0] >= 1040 and event.pos[1] > 70:
                    active_status = self.status_list[self.status_index] if self.status_list else "None"
                    if self.inspector.handle_click(event.pos, active_status, self.collision_data):
                        if self.save_data():
                            self.save_feedback_timer = pygame.time.get_ticks()
                # 确定点击位置在中央逻辑绘制画布内 (240 < x < 1040 且 y > 70)
                elif 240 < event.pos[0] < 1040 and event.pos[1] > 70:
                    self.drag_start = event.pos
                    self.drag_current = event.pos
                    
        elif event.type == pygame.MOUSEMOTION:
            if self.drag_start:
                self.drag_current = event.pos
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.drag_start and self.frames:
                x1, y1 = self.drag_start
                x2, y2 = event.pos
                
                char_surf = self.frames[self.frame_index]
                w, h = char_surf.get_size()
                
                img_x = 1280 // 2 - w // 2
                img_y = 720 // 2 - h // 2
                
                rx1, rx2 = min(x1, x2), max(x1, x2)
                ry1, ry2 = min(y1, y2), max(y1, y2)
                
                local_x = rx1 - img_x
                local_y = ry1 - img_y
                local_w = rx2 - rx1
                local_h = ry2 - ry1
                
                if local_w > 4 and local_h > 4:
                    boxes = self.get_current_boxes()
                    if not self.to_right:
                        local_x = w - local_x - local_w
                    boxes[self.active_box_type] = [int(local_x), int(local_y), int(local_w), int(local_h)]
                    # 拖拽绘制完成后直接执行自动保存 (Auto-save) 并显示屏幕反馈！
                    if self.save_data():
                        self.save_feedback_timer = pygame.time.get_ticks()
                    
                self.drag_start = None
                self.drag_current = None

    def run(self, dt) -> SceneStatus:
        self.screen.fill(self.BG_COLOR)
        
        # 绘制背景的极客风 CAD 方格网 (Sleek Grid Layout)
        self.draw_cad_grid()
        
        self.draw_character_frame()
        self.draw_ui()
        
        return SceneStatus.EDITOR

    def draw_cad_grid(self):
        """在绘制区域渲染科技感的虚线/实线网格背景"""
        grid_size = 40
        # 绘制横线
        for y in range(70, 720 - 45, grid_size):
            pygame.draw.line(self.screen, self.GRID_COLOR, (240, y), (1280 - 240, y), 1)
        # 绘制竖线
        for x in range(240, 1280 - 240, grid_size):
            pygame.draw.line(self.screen, self.GRID_COLOR, (x, 70), (x, 720 - 45), 1)
            
        # 绘制十字轴高亮线
        pygame.draw.line(self.screen, self.GRID_HIGHLIGHT, (1280 // 2, 70), (1280 // 2, 720 - 45), 2)
        pygame.draw.line(self.screen, self.GRID_HIGHLIGHT, (240, 720 // 2), (1280 - 240, 720 // 2), 2)

    def draw_character_frame(self):
        if not self.frames:
            return
            
        char_surf = self.frames[self.frame_index]
        w, h = char_surf.get_size()
        
        img_x = 1280 // 2 - w // 2
        img_y = 720 // 2 - h // 2
        
        # 绘制地平基准线 (霓虹蓝激光线，贯穿整个屏幕 0 到 1280)
        pygame.draw.line(self.screen, (30, 144, 255, 120), (0, img_y + h), (1280, img_y + h), 2)
        
        # 翻转绘制
        display_surf = char_surf
        if not self.to_right:
            display_surf = pygame.transform.flip(char_surf, True, False)
            
        self.screen.blit(display_surf, (img_x, img_y))
        
        # 绘制碰撞框
        boxes = self.get_current_boxes()
        
        # 🟢 Hurtbox
        if boxes["hurtbox"]:
            bx, by, bw, bh = boxes["hurtbox"]
            if not self.to_right:
                bx = w - bx - bw
            pygame.draw.rect(self.screen, self.HURTBOX_COLOR, (img_x + bx, img_y + by, bw, bh), 2)
            lbl = self.font_small.render("Hurtbox 受击", True, self.HURTBOX_COLOR)
            self.screen.blit(lbl, (img_x + bx, img_y + by - 18))
            
        # 🔴 Hitbox
        if boxes["hitbox"]:
            bx, by, bw, bh = boxes["hitbox"]
            if not self.to_right:
                bx = w - bx - bw
            pygame.draw.rect(self.screen, self.HITBOX_COLOR, (img_x + bx, img_y + by, bw, bh), 2)
            lbl = self.font_small.render("Hitbox 攻击", True, self.HITBOX_COLOR)
            self.screen.blit(lbl, (img_x + bx, img_y + by - 18))
            
        # 🔵 Pushbox
        if boxes["pushbox"]:
            bx, by, bw, bh = boxes["pushbox"]
            if not self.to_right:
                bx = w - bx - bw
            pygame.draw.rect(self.screen, self.PUSHBOX_COLOR, (img_x + bx, img_y + by, bw, bh), 2)
            lbl = self.font_small.render("Pushbox 推挤", True, self.PUSHBOX_COLOR)
            self.screen.blit(lbl, (img_x + bx, img_y + by - 18))
            
        # 实时绘制正在拖拽的预览框
        if self.drag_start and self.drag_current:
            x1, y1 = self.drag_start
            x2, y2 = self.drag_current
            rx, ry = min(x1, x2), min(y1, y2)
            rw, rh = abs(x2 - x1), abs(y2 - y1)
            
            if self.active_box_type == 'hurtbox':
                color = self.HURTBOX_COLOR
                label = "Hurtbox 受击 (绘制中)"
            elif self.active_box_type == 'hitbox':
                color = self.HITBOX_COLOR
                label = "Hitbox 攻击 (绘制中)"
            else:
                color = self.PUSHBOX_COLOR
                label = "Pushbox 推挤 (绘制中)"
                
            # 绘制实线预览框 (厚度为 1 像素)
            pygame.draw.rect(self.screen, color, (rx, ry, rw, rh), 1)
            
            # 绘制预览文字提示
            lbl = self.font_small.render(label, True, color)
            lbl_y = ry - 18 if ry - 18 > 70 else ry + rh + 4
            self.screen.blit(lbl, (rx, lbl_y))
    def draw_ui(self):
        import math
        # --- 1. 顶部操作栏 ---
        pygame.draw.rect(self.screen, self.PANEL_COLOR, (0, 0, 1280, 70))
        pygame.draw.line(self.screen, self.PANEL_BORDER, (0, 70), (1280, 70), 1)
        
        title = self.font_large.render("FreeFight 可视化编辑器", True, self.TEXT_COLOR)
        self.screen.blit(title, (25, 18))
        
        # 绘制 1/2/3 绘制状态栏 (已彻底移除 emoji 字符，防止 Mac 上显示为方框)
        modes = [
            ('hurtbox', '1 键 受击盒 (Hurtbox)', self.HURTBOX_COLOR),
            ('hitbox', '2 键 攻击盒 (Hitbox)', self.HITBOX_COLOR),
            ('pushbox', '3 键 推挤盒 (Pushbox)', self.PUSHBOX_COLOR)
        ]
        
        x_btn = 600
        for m_id, m_lbl, m_col in modes:
            is_active = (self.active_box_type == m_id)
            if self.theme_mode == 'dark':
                btn_bg = (40, 40, 52) if is_active else (20, 20, 24)
            else:
                btn_bg = (230, 230, 240) if is_active else (245, 245, 250)
            btn_rect = pygame.Rect(x_btn, 16, 205, 38)
            pygame.draw.rect(self.screen, btn_bg, btn_rect, 0, 8)
            if is_active:
                pygame.draw.rect(self.screen, m_col, btn_rect, 2, 8)
                
            # 物理绘制：在按钮内部左侧画一个带呼吸动画的发光状态圆点
            if is_active:
                pulse_r = math.sin(pygame.time.get_ticks() * 0.007) * 1.5 + 5.5
                pygame.draw.circle(self.screen, m_col, (btn_rect.x + 20, btn_rect.centery), int(pulse_r))
                # 绘制外发光环
                pygame.draw.circle(self.screen, m_col, (btn_rect.x + 20, btn_rect.centery), int(pulse_r + 2), 1)
            else:
                pygame.draw.circle(self.screen, self.TEXT_MUTED, (btn_rect.x + 20, btn_rect.centery), 4)
            
            # 绘制文本，向右偏移 32 像素以留出圆点空间
            txt = self.font_small.render(m_lbl, True, m_col if is_active else self.TEXT_MUTED)
            txt_r = txt.get_rect(midleft=(btn_rect.x + 32, btn_rect.centery))
            self.screen.blit(txt, txt_r)
            x_btn += 215
 
        # --- 2. 左侧控制面板 ---
        pygame.draw.rect(self.screen, self.PANEL_COLOR, (0, 70, 240, 720 - 70))
        pygame.draw.line(self.screen, self.PANEL_BORDER, (240, 70), (240, 720), 1)
        
        # 下拉菜单渲染 (Dropdown menu for character selection)
        y = 85
        lbl = self.font_medium.render("选择角色", True, self.TEXT_MUTED)
        self.screen.blit(lbl, (20, y))
        
        # 下拉框背景与选定角色显示
        dropdown_bg = (20, 20, 24) if self.theme_mode == 'dark' else (245, 245, 250)
        pygame.draw.rect(self.screen, dropdown_bg, self.dropdown_rect, 0, 6)
        pygame.draw.rect(self.screen, self.PANEL_BORDER, self.dropdown_rect, 1, 6)
        
        char_txt = self.font_medium.render(self.char_name.capitalize(), True, self.TEXT_COLOR)
        self.screen.blit(char_txt, (self.dropdown_rect.x + 12, self.dropdown_rect.y + 7))
        
        # 下拉角箭头 (▼ / ▲) 物理绘制，避免跨平台渲染乱码方框
        arrow_x = self.dropdown_rect.right - 20
        arrow_y = self.dropdown_rect.centery
        if self.dropdown_expanded:
            # 向上实心三角形
            pygame.draw.polygon(self.screen, self.TEXT_MUTED, [
                (arrow_x - 5, arrow_y + 3),
                (arrow_x + 5, arrow_y + 3),
                (arrow_x, arrow_y - 4)
            ])
        else:
            # 向下实心三角形
            pygame.draw.polygon(self.screen, self.TEXT_MUTED, [
                (arrow_x - 5, arrow_y - 3),
                (arrow_x + 5, arrow_y - 3),
                (arrow_x, arrow_y + 4)
            ])
        
        # 动作状态列表渲染
        y = 180
        lbl = self.font_medium.render("动作状态 (按键 W/S)", True, self.TEXT_MUTED)
        self.screen.blit(lbl, (20, y))
        y += 35
        
        v_range = 14
        start = max(0, self.status_index - v_range // 2)
        end = min(len(self.status_list), start + v_range)
        for idx in range(start, end):
            is_cur = (idx == self.status_index)
            color = self.TEXT_COLOR if is_cur else self.TEXT_MUTED
            
            # 物理绘制取代 unrenderable unicode 字符 "▶"，完全避免跨平台乱码方框
            txt = self.font_small.render(f"   {self.status_list[idx]}", True, color)
            
            # 高亮选中动作背景与左侧指示灯
            if is_cur:
                item_bg = pygame.Rect(10, y - 2, 220, 22)
                item_hl = (40, 40, 52) if self.theme_mode == 'dark' else (230, 230, 240)
                pygame.draw.rect(self.screen, item_hl, item_bg, 0, 4)
                
                # 绘制极客感十足的蓝色垂直指示线条
                pygame.draw.rect(self.screen, self.ACCENT_COLOR, (15, y + 4, 4, 11), 0, 2)
                
            self.screen.blit(txt, (18, y))
            y += 24
            
        # --- 3. 右侧极客风 Inspector 面板 (招式与角色属性配置选项卡) ---
        m_pos = pygame.mouse.get_pos()
        self.inspector.draw(self.screen, m_pos, self.status_list[self.status_index] if self.status_list else "None", self.collision_data)

        # --- 4. 底部状态栏 ---
        pygame.draw.rect(self.screen, self.PANEL_COLOR, (0, 720 - 45, 1280, 45))
        pygame.draw.line(self.screen, self.PANEL_BORDER, (0, 720 - 45), (1280, 720 - 45), 1)
        
        status_str = f"角色: {self.char_name.capitalize()} | 动作: {self.status_list[self.status_index] if self.status_list else '无'} | 当前帧数: {self.frame_index + 1} / {len(self.frames)}"
        txt = self.font_medium.render(status_str, True, self.TEXT_COLOR)
        self.screen.blit(txt, (25, 720 - 32))
        
        # --- 5. 展开下拉菜单选项 (绘制在最上层) ---
        if self.dropdown_expanded:
            drop_items_h = len(self.characters) * 30
            drop_panel = pygame.Rect(self.dropdown_rect.x, self.dropdown_rect.bottom, self.dropdown_rect.w, drop_items_h)
            drop_panel_bg = (20, 20, 24) if self.theme_mode == 'dark' else (245, 245, 250)
            pygame.draw.rect(self.screen, drop_panel_bg, drop_panel, 0, 6)
            pygame.draw.rect(self.screen, self.PANEL_BORDER, drop_panel, 1, 6)
            
            # 获取鼠标位置以高亮 Hover 选项
            m_x, m_y = pygame.mouse.get_pos()
            
            for idx, char in enumerate(self.characters):
                opt_rect = pygame.Rect(self.dropdown_rect.x, self.dropdown_rect.bottom + idx * 30, self.dropdown_rect.w, 30)
                is_hover = opt_rect.collidepoint(m_x, m_y)
                
                if is_hover:
                    pygame.draw.rect(self.screen, self.ACCENT_COLOR, opt_rect, 0, 4)
                    
                txt_col = self.TEXT_COLOR if is_hover else self.TEXT_MUTED
                txt = self.font_small.render(char.capitalize(), True, txt_col)
                self.screen.blit(txt, (opt_rect.x + 15, opt_rect.y + 6))

        # --- 6. 绘制退出确认弹窗 (Exit Confirmation Modal, 绘制在最上层) ---
        if self.show_exit_dialog:
            # 半透明遮罩背景
            overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            # 科技感弹窗主体
            modal_rect = pygame.Rect(1280 // 2 - 200, 720 // 2 - 100, 400, 200)
            pygame.draw.rect(self.screen, self.PANEL_COLOR, modal_rect, 0, 12)
            pygame.draw.rect(self.screen, self.PANEL_BORDER, modal_rect, 2, 12)
            
            # 顶部紫色高亮修饰线
            pygame.draw.line(self.screen, self.ACCENT_COLOR, (modal_rect.left + 20, modal_rect.top + 45), (modal_rect.right - 20, modal_rect.top + 45), 1)
            
            # 提示文本
            t1 = self.font_medium.render("确认退出编辑器吗？", True, self.TEXT_COLOR)
            t1_r = t1.get_rect(centerx=1280 // 2, top=modal_rect.top + 20)
            self.screen.blit(t1, t1_r)
            
            t2 = self.font_small.render("所有碰撞修改均已实时自动保存", True, self.TEXT_MUTED)
            t2_r = t2.get_rect(centerx=1280 // 2, top=modal_rect.top + 60)
            self.screen.blit(t2, t2_r)
            
            # 获取当前鼠标位置以处理 Hover 态效果
            m_pos = pygame.mouse.get_pos()
            
            # "确定" 按钮 (Y / Enter)
            btn1_hover = self.exit_btn_confirm_rect.collidepoint(m_pos)
            btn1_bg = self.ACCENT_COLOR if btn1_hover else ((40, 40, 52) if self.theme_mode == 'dark' else (230, 230, 240))
            pygame.draw.rect(self.screen, btn1_bg, self.exit_btn_confirm_rect, 0, 6)
            btn1_txt = self.font_small.render("确定 (Y / Enter)", True, self.TEXT_COLOR)
            btn1_txt_r = btn1_txt.get_rect(center=self.exit_btn_confirm_rect.center)
            self.screen.blit(btn1_txt, btn1_txt_r)
            
            # "取消" 按钮 (N / ESC)
            btn2_hover = self.exit_btn_cancel_rect.collidepoint(m_pos)
            btn2_bg = ((56, 56, 68) if btn2_hover else (30, 30, 38)) if self.theme_mode == 'dark' else ((200, 200, 215) if btn2_hover else (220, 220, 228))
            pygame.draw.rect(self.screen, btn2_bg, self.exit_btn_cancel_rect, 0, 6)
            pygame.draw.rect(self.screen, self.PANEL_BORDER, self.exit_btn_cancel_rect, 1, 6)
            btn2_txt = self.font_small.render("取消 (N / ESC)", True, self.TEXT_COLOR)
            btn2_txt_r = btn2_txt.get_rect(center=self.exit_btn_cancel_rect.center)
            self.screen.blit(btn2_txt, btn2_txt_r)

        # --- 7. 绘制复制成功的轻量提示框 (Copy Success Toast Feedback) ---
        now = pygame.time.get_ticks()
        if now < self.copy_feedback_timer + 1500:
            toast_w = 420
            toast_h = 50
            toast_rect = pygame.Rect(1280 // 2 - toast_w // 2, 85, toast_w, toast_h)
            
            # 磨砂背景与霓虹紫色发光框
            pygame.draw.rect(self.screen, self.PANEL_COLOR, toast_rect, 0, 10)
            pygame.draw.rect(self.screen, self.ACCENT_COLOR, toast_rect, 2, 10)
            
            # 提示文本与类型名称
            box_name = "受击盒 (Hurtbox)" if self.active_box_type == 'hurtbox' else \
                       "攻击盒 (Hitbox)" if self.active_box_type == 'hitbox' else \
                       "推挤盒 (Pushbox)"
            msg = f"已成功复制 [{box_name}] 到该动作所有帧！"
            txt = self.font_small.render(msg, True, self.TEXT_COLOR)
            txt_r = txt.get_rect(center=toast_rect.center)
            self.screen.blit(txt, txt_r)
