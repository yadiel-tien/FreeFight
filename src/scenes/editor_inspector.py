import pygame

class EditorInspector:
    def __init__(self, font_small, font_medium, font_large, accent_color, text_color, text_muted, panel_color, panel_border):
        self.font_small = font_small
        self.font_medium = font_medium
        self.font_large = font_large
        self.ACCENT_COLOR = accent_color
        self.TEXT_COLOR = text_color
        self.TEXT_MUTED = text_muted
        self.PANEL_COLOR = panel_color
        self.PANEL_BORDER = panel_border
        
        self.right_tab = 'move' # 'move' (招式), 'base' (角色属性), 'help' (指令帮助)
        
        # 选项卡控制区域
        self.tab_rects = {
            'move': pygame.Rect(1040, 70, 80, 40),
            'base': pygame.Rect(1120, 70, 80, 40),
            'help': pygame.Rect(1200, 70, 80, 40)
        }
        
        # 选项卡滑块微动画
        self.indicator_x = 1040.0
        
        # 战斗动作定义
        self.combat_moves = ['attack', 'combo', 'dash attack', 'jump attack', 'super move 1', 'super move 2', 'super move 3', 'finisher']
        self.theme_mode = 'dark'
        
    def draw(self, screen, m_pos, active_status, collision_data):
        # 0. 根据 theme_mode 选择内部控制色，实现白昼/黑夜完美主题对比度适配
        if self.theme_mode == 'dark':
            row_bg = (20, 20, 24)
            btn_bg = (35, 35, 42)
            btn_hover = (56, 56, 68)
            tab_bar_bg = (20, 20, 24)
            tab_hover = (32, 32, 40)
        else:
            row_bg = (245, 245, 250)
            btn_bg = (220, 220, 228)
            btn_hover = (200, 200, 212)
            tab_bar_bg = (240, 240, 245)
            tab_hover = (225, 225, 235)

        # 1. 绘制右侧主面板背景与左边界线
        pygame.draw.rect(screen, self.PANEL_COLOR, (1040, 70, 240, 650))
        pygame.draw.line(screen, self.PANEL_BORDER, (1040, 70), (1040, 720), 1)
        
        # 2. 绘制顶部 Tab 切换条
        pygame.draw.rect(screen, tab_bar_bg, (1040, 70, 240, 40))
        pygame.draw.line(screen, self.PANEL_BORDER, (1040, 110), (1280, 110), 1)
        
        # 微动画插值计算底条位置
        target_x = self.tab_rects[self.right_tab].x
        self.indicator_x += (target_x - self.indicator_x) * 0.25
        
        # 绘制滑块指示器 (霓虹紫色呼吸光)
        pygame.draw.rect(screen, self.ACCENT_COLOR, (int(self.indicator_x), 108, 80, 3), 0, 2)
        
        labels = {
            'move': '招式属性',
            'base': '角色属性',
            'help': '快捷指令'
        }
        
        for m_id, rect in self.tab_rects.items():
            is_active = (self.right_tab == m_id)
            is_hover = rect.collidepoint(m_pos)
            
            # Hover 微微高亮
            if is_hover and not is_active:
                pygame.draw.rect(screen, tab_hover, rect)
                
            txt_color = self.TEXT_COLOR if is_active else (self.TEXT_COLOR if is_hover else self.TEXT_MUTED)
            txt = self.font_small.render(labels[m_id], True, txt_color)
            txt_r = txt.get_rect(center=rect.center)
            screen.blit(txt, txt_r)
            
            # 选项卡分隔竖线
            if m_id != 'help':
                pygame.draw.line(screen, self.PANEL_BORDER, (rect.right, 75), (rect.right, 105), 1)
                
        # 3. 渲染各个面板的具体内容
        if self.right_tab == 'move':
            self._draw_move_tab(screen, m_pos, active_status, collision_data, row_bg, btn_bg, btn_hover)
        elif self.right_tab == 'base':
            self._draw_base_tab(screen, m_pos, collision_data, row_bg, btn_bg, btn_hover)
        elif self.right_tab == 'help':
            self._draw_help_tab(screen, row_bg)
            
    def _draw_move_tab(self, screen, m_pos, active_status, collision_data, row_bg, btn_bg, btn_hover):
        y = 125
        
        # 显示当前招式名称
        title_txt = self.font_medium.render(f"当前动作: {active_status}", True, self.TEXT_COLOR)
        screen.blit(title_txt, (1060, y))
        y += 35
        
        if active_status not in self.combat_moves:
            # 普通非战斗动作 (例如 idle, walk, run 等) 友情提示
            pygame.draw.rect(screen, row_bg, (1055, y, 210, 150), 0, 6)
            pygame.draw.rect(screen, self.PANEL_BORDER, (1055, y, 210, 150), 1, 6)
            
            msg_lines = [
                "当前动作为非战斗状态",
                "无需配置招式数值属性。",
                "请在左侧选择：",
                "attack (轻拳)",
                "super move (大招)",
                "等战斗招式进行参数编辑。"
            ]
            msg_y = y + 15
            for line in msg_lines:
                txt = self.font_small.render(line, True, self.TEXT_MUTED)
                screen.blit(txt, (1070, msg_y))
                msg_y += 22
            return
            
        # 战斗招式属性微调渲染
        move_stats = collision_data.setdefault("move_stats", {})
        stats = move_stats.setdefault(active_status, {
            "damage": 50, "knockback": 10, "startup": 0.0, "recovery": 0.08, "cost": 0
        })
        
        rows = [
            ("damage", "伤害 (Damage)", stats.get("damage", 50), 5, "整数"),
            ("knockback", "击退 (Knockback)", stats.get("knockback", 10), 5, "整数"),
            ("cost", "耗能 (MP Cost)", stats.get("cost", 0), 5, "整数"),
            ("startup", "前摇时间 (Startup)", stats.get("startup", 0.0), 0.05, "小数"),
            ("recovery", "收招僵直 (Recovery)", stats.get("recovery", 0.08), 0.05, "小数")
        ]
        
        for key, label, val, step, val_type in rows:
            # 绘制背景条
            row_rect = pygame.Rect(1055, y, 210, 52)
            pygame.draw.rect(screen, row_bg, row_rect, 0, 6)
            pygame.draw.rect(screen, self.PANEL_BORDER, row_rect, 1, 6)
            
            # 绘制标签名称
            lbl = self.font_small.render(label, True, self.TEXT_MUTED)
            screen.blit(lbl, (1065, y + 6))
            
            # 计算按钮位置
            btn_sub = pygame.Rect(1065, y + 24, 30, 22)
            btn_add = pygame.Rect(1220, y + 24, 30, 22)
            
            # 按钮 Hover 态处理
            sub_hover = btn_sub.collidepoint(m_pos)
            add_hover = btn_add.collidepoint(m_pos)
            
            pygame.draw.rect(screen, btn_hover if sub_hover else btn_bg, btn_sub, 0, 4)
            pygame.draw.rect(screen, btn_hover if add_hover else btn_bg, btn_add, 0, 4)
            
            # 绘制 "-" 和 "+" 符号文本
            txt_sub = self.font_medium.render("-", True, self.TEXT_COLOR)
            txt_add = self.font_medium.render("+", True, self.TEXT_COLOR)
            screen.blit(txt_sub, txt_sub.get_rect(center=btn_sub.center))
            screen.blit(txt_add, txt_add.get_rect(center=btn_add.center))
            
            # 绘制数值框与当前属性值
            val_rect = pygame.Rect(1100, y + 24, 115, 22)
            val_str = f"{val}" if val_type == "整数" else f"{val:.2f}s"
            txt_val = self.font_small.render(val_str, True, self.ACCENT_COLOR)
            screen.blit(txt_val, txt_val.get_rect(center=val_rect.center))
            
            y += 58
            
    def _draw_base_tab(self, screen, m_pos, collision_data, row_bg, btn_bg, btn_hover):
        y = 125
        
        # 显示基础属性标题
        title_txt = self.font_medium.render("角色全局基础物理属性", True, self.TEXT_COLOR)
        screen.blit(title_txt, (1060, y))
        y += 35
        
        # 角色基础属性数据微调渲染
        char_stats = collision_data.setdefault("character_stats", {
            "max_health": 1000, "speed": 150, "gravity": 800, "jump_strength": 500
        })
        
        rows = [
            ("max_health", "最大血量 (Max HP)", char_stats.get("max_health", 1000), 50),
            ("speed", "移动速度 (Speed)", char_stats.get("speed", 150), 10),
            ("gravity", "重力加速度 (Gravity)", char_stats.get("gravity", 800), 50),
            ("jump_strength", "跳跃力度 (Jump Strength)", char_stats.get("jump_strength", 500), 50)
        ]
        
        for key, label, val, step in rows:
            # 绘制背景条
            row_rect = pygame.Rect(1055, y, 210, 52)
            pygame.draw.rect(screen, row_bg, row_rect, 0, 6)
            pygame.draw.rect(screen, self.PANEL_BORDER, row_rect, 1, 6)
            
            # 绘制标签名称
            lbl = self.font_small.render(label, True, self.TEXT_MUTED)
            screen.blit(lbl, (1065, y + 6))
            
            # 计算按钮位置
            btn_sub = pygame.Rect(1065, y + 24, 30, 22)
            btn_add = pygame.Rect(1220, y + 24, 30, 22)
            
            # 按钮 Hover 态处理
            sub_hover = btn_sub.collidepoint(m_pos)
            add_hover = btn_add.collidepoint(m_pos)
            
            pygame.draw.rect(screen, btn_hover if sub_hover else btn_bg, btn_sub, 0, 4)
            pygame.draw.rect(screen, btn_hover if add_hover else btn_bg, btn_add, 0, 4)
            
            # 绘制 "-" 和 "+" 符号文本
            txt_sub = self.font_medium.render("-", True, self.TEXT_COLOR)
            txt_add = self.font_medium.render("+", True, self.TEXT_COLOR)
            screen.blit(txt_sub, txt_sub.get_rect(center=btn_sub.center))
            screen.blit(txt_add, txt_add.get_rect(center=btn_add.center))
            
            # 绘制数值框与当前属性值
            val_rect = pygame.Rect(1100, y + 24, 115, 22)
            txt_val = self.font_small.render(f"{val}", True, self.ACCENT_COLOR)
            screen.blit(txt_val, txt_val.get_rect(center=val_rect.center))
            
            y += 58
            
    def _draw_help_tab(self, screen, row_bg):
        y_hint = 130
        hints = [
            ("A / D", "左右切换当前动作帧"),
            ("W / S", "上下切换动作状态"),
            ("Mouse Drag", "按鼠标左键框选绘制"),
            ("1 / 2 / 3", "切换 绿/红/蓝 盒子类型"),
            ("Delete / C", "清空当前帧指定碰撞盒"),
            ("F", "镜像翻转角色朝向"),
            ("R", "复制当前框类型至所有帧"),
            ("B", "切换主题 (深色/浅色)"),
            ("ESC", "取消绘制 / 退出确认")
        ]
        
        for key, desc in hints:
            if key in ["A / D", "W / S"]:
                tag_col = (165, 177, 194)  # 银灰：导航
            elif key in ["Mouse Drag", "1 / 2 / 3", "Delete / C"]:
                tag_col = (30, 144, 255)   # 极光蓝：绘图
            else:
                tag_col = self.ACCENT_COLOR  # 霓虹紫：操作
                
            item_r = pygame.Rect(1055, y_hint - 2, 210, 40)
            pygame.draw.rect(screen, row_bg, item_r, 0, 5)
            pygame.draw.rect(screen, (35, 35, 42), item_r, 1, 5)
            
            # 左侧精细分类霓虹标签线
            pygame.draw.rect(screen, tag_col, (1055, y_hint + 4, 3, 28), 0, 2)
            
            t_key = self.font_small.render(key, True, self.TEXT_COLOR)
            t_desc = self.font_small.render(desc, True, self.TEXT_MUTED)
            screen.blit(t_key, (1067, y_hint + 2))
            screen.blit(t_desc, (1067, y_hint + 18))
            y_hint += 46

    def handle_click(self, m_pos, active_status, collision_data) -> bool:
        """
        拦截并处理 Inspector 面板上的按钮点击事件。
        返回 True 表示数据被修改，需要触发 auto-save。
        """
        # 1. 检测 Tab 切换
        for m_id, rect in self.tab_rects.items():
            if rect.collidepoint(m_pos):
                if self.right_tab != m_id:
                    self.right_tab = m_id
                    return True
                return False
                
        # 2. 招式属性面板微调 clicks
        if self.right_tab == 'move' and active_status in self.combat_moves:
            stats = collision_data.setdefault("move_stats", {}).setdefault(active_status, {
                "damage": 50, "knockback": 10, "startup": 0.0, "recovery": 0.08, "cost": 0
            })
            
            y = 160 # 第一个微调控制项的起始 y 坐标
            rows = [
                ("damage", 5, 0, 999),
                ("knockback", 5, 0, 500),
                ("cost", 5, 0, 100),
                ("startup", 0.05, 0.0, 5.0),
                ("recovery", 0.05, 0.0, 5.0)
            ]
            
            for key, step, min_val, max_val in rows:
                btn_sub = pygame.Rect(1065, y + 24, 30, 22)
                btn_add = pygame.Rect(1220, y + 24, 30, 22)
                
                if btn_sub.collidepoint(m_pos):
                    # 减小数值，对于浮点数使用 round 防止浮点精度误差
                    val = stats.get(key, 0.0)
                    stats[key] = max(min_val, round(val - step, 2))
                    return True
                elif btn_add.collidepoint(m_pos):
                    # 增加数值
                    val = stats.get(key, 0.0)
                    stats[key] = min(max_val, round(val + step, 2))
                    return True
                
                y += 58
                
        # 3. 角色基础属性面板微调 clicks
        elif self.right_tab == 'base':
            char_stats = collision_data.setdefault("character_stats", {
                "max_health": 1000, "speed": 150, "gravity": 800, "jump_strength": 500
            })
            
            y = 160
            rows = [
                ("max_health", 50, 100, 5000),
                ("speed", 10, 10, 800),
                ("gravity", 50, 100, 3000),
                ("jump_strength", 50, 100, 2000)
            ]
            
            for key, step, min_val, max_val in rows:
                btn_sub = pygame.Rect(1065, y + 24, 30, 22)
                btn_add = pygame.Rect(1220, y + 24, 30, 22)
                
                if btn_sub.collidepoint(m_pos):
                    val = char_stats.get(key, 0)
                    char_stats[key] = max(min_val, val - step)
                    return True
                elif btn_add.collidepoint(m_pos):
                    val = char_stats.get(key, 0)
                    char_stats[key] = min(max_val, val + step)
                    return True
                
                y += 58
                
        return False
