import random
import pygame
from src.scenes.scene import Scene, SceneStatus
from src.core.input import GameInput, Controller
from src.core.support import resource_path, import_pic, import_gif
from src.core.constants import SCREEN_WIDTH, SCREEN_HEIGHT
from src.entities.player import Player
from src.core.timer import Timer
from src.core.config import config


def get_short_key_name(key_name):
    key_name = key_name.upper()
    mapping = {
        'SPACE': 'SPACE',
        'RETURN': 'ENTER',
        'ESCAPE': 'ESC',
        'LEFT SHIFT': 'LSHIFT',
        'RIGHT SHIFT': 'RSHIFT',
        'LEFT CTRL': 'LCTRL',
        'RIGHT CTRL': 'RCTRL',
        'LEFT ALT': 'LALT',
        'RIGHT ALT': 'RALT',
        'BACKSPACE': 'BACK',
    }
    return mapping.get(key_name, key_name)


class MockController(Controller):
    """虚拟控制器，专门用于锁定沙袋假人，使其保持静止不做出任何输入动作"""
    def __init__(self):
        super().__init__()
        class EmptyAction:
            pressed = False
            just_pressed = False
            just_released = False
            
        self.actions = {
            'up': EmptyAction(), 'down': EmptyAction(), 'left': EmptyAction(), 'right': EmptyAction(),
            'jump': EmptyAction(), 'attack': EmptyAction(), 'super move 1': EmptyAction(),
            'super move 2': EmptyAction(), 'finisher': EmptyAction(), 'taunt': EmptyAction()
        }

    def performed(self, action: str) -> bool:
        return False


class DamageText(pygame.sprite.Sprite):
    """高度优化的打击伤害动态飘字粒子 (Arcade Damage Numbers)"""
    def __init__(self, damage, pos, groups):
        super().__init__(groups)
        
        # 1. 动态自适应尺寸与霓虹色彩系统
        if damage < 50:
            font_size = 28
            text_color = (100, 240, 255)     # Cyber Cyan (轻度攻击)
        elif damage < 100:
            font_size = 40
            text_color = (255, 215, 0)       # Golden Gold (中度普攻)
        elif damage < 250:
            font_size = 60
            text_color = (255, 110, 0)       # Fiery Orange (大招爆发)
        else:
            font_size = 85
            text_color = (255, 0, 90)        # Hyper Crimson Pink (终极斩杀)
            
        self.font = pygame.font.Font(resource_path('assets/font/impact.ttf'), font_size)
        text_surf = self.font.render(str(damage), True, text_color)
        w, h = text_surf.get_size()
        
        # 2. 创建 100% 透明无背景的 Surface，并强制清理颜色通道，去掉 convert_alpha 保证在 macOS 下不产生黑框
        self.image = pygame.Surface((w + 8, h + 8), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        
        # 3. 绘制高对比度微弱立体阴影 (仅右下偏移 2 像素)，绝不产生方框阴影感
        shadow_surf = self.font.render(str(damage), True, (15, 10, 25))
        self.image.blit(shadow_surf, (2, 2))
                    
        # 4. 绘制中心高亮色彩文本
        self.image.blit(text_surf, (0, 0))
        
        self.pos = pygame.math.Vector2(pos)
        self.rect = self.image.get_rect(center=self.pos)
        
        # 5. 根据伤害重感模拟不同的爆发式抛逸初速度与生命周期
        self.lifetime = 0.80 if damage >= 100 else 0.60
        self.max_lifetime = self.lifetime
        
        vx = random.uniform(-60, 60) if damage >= 100 else random.uniform(-35, 35)
        vy = -230 if damage >= 100 else -170
        self.velocity = pygame.math.Vector2(vx, vy)
        self.alpha = 255

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return
        
        # 运动学物理模拟
        self.pos += self.velocity * dt
        self.velocity.y += 240 * dt # 重力回弹拉力
        self.rect.center = self.pos
        
        # 渐隐淡出效果
        self.alpha = int(max(0, min(255, (self.lifetime / self.max_lifetime) * 255)))
        self.image.set_alpha(self.alpha)


class Confetti(pygame.sprite.Sprite):
    """测试圆满成功时的七彩洒花粒子"""
    def __init__(self, pos, groups):
        super().__init__(groups)
        w = random.randint(8, 14)
        h = random.randint(5, 9)
        self.image = pygame.Surface((w, h))
        self.color = random.choice([
            (255, 215, 0), (255, 69, 0), (255, 20, 147), 
            (0, 255, 0), (0, 255, 255), (238, 130, 238)
        ])
        self.image.fill(self.color)
        
        self.pos = pygame.math.Vector2(pos)
        self.rect = self.image.get_rect(center=self.pos)
        
        # 抛射物理模拟
        angle = random.uniform(0, 3.14159 * 2)
        speed = random.uniform(200, 500)
        self.velocity = pygame.math.Vector2(pygame.math.Vector2(1, 0).rotate_rad(angle) * speed)
        self.gravity = 380
        self.wind = random.uniform(-40, 40)
        self.rot_speed = random.uniform(-200, 200)
        self.angle = 0
        self.lifetime = random.uniform(1.8, 2.8)
        self.orig_image = self.image.copy()

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return
            
        self.velocity.y += self.gravity * dt
        self.velocity.x += self.wind * dt
        self.pos += self.velocity * dt
        
        self.angle += self.rot_speed * dt
        self.image = pygame.transform.rotate(self.orig_image, self.angle)
        self.rect = self.image.get_rect(center=self.pos)


class Practice(Scene):
    def __init__(self, game_input: GameInput, surface: pygame.Surface):
        super().__init__(game_input, surface)
        # 加载模糊背景图
        bg_image = pygame.image.load(resource_path('assets/graphics/background/background_blurred.png'))
        self.bg = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # 实体管理组
        self.display_sprites = pygame.sprite.Group()
        self.effect_sprites = pygame.sprite.Group()
        
        # 初始化玩家控制器自适应绑定
        active_id = getattr(self.game_input, 'last_active_id', -1)
        if active_id not in self.game_input.controllers:
            active_id = -1
        original_info = self.game_input.controllers[active_id]
        
        # 1. 玩家数据结构 (使用选人界面中玩家所选定的真实角色)
        player_name = original_info.get('player_name', 'bai')
        if player_name == 'unselected':
            player_name = 'bai'
        player_info = {
            'player_index': 'p1',
            'player_name': player_name,
            'controller': original_info['controller'],
            'timer': original_info['timer'],
            'confirmed': True
        }
        # 2. 假人数据结构 (为避免镜像同色角色难以区分，给以智能化降级选择)
        dummy_char = 'bai' if player_name == 'dora' else 'dora'
        dummy_info = {
            'player_index': 'p2',
            'player_name': dummy_char,
            'controller': MockController(),
            'timer': Timer(200),
            'confirmed': True
        }
        
        # 实例化玩家与假人 (练习场无需对话框，我们定义一个带 showing=False 的虚空对象以防主循环崩溃)
        class DummyDialogue:
            showing = False
        self.dialogue = DummyDialogue()
        self.player = Player(player_info, self.display_sprites, None, self.screen)
        self.dummy = Player(dummy_info, self.display_sprites, None, self.screen)
        
        # 标明处于练习状态，以便 Player 内部解除边缘物理碰撞限制
        self.player.is_practice = True
        self.dummy.is_practice = True
        
        # 初始化摄像机 X 轴坐标 (聚焦于双人格斗中点)
        self.camera_x = 0.0
        
        # 调整假人位置与朝向，使其面朝左，处于黄金挨打位
        self.dummy.pos = pygame.math.Vector2(700, 700)
        self.dummy.to_right = False
        self.dummy.rect.midbottom = self.dummy.pos
        
        # 震屏属性
        self.shake_timer = 0
        self.shake_intensity = 0
        
        # 右侧毛玻璃清单面板数据 (分组：move / attack / super)
        self.checklist = [
            # ── 基础移动 ──
            {'id': 'right',      'group': 'move',   'zh': '向前移动（靠近对手）', 'en': 'Advance (Forward)',    'action': 'right',       'done': False, 'active_timer': 0.0, 'key_type': 'single'},
            {'id': 'left',       'group': 'move',   'zh': '向后移动（远离对手）', 'en': 'Retreat (Backward)',   'action': 'left',        'done': False, 'active_timer': 0.0, 'key_type': 'single'},
            {'id': 'run',        'group': 'move',   'zh': '向前奔跑（冲刺）',     'en': 'Dash Forward',         'action': 'run',         'done': False, 'active_timer': 0.0, 'key_type': 'run'},
            {'id': 'jump',       'group': 'move',   'zh': '垂直/方向跳跃',        'en': 'Jump',                 'action': 'jump',        'done': False, 'active_timer': 0.0, 'key_type': 'single'},
            # ── 战斗攻击 ──
            {'id': 'attack',     'group': 'attack', 'zh': '地面普通攻击（站立时轻拳）', 'en': 'Ground Attack',         'action': 'attack',      'done': False, 'active_timer': 0.0, 'key_type': 'single'},
            {'id': 'combo',      'group': 'attack', 'zh': '地面连击（轻拳连续按键）',   'en': 'Ground Combo',          'action': 'combo',       'done': False, 'active_timer': 0.0, 'key_type': 'combo_chain'},
            {'id': 'dash_attack','group': 'attack', 'zh': '冲刺击（向前奔跑中轻拳）',   'en': 'Dash Attack',           'action': 'dash attack', 'done': False, 'active_timer': 0.0, 'key_type': 'run_attack'},
            {'id': 'jump_attack','group': 'attack', 'zh': '空中击（起跳滞空时轻拳）',   'en': 'Air Attack',            'action': 'jump attack', 'done': False, 'active_timer': 0.0, 'key_type': 'air_attack'},
            # ── 必杀技能 ──
            {'id': 'super1',     'group': 'super',  'zh': '必杀一（耗 30 能量）',       'en': 'Super Move 1 (30)',     'action': 'super move 1','done': False, 'active_timer': 0.0, 'key_type': 'single'},
            {'id': 'super2',     'group': 'super',  'zh': '必杀二（耗 40 能量）',       'en': 'Super Move 2 (40)',     'action': 'super move 2','done': False, 'active_timer': 0.0, 'key_type': 'single'},
            {'id': 'finisher',   'group': 'super',  'zh': '终结奥义（耗 100 能量）',    'en': 'Finisher (100)',        'action': 'finisher',    'done': False, 'active_timer': 0.0, 'key_type': 'single'},
            {'id': 'air_super',  'group': 'super',  'zh': '起跳空中必杀（滞空时出招）', 'en': 'Air Super',             'action': 'air_super',   'done': False, 'active_timer': 0.0, 'key_type': 'air_any_super'},
            {'id': 'taunt',      'group': 'super',  'zh': '个性挑衅（炫耀展示）',       'en': 'Taunt / Show Off',      'action': 'taunt',       'done': False, 'active_timer': 0.0, 'key_type': 'single'},
        ]
        
        self.panel_visible = True
        self.panel_rect = pygame.Rect(940, 20, 320, 680)
        self.panel_surf = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA).convert_alpha()
        
        # 胜利与完成状态
        self.all_completed = False
        self.completion_banner_timer = 0.0
        self.confetti_timer = 0.0
        
        # 键盘/手柄按键符号缓存，提高绘制效率
        self.controller_type = 'keyboard' if active_id == -1 else 'gamepad'
        self.ctrl_ref = original_info['controller']
        self.active_id = active_id

        # 加载四个格斗家头像
        self.avatars = {}
        self.char_names_display = {
            'bai': {'zh': '白 (BAI)', 'en': 'BAI'},
            'dora': {'zh': '朵拉 (DORA)', 'en': 'DORA'},
            'raymon': {'zh': '雷蒙 (RAYMON)', 'en': 'RAYMON'},
            'shuo': {'zh': '硕 (SHUO)', 'en': 'SHUO'}
        }
        for name in ['bai', 'dora', 'raymon', 'shuo']:
            try:
                img = pygame.image.load(resource_path(f'assets/graphics/sprites/{name}/avatar.png')).convert_alpha()
                self.avatars[name] = pygame.transform.scale(img, (48, 48))
            except Exception as e:
                print(f"Error loading avatar for {name}: {e}")
                surf = pygame.Surface((48, 48))
                surf.fill((100, 100, 100))
                self.avatars[name] = surf

    def get_logical_mouse_pos(self):
        """将物理窗口鼠标坐标映射到逻辑1280x720画布坐标，完美适配窗口拉伸缩放"""
        window_w, window_h = pygame.display.get_surface().get_size()
        scale = min(window_w / SCREEN_WIDTH, window_h / SCREEN_HEIGHT)
        if scale == 0:
            return pygame.mouse.get_pos()
        new_w = SCREEN_WIDTH * scale
        new_h = SCREEN_HEIGHT * scale
        offset_x = (window_w - new_w) / 2
        offset_y = (window_h - new_h) / 2
        
        mx, my = pygame.mouse.get_pos()
        logical_x = (mx - offset_x) / scale
        logical_y = (my - offset_y) / scale
        return int(logical_x), int(logical_y)

    def handle_event(self, event):
        """拦截并处理鼠标点击与按键事件，支持换人与显示/隐藏出招表"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            lx, ly = self.get_logical_mouse_pos()
            
            # A. 顶部 HUD 角色选择栏区域坐标
            box_y = 20
            for i, name in enumerate(['bai', 'dora', 'raymon', 'shuo']):
                cx = 320 + i * 85
                cy = box_y + 40
                # 判定点击矩形热区
                avatar_rect = pygame.Rect(cx - 24, cy - 24, 48, 48)
                if avatar_rect.collidepoint(lx, ly):
                    current_char = self.player.device_info['player_name']
                    if name != current_char:
                        self.switch_to_character(name)
                    return
            
            # B. 隐藏/显示出招表的鼠标点击交互
            if self.panel_visible:
                # 点击隐藏按钮：x in [1180, 1240], y in [40, 62] (逻辑坐标系)
                hide_rect = pygame.Rect(1180, 40, 60, 22)
                if hide_rect.collidepoint(lx, ly):
                    self.panel_visible = False
                    return
            else:
                # 隐藏时，点击悬浮玻璃条：x in [940, 1260], y in [20, 68]
                show_rect = pygame.Rect(940, 20, 320, 48)
                if show_rect.collidepoint(lx, ly):
                    self.panel_visible = True
                    return

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.panel_visible = not self.panel_visible

        elif event.type == pygame.JOYBUTTONDOWN:
            # 兼容各类型手柄的 Select/Share/Options 键来一键开关出招表
            if event.button in [4, 6, 8]:
                self.panel_visible = not self.panel_visible

    def switch_to_character(self, next_char):
        """瞬发切换当前正在测试的格斗角色，并自适应调整假人以防镜像冲突"""
        # 1. 记录玩家当前位置、血量、朝向、控制器配置等信息
        old_pos = pygame.math.Vector2(self.player.pos)
        old_to_right = self.player.to_right
        old_info = self.player.device_info
        
        # 2. 销毁旧玩家
        self.player.kill()
        
        # 3. 实例化新角色
        new_info = old_info.copy()
        new_info['player_name'] = next_char
        
        self.player = Player(new_info, self.display_sprites, None, self.screen)
        self.player.is_practice = True
        self.player.pos = old_pos
        self.player.to_right = old_to_right
        self.player.rect.midbottom = old_pos
        
        # 4. 智能化避免假人与玩家镜像重合
        dummy_char = 'bai' if next_char == 'dora' else 'dora'
        if self.dummy.device_info['player_name'] != dummy_char:
            dummy_pos = pygame.math.Vector2(self.dummy.pos)
            dummy_to_right = self.dummy.to_right
            dummy_info = self.dummy.device_info.copy()
            dummy_info['player_name'] = dummy_char
            
            self.dummy.kill()
            self.dummy = Player(dummy_info, self.display_sprites, None, self.screen)
            self.dummy.is_practice = True
            self.dummy.pos = dummy_pos
            self.dummy.to_right = dummy_to_right
            self.dummy.rect.midbottom = dummy_pos
            
        # 5. 在原位置炸开华丽的命中闪光粒子作为转场特效！
        from src.ui.ui import HitSpark
        HitSpark(old_pos, self.effect_sprites)

    def switch_character(self, forward=True):
        """循环切换当前角色"""
        current_char = self.player.device_info['player_name']
        chars = ['bai', 'dora', 'raymon', 'shuo']
        if current_char not in chars:
            current_char = 'bai'
            
        idx = chars.index(current_char)
        if forward:
            idx = (idx + 1) % len(chars)
        else:
            idx = (idx - 1) % len(chars)
        self.switch_to_character(chars[idx])

    def spawn_damage_text(self, damage, pos):
        """在打击点生成高亮漂浮伤害飘字"""
        DamageText(damage, pos, [self.display_sprites, self.effect_sprites])

    def apply_shake(self, duration, intensity):
        self.shake_timer = duration
        self.shake_intensity = intensity

    def check_collisions(self):
        """高度精简高保真物理碰撞检测与反馈"""
        players = [self.player, self.dummy]
        for attacker in players:
            hitbox = attacker.get_hitbox()
            if hitbox:
                # 检查特殊招式冲击波粒子发生
                if attacker.status in ['super move 1', 'super move 2', 'finisher'] and not attacker.special_wave_spawned:
                    attacker.special_wave_spawned = True
                    from src.ui.ui import ShockWave
                    ShockWave(hitbox, self.effect_sprites, attacker.device_info['player_name'], attacker.status)
                    
                for target in players:
                    if target != attacker and not target.is_hit and target.health > 0:
                        if not hasattr(attacker, 'has_hit_targets') or not isinstance(attacker.has_hit_targets, dict) or target not in attacker.has_hit_targets:
                            hurtbox = target.get_hurtbox()
                            if hitbox.colliderect(hurtbox):
                                if not hasattr(attacker, 'has_hit_targets') or not isinstance(attacker.has_hit_targets, dict):
                                    attacker.has_hit_targets = {}
                                attacker.has_hit_targets[target] = 0.35
                                
                                damage_data = attacker.attack_data.get(attacker.status, {'damage': 40, 'knockback': 15})
                                damage = damage_data['damage']
                                target.take_hit(damage, damage_data['knockback'], attacker)
                                
                                # 双方顿帧阻滞 (Hit Stop)
                                if damage < 60:
                                    attacker.hit_stop_timer = 0.08
                                elif damage < 100:
                                    attacker.hit_stop_timer = 0.12
                                else:
                                    attacker.hit_stop_timer = 0.18
                                    
                                # 触发震屏
                                self.apply_shake(0.15, 7 if damage >= 100 else 3)
                                
                                # 生成命中打击火花
                                from src.ui.ui import HitSpark
                                spark_pos = hitbox.clip(hurtbox).center
                                HitSpark(spark_pos, self.effect_sprites)
                                
                                # 生成伤害飘字粒子
                                self.spawn_damage_text(damage, spark_pos)

    def draw_top_hud(self):
        """在测试场景顶部绘制超高颜值的角色切换控制中心 (Top Character Selector HUD)"""
        # 1. 绘制 Midnight Violet Glass (半透明午夜紫) 玻璃底板
        hud_rect = pygame.Rect(40, 20, 760, 80)
        hud_surf = pygame.Surface(hud_rect.size, pygame.SRCALPHA).convert_alpha()
        
        # 绘制半透明背景
        pygame.draw.rect(hud_surf, (18, 12, 28, 220), (0, 0, hud_rect.w, hud_rect.h), border_radius=12)
        # 绘制亮紫发光霓虹边框
        pygame.draw.rect(hud_surf, (155, 38, 182), (0, 0, hud_rect.w, hud_rect.h), width=2, border_radius=12)
        
        # 2. 绘制标题 "角色特训"
        lang = config.get('system', 'language')
        title_font = pygame.font.Font(resource_path('assets/font/simhei.ttf'), 20)
        sub_font = pygame.font.Font(resource_path('assets/font/impact.ttf'), 12)
        
        title_text = "特训角色切换" if lang == 'zh_CN' else "CHARACTER SELECTOR"
        title_surf = title_font.render(title_text, True, (255, 215, 0)) # 黄金色
        hud_surf.blit(title_surf, (20, 16))
        
        current_char = self.player.device_info['player_name']
        display_info = self.char_names_display.get(current_char, {'zh': current_char, 'en': current_char})
        active_char_name = display_info['zh'] if lang == 'zh_CN' else display_info['en']
        
        sub_text = f"TRAINING: {active_char_name.upper()}"
        sub_surf = sub_font.render(sub_text, True, (0, 255, 255)) # 霓虹青
        hud_surf.blit(sub_surf, (20, 48))
        
        # 3. 绘制角色头像列表
        lx, ly = self.get_logical_mouse_pos()
        box_y = 20
        chars = ['bai', 'dora', 'raymon', 'shuo']
        
        for i, name in enumerate(chars):
            cx = 320 + i * 85
            cy = box_y + 40
            
            # 计算绝对坐标 and 相对box坐标
            rx = cx - hud_rect.x
            ry = cy - hud_rect.y
            
            is_active = (name == current_char)
            # 检查鼠标悬停 (使用逻辑坐标)
            is_hovered = pygame.Rect(cx - 24, cy - 24, 48, 48).collidepoint(lx, ly)
            
            # 如果是当前选中的，绘制华丽的发光外边框
            if is_active:
                # 绘制彩色发光环
                pygame.draw.circle(hud_surf, (0, 255, 255), (rx, ry), 27, width=3)
                pygame.draw.circle(hud_surf, (0, 150, 200, 100), (rx, ry), 30, width=1) # 外层微弱发光
                # 绘制一个向下的亮黄小三角指示器
                pygame.draw.polygon(hud_surf, (255, 215, 0), [(rx, ry - 35), (rx - 6, ry - 43), (rx + 6, ry - 43)])
            elif is_hovered:
                # 悬停时绘制微亮白边框
                pygame.draw.circle(hud_surf, (255, 255, 255), (rx, ry), 26, width=2)
            else:
                # 普通未选中，暗紫边框
                pygame.draw.circle(hud_surf, (80, 50, 100), (rx, ry), 25, width=1)
                
            # 绘制头像图片 (带不同透明度)
            avatar_img = self.avatars[name]
            if is_active:
                avatar_surf = avatar_img.copy()
            else:
                # 半透明处理
                avatar_surf = avatar_img.copy()
                alpha_val = 220 if is_hovered else 130
                avatar_surf.set_alpha(alpha_val)
                
            # 绘制头像 (居中)
            avatar_rect = avatar_surf.get_rect(center=(rx, ry))
            hud_surf.blit(avatar_surf, avatar_rect)
            
    def draw_right_panel(self):
        """绘制高保真毛玻璃指令面板 - 分组布局 + 触发高亮"""
        lang = config.get('system', 'language')

        # A. 隐藏时显示悬浮玻璃条 Toggle Button
        if not self.panel_visible:
            btn_rect = pygame.Rect(940, 20, 320, 40)
            btn_surf = pygame.Surface(btn_rect.size, pygame.SRCALPHA).convert_alpha()
            
            lx, ly = self.get_logical_mouse_pos()
            is_hovered = btn_rect.collidepoint(lx, ly)
            
            bg_alpha = 240 if is_hovered else 190
            border_color = (0, 255, 255) if is_hovered else (155, 38, 182)
            text_color = (255, 255, 255) if is_hovered else (0, 255, 255)
            
            # 绘制 Midnight Violet Glass (半透明午夜紫) 玻璃底盒
            pygame.draw.rect(btn_surf, (18, 12, 28, bg_alpha), (0, 0, btn_rect.w, btn_rect.h), border_radius=8)
            pygame.draw.rect(btn_surf, border_color, (0, 0, btn_rect.w, btn_rect.h), width=2, border_radius=8)
            
            # 绘制提示文字与按键提示
            btn_font = pygame.font.Font(resource_path('assets/font/simhei.ttf'), 14)
            btn_text = "[Tab] 显示操作出招表" if lang == 'zh_CN' else "[Tab] Show Command Checklist"
            text_surf = btn_font.render(btn_text, True, text_color)
            btn_surf.blit(text_surf, text_surf.get_rect(center=(btn_rect.w // 2, btn_rect.h // 2)))
            
            self.screen.blit(btn_surf, btn_rect)
            return

        # B. 显示完整指令面板
        self.panel_surf.fill((0, 0, 0, 0))
        pw, ph = self.panel_rect.w, self.panel_rect.h

        # 面板背景 + 双边框
        pygame.draw.rect(self.panel_surf, (14, 10, 22, 235), (0, 0, pw, ph), border_radius=14)
        pygame.draw.rect(self.panel_surf, (110, 38, 150), (0, 0, pw, ph), width=2, border_radius=14)

        # 字体
        title_font = pygame.font.Font(resource_path('assets/font/simhei.ttf'), 17)
        group_font = pygame.font.Font(resource_path('assets/font/impact.ttf'), 10)
        item_font  = pygame.font.Font(resource_path('assets/font/simhei.ttf'), 13)
        key_font   = pygame.font.Font(resource_path('assets/font/impact.ttf'), 11)

        # 标题
        title_text = "操作指令" if lang == 'zh_CN' else "MOVE LIST"
        title_surf = title_font.render(title_text, True, (255, 215, 0))
        self.panel_surf.blit(title_surf, (16, 12))

        # 隐藏按钮
        lx, ly = self.get_logical_mouse_pos()
        hide_btn_abs = pygame.Rect(1180, 40, 60, 22)
        hide_hover   = hide_btn_abs.collidepoint(lx, ly)
        rel_hide     = pygame.Rect(pw - 76, 12, 60, 22)
        pygame.draw.rect(self.panel_surf, (50, 20, 80) if hide_hover else (18, 12, 28), rel_hide, border_radius=4)
        pygame.draw.rect(self.panel_surf, (0, 255, 255) if hide_hover else (90, 55, 120), rel_hide, width=1, border_radius=4)
        hide_text = "隐藏[Tab]" if lang == 'zh_CN' else "Hide[Tab]"
        hide_surf = key_font.render(hide_text, True, (0, 255, 255) if hide_hover else (150, 130, 170))
        self.panel_surf.blit(hide_surf, hide_surf.get_rect(center=rel_hide.center))

        # 标题分割线
        pygame.draw.line(self.panel_surf, (80, 50, 110), (12, 40), (pw - 12, 40), 1)

        # 分组颜色与标签配置
        GROUP_COLORS = {
            'move':   (0,   200, 255),
            'attack': (255, 150,   0),
            'super':  (200,  50, 255),
        }
        GROUP_LABELS = {
            'move':   ('基础移动', 'MOVEMENT'),
            'attack': ('战斗攻击', 'ATTACKS'),
            'super':  ('必杀技能', 'SPECIALS'),
        }

        def get_action_symbol(act):
            if self.controller_type == 'keyboard':
                raw_k = self.ctrl_ref.action_map.get(act, pygame.K_UNKNOWN)
                sym = pygame.key.name(raw_k).upper() if raw_k != pygame.K_UNKNOWN else '---'
                return get_short_key_name(sym)
            else:
                raw_b = self.ctrl_ref.action_map.get(act)
                return self.ctrl_ref.get_button_name(raw_b)

        now_ms     = pygame.time.get_ticks()
        y          = 46
        item_h     = 29
        gap        = 3
        last_group = None

        for item in self.checklist:
            grp = item.get('group', 'move')
            gc  = GROUP_COLORS.get(grp, (180, 180, 180))

            # ── 分组标题行 ──
            if grp != last_group:
                if last_group is not None:
                    y += 5
                last_group = grp
                glbl  = GROUP_LABELS.get(grp, ('', ''))[0 if lang == 'zh_CN' else 1]
                mid_y = y + 8
                # 左侧细线
                pygame.draw.line(self.panel_surf, (gc[0]//3, gc[1]//3, gc[2]//3), (12, mid_y), (50, mid_y), 1)
                # 标签
                g_surf = group_font.render(glbl, True, gc)
                self.panel_surf.blit(g_surf, (54, y))
                # 右侧细线
                rx_line = 58 + g_surf.get_width()
                pygame.draw.line(self.panel_surf, (gc[0]//3, gc[1]//3, gc[2]//3), (rx_line, mid_y), (pw - 12, mid_y), 1)
                y += 18

            # ── 行状态 ──
            is_active = item['active_timer'] > 0

            if is_active:
                pulse    = 0.75 + 0.25 * abs(((now_ms // 90) % 10) / 5.0 - 1.0)
                row_bg   = (int(gc[0]*0.18), int(gc[1]*0.18), int(gc[2]*0.18), 210)
                bdr_col  = (int(gc[0]*pulse), int(gc[1]*pulse), int(gc[2]*pulse))
                text_col = (255, 255, 255)
                dot_col  = gc
                key_col  = (255, 255, 255)
            else:
                row_bg   = (20, 16, 32, 110)
                bdr_col  = (65, 42, 85)
                text_col = (185, 175, 205)
                dot_col  = (85, 58, 108)
                key_col  = (0, 200, 230)

            # 行背景
            row_rect = pygame.Rect(10, y, pw - 20, item_h)
            pygame.draw.rect(self.panel_surf, row_bg,  row_rect, border_radius=6)
            pygame.draw.rect(self.panel_surf, bdr_col, row_rect, width=1, border_radius=6)

            # 触发时：额外外层光晕
            if is_active:
                glow_surf = pygame.Surface((row_rect.w + 8, row_rect.h + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (gc[0], gc[1], gc[2], 55),
                                 (0, 0, glow_surf.get_width(), glow_surf.get_height()), border_radius=9)
                self.panel_surf.blit(glow_surf, (row_rect.x - 4, row_rect.y - 4))

            # 状态指示圆点
            dot_cx = row_rect.x + 13
            dot_cy = row_rect.centery
            if is_active:
                pygame.draw.circle(self.panel_surf, dot_col, (dot_cx, dot_cy), 5)
            else:
                pygame.draw.circle(self.panel_surf, dot_col, (dot_cx, dot_cy), 4, width=2)

            # 招式名称
            name_text = item['zh'] if lang == 'zh_CN' else item['en']
            name_surf = item_font.render(name_text, True, text_col)
            self.panel_surf.blit(name_surf, (dot_cx + 12, dot_cy - name_surf.get_height() // 2))

            # 按键提示标签
            key_type    = item.get('key_type', 'single')
            action_name = item['action']
            if key_type == 'single':
                k = get_action_symbol(action_name)
                if action_name == 'right':
                    key_symbol = f"{k} (→)"
                elif action_name == 'left':
                    key_symbol = f"{k} (←)"
                elif action_name == 'jump':
                    # W 作为系统默认上键跳跃，K 则是单独绑定的跳跃键
                    up_k = get_action_symbol('up') if 'up' in self.ctrl_ref.action_map else 'W'
                    if k == '---' or k == up_k:
                        key_symbol = f"{up_k} (↑)"
                    else:
                        key_symbol = f"{up_k} / {k} (↑)"
                else:
                    key_symbol = k
            elif key_type == 'combo_chain':
                atk = get_action_symbol('attack')
                key_symbol = f"{atk}, {atk}"
            elif key_type == 'air_attack':
                atk = get_action_symbol('attack')
                key_symbol = (f"空中按 {atk}" if lang == 'zh_CN' else f"AIR {atk}")
            elif key_type == 'run_attack':
                atk = get_action_symbol('attack')
                key_symbol = (f"跑动中按 {atk}" if lang == 'zh_CN' else f"RUN {atk}")
            elif key_type == 'run':
                key_symbol = ("双击前 (→/←)" if lang == 'zh_CN' else "2x Forward")
            elif key_type == 'air_any_super':
                s1 = get_action_symbol('super move 1')
                s2 = get_action_symbol('super move 2')
                fin = get_action_symbol('finisher')
                key_symbol = (f"空中按 {s1}/{s2}/{fin}" if lang == 'zh_CN' else f"AIR {s1}/{s2}/{fin}")
            else:
                key_symbol = '---'

            key_text_surf = key_font.render(key_symbol, True, key_col)
            key_box_w     = max(68, key_text_surf.get_width() + 14)
            key_box       = pygame.Rect(pw - 12 - key_box_w, dot_cy - 9, key_box_w, 19)
            if is_active:
                kb_bg = (int(gc[0]*0.22), int(gc[1]*0.22), int(gc[2]*0.22), 200)
            else:
                kb_bg = (12, 10, 22, 160)
            pygame.draw.rect(self.panel_surf, kb_bg,   key_box, border_radius=4)
            pygame.draw.rect(self.panel_surf, bdr_col, key_box, width=1, border_radius=4)
            self.panel_surf.blit(key_text_surf, key_text_surf.get_rect(center=key_box.center))

            y += item_h + gap

        # 底部提示栏
        y += 6
        pygame.draw.line(self.panel_surf, (70, 45, 95), (12, y), (pw - 12, y), 1)
        y += 8
        tip_font = pygame.font.Font(resource_path('assets/font/simhei.ttf'), 11)
        tips = [
            ("Q / E (LB / RB)  切换角色" if lang == 'zh_CN' else "Q / E (LB / RB)  Switch Char"),
            ("ESC  退出返回主菜单"         if lang == 'zh_CN' else "ESC  Return to Menu"),
        ]
        for tip in tips:
            ts = tip_font.render(tip, True, (110, 100, 140))
            self.panel_surf.blit(ts, ts.get_rect(center=(pw // 2, y + 7)))
            y += 18

        self.screen.blit(self.panel_surf, self.panel_rect)

    def draw_celebration_banner(self, dt):
        """渲染大功告成的金色金属奖杯横幅与撒花粒子动画"""
        self.completion_banner_timer += dt
        
        # 1. Spawning confetti particle burst (撒花粒子持续爆破)
        self.confetti_timer -= dt
        if self.confetti_timer <= 0:
            self.confetti_timer = 0.05
            # 从中心和大范围随机抛射粒子
            for _ in range(3):
                Confetti((SCREEN_WIDTH // 2, 300), [self.display_sprites, self.effect_sprites])
                
        # 2. 绘制毛玻璃 Midnight Black 遮罩层 (淡入半透明)
        mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA).convert_alpha()
        alpha = int(min(180, self.completion_banner_timer * 150))
        mask.fill((5, 3, 10, alpha))
        self.screen.blit(mask, (0, 0))
        
        # 3. 绘制金色 Trophy & Victory Banner (金属奖杯横幅)
        banner_font = pygame.font.Font(resource_path('assets/font/impact.ttf'), 56)
        lang = config.get('system', 'language')
        
        banner_text = "TEST COMPLETED!"
        sub_text = "You are ready for the real battle!" if lang == 'en_US' else "格斗操作测试大获全胜，去对战吧！"
        
        # 大标题带极亮金色发光和多层硬阴影
        title_surf = banner_font.render(banner_text, True, (255, 215, 0))
        shadow_surf = banner_font.render(banner_text, True, (10, 10, 15))
        
        sub_font = pygame.font.Font(resource_path('assets/font/simhei.ttf'), 22)
        sub_surf = sub_font.render(sub_text, True, (0, 255, 255)) # 亮青色提示
        
        anykey_font = pygame.font.Font(resource_path('assets/font/simhei.ttf'), 16)
        anykey_text = "—— 按任意键返回主菜单 ——" if lang == 'zh_CN' else "—— PRESS ANY KEY TO CONTINUE ——"
        anykey_surf = anykey_font.render(anykey_text, True, (240, 240, 240))
        
        # 弹入缩放动画效果
        scale_ratio = min(1.0, self.completion_banner_timer * 2.0)
        if scale_ratio < 1.0:
            sw, sh = title_surf.get_size()
            title_surf = pygame.transform.scale(title_surf, (int(sw * scale_ratio), int(sh * scale_ratio)))
            shadow_surf = pygame.transform.scale(shadow_surf, (int(sw * scale_ratio), int(sh * scale_ratio)))
            
        cx, cy = SCREEN_WIDTH // 2, 280
        
        # 绘制大阴影和金标题
        self.screen.blit(shadow_surf, shadow_surf.get_rect(center=(cx + 3, cy + 3)))
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, cy)))
        
        # 绘制辅助小行
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(cx, cy + 60)))
        
        # 让“按任意键”文字产生呼吸发光特效
        pulse_alpha = int(140 + 115 * abs(pygame.math.sin(self.completion_banner_timer * 4.0)))
        anykey_surf.set_alpha(pulse_alpha)
        self.screen.blit(anykey_surf, anykey_surf.get_rect(center=(cx, cy + 120)))

    def run(self, dt) -> SceneStatus:
        # 1. 物理逻辑与更新
        if dt > 0:
            # 持续将玩家能量锁定为 100，达成无限发波和大招状态
            self.player.energy = 100.0
            # 假人血量重置，防止打死
            self.dummy.health = 9999
            
            # 检测玩家当前状态，更新 checklist（触发高亮 + 打勾完成）
            p_status    = self.player.status
            is_airborne = self.player.pos.y < self.player.ground_y

            for item in self.checklist:
                act       = item['id']
                triggered = False

                if act == 'left':
                    triggered = (p_status == 'walk' and self.player.direction.x < 0)
                elif act == 'right':
                    triggered = (p_status == 'walk' and self.player.direction.x > 0)
                elif act == 'run':
                    triggered = (p_status == 'run')
                elif act == 'jump':
                    triggered = (p_status == 'jump')
                elif act == 'attack':
                    triggered = (p_status == 'attack')
                elif act == 'combo':
                    triggered = (p_status == 'combo')
                elif act == 'dash_attack':
                    triggered = (p_status == 'dash attack')
                elif act == 'jump_attack':
                    triggered = (p_status == 'jump attack')
                elif act == 'super1':
                    triggered = (p_status == 'super move 1')
                elif act == 'super2':
                    triggered = (p_status == 'super move 2')
                elif act == 'finisher':
                    triggered = (p_status == 'finisher')
                elif act == 'air_super':
                    # 空中触发任意大招均算
                    triggered = (p_status in ['super move 1', 'super move 2', 'finisher'] and is_airborne)
                elif act == 'taunt':
                    triggered = (p_status == 'show off')

                if triggered:
                    item['active_timer'] = 1.0  # 处于触发状态，即时高亮
                else:
                    item['active_timer'] = 0.0  # 未处于触发状态，即时恢复原样

            # 仅在未完成或结算的淡入期间处理碰撞和角色更新
            self.check_collisions()
            
            # 双重人物推挤框计算 (防穿模)
            self.player.resolve_player_collision(self.dummy)
            
            # 记录更新前的位置以判断谁在往远处走
            prev_p1_x = self.player.pos.x
            prev_p2_x = self.dummy.pos.x

            # 组实体更新
            self.display_sprites.update(dt)
            self.effect_sprites.update(dt)

            # 强保真双人视距边缘强锁 (因另一个人卡视野无法前进，绝不拖动另一个人)
            max_dist = 720.0 if self.panel_visible else 960.0
            new_p1_x = self.player.pos.x
            new_p2_x = self.dummy.pos.x
            
            if abs(new_p1_x - new_p2_x) > max_dist:
                # 判定是谁的移动增加了两者间距
                p1_moved = abs(new_p1_x - prev_p2_x) > abs(prev_p1_x - prev_p2_x)
                p2_moved = abs(new_p2_x - prev_p1_x) > abs(prev_p2_x - prev_p1_x)
                
                if p1_moved and not p2_moved:
                    # P1 试图走远，拉回 P1 并锁定在以 P2 为中心的 max_dist 边界
                    if new_p1_x < new_p2_x:
                        self.player.pos.x = new_p2_x - max_dist
                    else:
                        self.player.pos.x = new_p2_x + max_dist
                elif p2_moved and not p1_moved:
                    # P2 (假人被击退等) 试图走远，拉回 P2 并锁定在以 P1 为中心的 max_dist 边界
                    if new_p2_x < new_p1_x:
                        self.dummy.pos.x = new_p1_x - max_dist
                    else:
                        self.dummy.pos.x = new_p1_x + max_dist
                else:
                    # 双向或无差异超限时，采用平分拉回兜底
                    midpoint_x = (new_p1_x + new_p2_x) / 2.0
                    direction = 1 if new_p1_x > new_p2_x else -1
                    self.player.pos.x = midpoint_x + direction * (max_dist / 2.0)
                    self.dummy.pos.x = midpoint_x - direction * (max_dist / 2.0)
                
                # 重新计算并同步物理包围盒
                self.player.rect.midbottom = self.player.pos
                self.dummy.rect.midbottom = self.dummy.pos

            # 摄像机聚焦：计算双人格斗中点，让其中央对齐至实战区的正中心 (当面板可见时居中于 470px，隐藏时居中于 640px)
            midpoint_x = (self.player.pos.x + self.dummy.pos.x) / 2.0
            center_x = 470.0 if self.panel_visible else 640.0
            target_camera_x = midpoint_x - center_x
            
            # 平滑插值 (Lerp) 追随，平滑平动
            self.camera_x += (target_camera_x - self.camera_x) * 5.0 * dt

        # 2. 物理屏幕震动偏置计算
        shake_offset = pygame.math.Vector2(0, 0)
        if self.shake_timer > 0:
            self.shake_timer -= dt
            shake_offset.x = random.uniform(-self.shake_intensity, self.shake_intensity)
            shake_offset.y = random.uniform(-self.shake_intensity, self.shake_intensity)

        # 3. 屏幕绘图流程
        # A. 渲染平铺的无线背景 (根据面板可见度动态扩展平铺区域)
        play_area_w = 940 if self.panel_visible else 1280
        bg_w = self.bg.get_width()
        start_x = -int(self.camera_x) % bg_w
        if start_x > 0:
            start_x -= bg_w
            
        current_x = start_x
        while current_x < play_area_w:
            self.screen.blit(self.bg, (current_x + shake_offset.x, shake_offset.y))
            current_x += bg_w
        
        # 绘制两侧的分栏边界阴影以产生深度纵深感 (面板显示时，分栏线移至 940px 处)
        if self.panel_visible:
            border_rect = pygame.Rect(940, 0, 8, SCREEN_HEIGHT)
            pygame.draw.rect(self.screen, (10, 8, 15), border_rect)
        
        # B. 绘制所有战斗与特效实体，应用摄像机偏移 (camera_x) 与震屏偏置
        # Ghost Trails removed
        pass

        # 融合 display_sprites 与 effect_sprites 并按 Y 坐标进行完美纵深排序绘制
        all_sprites = self.display_sprites.sprites() + self.effect_sprites.sprites()
        sorted_sprites = sorted(all_sprites, key=lambda s: getattr(s, 'rect', s).y)
        for sprite in sorted_sprites:
            offset_pos = (sprite.rect.x - self.camera_x + shake_offset.x, sprite.rect.y + shake_offset.y)
            self.screen.blit(sprite.image, offset_pos)

        # C. 绘制右侧毛玻璃清单面板
        self.draw_right_panel()
        
        # D. 绘制顶部 HUD (角色切换控制栏)
        self.draw_top_hud()

        # D. 如果测试达成，覆盖绘制胜利纸屑与奖杯横幅
        if self.all_completed:
            self.draw_celebration_banner(dt)

        # 4. 键盘/手柄输入拦截 (返回处理)
        if dt > 0:
            active_id = getattr(self.game_input, 'last_active_id', -1)
            if active_id in self.game_input.controllers:
                original_info = self.game_input.controllers[active_id]
                ctrl = original_info['controller']
                
                # 在全部点亮后的庆祝画面中，按任意键直接退回
                if self.all_completed and self.completion_banner_timer >= 1.0:
                    for action in ctrl.actions.values():
                        if action.just_pressed:
                            self.game_input.practice_mode = False
                            return SceneStatus.HOME
                    # 检查回车键和其它手柄确认键等
                    if ctrl.ui_performed('confirm') or ctrl.ui_performed('cancel'):
                        self.game_input.practice_mode = False
                        return SceneStatus.HOME
                
                # 随时可以按 Q / E 键 (手柄 LB / RB) 来瞬间切换角色！
                if ctrl.ui_performed('tab_right'):
                    self.switch_character(forward=True)
                elif ctrl.ui_performed('tab_left'):
                    self.switch_character(forward=False)
                
                # 随时可以按 ESC 退回主菜单
                if ctrl.ui_performed('cancel'):
                    self.game_input.practice_mode = False
                    return SceneStatus.HOME

        return SceneStatus.HOW_TO_PLAY
