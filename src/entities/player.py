import pygame
from src.core.support import import_gifs_dict, import_pic
from src.ui.ui import PlayerInfoCard


class Player(pygame.sprite.Sprite):
    def __init__(self, info, groups, dialogue, surface: pygame.Surface):
        super().__init__(groups)
        self.device_info = info
        self.dialogue = dialogue
        # 画面相关
        self.status = 'idle'
        self.images = import_gifs_dict(f'assets/graphics/sprites/{info["player_name"]}')
        self.image_index = 0
        self.image = self.images['idle'][0]
        self.display_surf = surface
        from src.settings import SCREEN_WIDTH
        if info['player_index'] == 'p1':
            self.pos = pygame.math.Vector2(280, 700)
            self.to_right = True
        else:
            self.pos = pygame.math.Vector2(SCREEN_WIDTH - 280, 700)
            self.to_right = False
        
        self.rect = self.image.get_rect(midbottom=self.pos)
        self.speed = 150
        self.direction = pygame.math.Vector2()

        # 战斗与物理属性
        self.max_health = 1000
        self.health = 1000
        self.is_hit = False
        self.hit_timer = 0
        self.hit_stop_timer = 0 # 击中冻结时间 (Hit Stop)
        self.invincible_timer = 0.0 # 无敌时间帧 (i-frames)
        self.knockback_velocity = pygame.math.Vector2(0, 0) # 物理滑动击退速度
        
        # 招式数据 (伤害, 活跃帧范围, 击退)
        self.attack_data = {
            'attack': {'damage': 50, 'active': (2, 5), 'knockback': 10},
            'combo': {'damage': 30, 'active': (1, 10), 'knockback': 5},
            'dash attack': {'damage': 60, 'active': (2, 6), 'knockback': 20},
            'jump attack': {'damage': 40, 'active': (1, 4), 'knockback': 15},
            'super move 1': {'damage': 150, 'active': (5, 15), 'knockback': 40},
            'super move 2': {'damage': 200, 'active': (10, 25), 'knockback': 50},
            'super move 3': {'damage': 180, 'active': (5, 20), 'knockback': 45},
            'finisher': {'damage': 300, 'active': (15, 40), 'knockback': 100},
        }

        # 临时血条展示 (使用 player_index p1/p2 以对称渲染)
        avatar = import_pic(f'assets/graphics/sprites/{info["player_name"]}/avatar.png')
        self.blood_ui = PlayerInfoCard(info['player_index'], avatar, self.display_surf)

        # 跳跃控制
        self.gravity = 800
        self.ground_y = 700
        self.jump_velocity = 0
        self.jump_strength = 500

        # 移动锁控制 (冲刺攻击后需释放按键重新按下才能移动)
        self.movement_locked = False

        # 连击计数
        self.combo_count = 0
        self.max_combo = 0
        self.combo_timer = 0.0

        # AAA级视觉表现属性
        self.shadow_health = 1000.0
        self.ghosts = []
        self.ghost_timer = 0

    def update_image(self, dt):
        # frames是一个系列动画图片的列表
        frames = self.images[self.status]
        # 增加动画播放速度
        self.image_index += dt * 10
        
        # 动画结束后动作
        if self.image_index >= len(frames):
            self.image_index = 0
            # 维持最后一帧的状态：跳跃、被击倒、或受击硬直定格 (避免受击振动抖动循环)
            if self.status in ['jump', 'jump attack', 'knock down', 'body hit', 'head hit']:
                self.image_index = len(frames) - 1
            
            # 自动回到 idle 的动画
            if self.status in ['attack', 'super move 1', 'super move 2', 'finisher',
                               'combo', 'dash attack', 'victory', 'show off']:
                # victory 和 show off 动画通常循环播放或停在最后一帧，这里我们让其循环或停住
                if self.status in ['victory', 'show off']:
                    self.image_index = len(frames) - 1
                else:
                    self.status = 'idle'
            
            # 受击动画结束判断
            if self.status in ['body hit', 'head hit'] and not self.is_hit:
                self.status = 'idle'

        # 安全索引，防止越界
        idx = int(max(0, min(len(frames) - 1, self.image_index)))
        original = frames[idx]
        
        # 缩放图片
        w, h = original.get_size()
        scaled = pygame.transform.scale(original, (int(w * 0.5), int(h * 0.5)))
        
        # 高性能闪白：使用 BLEND_RGBA_MAX 完美提取剪影
        if self.is_hit and (pygame.time.get_ticks() // 60) % 2 == 0:
            white_mask = scaled.copy()
            white_mask.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            scaled = white_mask
            
        # 无敌帧透明度闪烁效果 (Arcade Blinking I-Frames)
        if self.invincible_timer > 0 and (pygame.time.get_ticks() // 80) % 2 == 0:
            scaled.set_alpha(120)

        # 左右转向
        self.image = pygame.transform.flip(scaled, self.to_right, False)

        # 在高速/大招动作下周期性产生分身残影 (Ghost Trails Generation)
        if self.status in ['run', 'dash attack', 'super move 1', 'super move 2', 'super move 3', 'finisher']:
            self.ghost_timer += 1
            if self.ghost_timer % 3 == 0:
                self.ghosts.append({
                    'image': self.image.copy(),
                    'pos': self.rect.topleft,
                    'alpha': 160.0
                })

    def get_hurtbox(self):
        # 更加精细的受击盒：根据图片实际缩放后的尺寸计算
        # 宽度收缩更多（胸腹部受击），高度稍微降低（头部以下）
        hurtbox = self.rect.copy()
        hurtbox.width = int(self.rect.width * 0.4)
        hurtbox.height = int(self.rect.height * 0.8)
        hurtbox.center = self.rect.center
        return hurtbox

    def get_hitbox(self):
        # 只有在攻击动作的活跃帧内才产生判定盒
        if self.status in self.attack_data and self.status in self.images:
            frames = self.images[self.status]
            total_frames = len(frames)
            
            # 动态计算活跃帧区间，防止 GIF 帧数极少导致硬编码活跃帧失效
            if self.status in ['attack', 'combo', 'dash attack', 'jump attack']:
                # 轻攻击/普通/跑攻/跳攻：第 1 帧到最后一帧 (留 1 帧前摇，如果是单帧则直接第 0 帧)
                start_frame = max(0, min(1, total_frames - 1))
                end_frame = max(0, total_frames - 1)
            else:
                # 重攻击/必杀技/终结技：前摇 30% 到 90%
                start_frame = int(total_frames * 0.3)
                end_frame = max(start_frame, int(total_frames * 0.9))
            
            if start_frame <= self.image_index <= end_frame:
                # 判定盒尺寸优化：根据动作类型调整
                if self.status in ['super move 1', 'super move 2', 'super move 3', 'finisher']:
                    # 重攻击/必杀技拥有大范围霸道的判定盒 (70% 宽度，40% 高度)
                    hw = int(self.rect.width * 0.7)
                    hh = int(self.rect.height * 0.4)
                else:
                    # 普通攻击/轻攻击判定盒 (25% 宽度，20% 高度)，必须贴近碰到人才有判定
                    hw = int(self.rect.width * 0.25)
                    hh = int(self.rect.height * 0.2)
                
                # 针对特定招式调整判定高度
                y_offset = 0
                if self.status == 'jump attack':
                    y_offset = 20 # 踢腿偏下
                elif self.status == 'head hit': # 某些特殊动作
                    y_offset = -30

                hitbox = pygame.Rect(0, 0, hw, hh)
                
                # 核心：根据面向（to_right）精准放置在拳头/脚部位置
                if self.to_right:
                    hitbox.midleft = self.rect.center
                    hitbox.x += 10 # 稍微向外偏移
                else:
                    hitbox.midright = self.rect.center
                    hitbox.x -= 10
                
                hitbox.y += y_offset
                return hitbox
        return None

    def take_hit(self, damage, knockback, attacker):
        # 仅在非受击状态、没死、且无敌帧已结束时才接受受击
        if not self.is_hit and self.health > 0 and self.invincible_timer <= 0:
            self.health -= max(0, damage)
            self.is_hit = True
            # 受击僵直时间根据伤害调整
            self.hit_timer = 0.4 + (damage / 500) 
            
            # 动态顿帧 (Hit Stop): 根据伤害等级动态调整阻滞感，强化打击重量感
            if damage < 60:
                self.hit_stop_timer = 0.08
            elif damage < 100:
                self.hit_stop_timer = 0.12
            elif damage < 250:
                self.hit_stop_timer = 0.18
            else:
                self.hit_stop_timer = 0.25
            
            # 确定受击与击飞状态：空中受击、重击 (>=100)、或死亡时触发击飞 knockdown
            if self.pos.y < self.ground_y or damage >= 100 or self.health <= 0:
                self.status = 'knock down'
                # 赋予物理抛物线击飞初速度，支持空中追击连招
                self.jump_velocity = -120 - knockback * 1.5
            else:
                self.status = 'body hit'
            
            # 强制重置动画帧
            self.image_index = 0
            
            # --- 真实格斗受力物理系统：攻击方自我反震 (Attacker Recoil) 与 墙角反作用力 (Corner Pushback) ---
            from src.settings import SCREEN_WIDTH
            push_dir = 1 if self.pos.x > attacker.pos.x else -1
            attacker_push_dir = -push_dir
            
            # 检测被攻击者是否已被逼入墙角 (舞台左限 -500 + 40, 右限 SCREEN_WIDTH + 500 - 40)
            is_cornered_left = (self.pos.x <= -460 and push_dir == -1)
            is_cornered_right = (self.pos.x >= SCREEN_WIDTH + 460 and push_dir == 1)
            
            if is_cornered_left or is_cornered_right:
                # 墙角反震转移：被攻击者由于背后有坚硬墙壁无法后退，反作用力100%转移给攻击者！
                self.knockback_velocity.x = 0
                attacker.knockback_velocity.x = attacker_push_dir * (knockback * 75.0)
            else:
                # 正常力学分布：被攻击者承受100%击击退滑行，攻击者受到较小(25%)的反震力，防止近身压制粘人
                self.knockback_velocity.x = push_dir * (knockback * 75.0)
                attacker.knockback_velocity.x = attacker_push_dir * (knockback * 75.0 * 0.25)

    def resolve_player_collision(self, other):
        # 简单的圆形/距离碰撞，防止重叠
        dist = self.pos.x - other.pos.x
        min_dist = 60 # 最小间距
        if abs(dist) < min_dist and abs(self.pos.y - other.pos.y) < 30:
            push = (min_dist - abs(dist)) * 0.5
            direction = 1 if dist > 0 else -1
            self.pos.x += direction * push
            other.pos.x -= direction * push

    def update(self, dt):
        if dt > 0:
            # 递减连击时间
            if self.combo_timer > 0:
                self.combo_timer -= dt
                if self.combo_timer <= 0:
                    self.combo_count = 0

            # 递减残影透明度并清理过期残影 (Ghost Trails decay)
            for ghost in self.ghosts:
                ghost['alpha'] -= dt * 450.0
            self.ghosts = [g for g in self.ghosts if g['alpha'] > 0]

            # 缓动红色血量阴影槽 (Smooth Damage Shadow Bar decay)
            if self.shadow_health > self.health:
                self.shadow_health -= (self.shadow_health - self.health) * 0.08
                if self.shadow_health - self.health < 1.0:
                    self.shadow_health = self.health
            elif self.shadow_health < self.health:
                # 治疗或血量重置时瞬间同步，防止阴影槽反常滞后
                self.shadow_health = self.health

            # 递减无敌时间帧
            if self.invincible_timer > 0:
                self.invincible_timer -= dt

            # 顿帧处理：如果处于顿帧中，跳过逻辑更新，保持当前姿势
            if self.hit_stop_timer > 0:
                self.hit_stop_timer -= dt
                return

            if self.health <= 0:
                # 死亡后只播放倒地动画，不再接受输入
                if self.status != 'knock down':
                    self.status = 'knock down'
                    self.image_index = 0
                self.mov(dt)  # 死亡状态依然运行物理（落回地面）
            elif self.is_hit:
                self.hit_timer -= dt
                if self.hit_timer <= 0:
                    self.is_hit = False
                    if self.status in ['body hit', 'head hit']:
                        self.status = 'idle'
                        self.invincible_timer = 0.20  # 普攻受击硬直结束后给予 0.2 秒无敌帧，以防多段死锁
                    elif self.status == 'knock down':
                        # 如果在地面上，直接起立；如果还在空中，保持倒地姿态继续下落，等落地再起立
                        if self.pos.y >= self.ground_y:
                            self.status = 'idle'
                            self.invincible_timer = 0.40  # 起地起立给予 0.4 秒无敌帧，防起身死锁压制
                self.mov(dt)  # 受击状态依然运行物理（受击退、重力下落）
            else:
                self.handle_input()
                self.mov(dt)
        self.update_image(dt)

    def mov(self, dt):
        if self.direction.magnitude() == 0 and self.status in ['walk', 'run']:
            self.status = 'idle'
        
        # 死亡状态不能进行水平控制移动，但继续向下运行物理重力与滑动击退
        if self.status == 'knock down' and self.health <= 0:
            self.direction.update(0, 0)

        # 不能移动的动画 (包含胜利和炫耀展示，防止出招/胜利后平移飘走，新增 combo 以免横向滑行)
        if self.status in ['idle', 'super move 1', 'super move 2', 'super move 3', 'finisher', 'attack', 'combo', 'body hit', 'head hit', 'knock down', 'victory', 'show off']:
            self.direction.update(0, 0)

        # 计算跳起后垂直运动。落地后还原
        is_airborne = self.pos.y < self.ground_y
        if is_airborne or self.status in ['jump', 'jump attack', 'super move 3', 'knock down']:
            if self.pos.y < self.ground_y or self.jump_velocity < 0:
                self.jump_velocity += self.gravity * dt
                self.pos.y += self.jump_velocity * dt
            else:
                self.pos.y = self.ground_y
                self.jump_velocity = 0
                
                # 落地状态判定
                if self.status == 'knock down':
                    # 如果受击硬直已经结束，立刻起立；否则保持躺地，等 update 里硬直结束再起立
                    if not self.is_hit:
                        self.status = 'idle'
                        self.invincible_timer = 0.40  # 起立起身无敌帧 0.4 秒，防止无限起身压制
                elif self.status in ['jump', 'jump attack', 'super move 3', 'body hit', 'head hit']:
                    self.status = 'idle'
        
        # 计算位置 (包括普通行走/跑动速度和物理击退滑行速度)
        new_pos = self.pos + (self.direction * self.speed + self.knockback_velocity) * dt
        
        # 击退滑动速度阻尼衰减 (基于 dt 的真实物理阻尼衰减，避免高帧率时衰减过快)
        self.knockback_velocity.x -= self.knockback_velocity.x * 12.0 * dt
        if abs(self.knockback_velocity.x) < 5.0:
            self.knockback_velocity.x = 0
        
        # 边界限制 (支持摄像机滚动，扩大舞台物理边界)
        from src.settings import SCREEN_WIDTH
        # 允许玩家走出初始屏幕，舞台总宽度设为 屏幕宽 + 1000 像素
        if -500 < new_pos.x < SCREEN_WIDTH + 500:
            self.pos.x = new_pos.x
        
        self.rect = self.image.get_rect(midbottom=self.pos)

    def handle_input(self):
        ctrl = self.device_info['controller']
        
        # 寻找对手，用于瞬时自动面向修正 (Auto-Facing Correction)
        opponent = next((p for p in self.groups()[0] if isinstance(p, Player) and p != self), None)
        
        # 如果移动锁激活，且玩家已经松开了所有方向键，则解除锁定
        if self.movement_locked:
            if not (ctrl.performed('left') or ctrl.performed('right') or ctrl.performed('up') or ctrl.performed('down')):
                self.movement_locked = False

        # 连击链检测 (Attack -> Combo)
        if self.status == 'attack':
            if ctrl.performed('attack') and self.image_index >= 2.0:
                if 'combo' in self.images:
                    self.status = 'combo'
                    self.image_index = 0
                    if opponent:
                        self.to_right = (opponent.pos.x > self.pos.x)

        # 切换状态
        if self.status == 'idle':
            if not self.movement_locked:
                for key in ['left', 'right', 'up', 'down']:
                    if ctrl.performed(key):
                        self.status = 'walk'
                if ctrl.performed('run left') or ctrl.performed('run right'):
                    self.status = 'run'
        elif self.status != 'walk':
            ctrl.last_released_key = ''  # 避免在其他动画中提前触发跑步事件

        # 在 idle, walk, run 下，且没有移动锁时允许触发大招、跳跃等
        if self.status in ['idle', 'walk', 'run'] and not self.movement_locked:
            for key in ['super move 1', 'super move 2', 'finisher', 'jump']:
                if ctrl.performed(key):
                    # 记录之前的状态，用于判断起跳来源
                    prev_status = self.status
                    self.status = key
                    self.image_index = 0
                    
                    # 瞬时面向修正 (仅针对大招与终结技)
                    if key in ['super move 1', 'super move 2', 'finisher'] and opponent:
                        self.to_right = (opponent.pos.x > self.pos.x)
                        
                    # 如果是从奔跑中触发其他任何招式（跳跃、必杀技、终结技），全部施加移动锁（落后/收招后处于僵直）
                    if prev_status == 'run':
                        self.movement_locked = True
                        
                    if key == 'jump':  # 设置跳起初始状态
                        self.ground_y = self.pos[1]
                        self.jump_velocity = -self.jump_strength
                        # 如果是从奔跑中跳起，触发“冲刺大跳”
                        if prev_status == 'run':
                            self.direction.x *= 1.5
                            self.jump_velocity *= 1.15

            # 如果非奔跑状态，也允许触发普通 attack
            if self.status != 'run':
                if ctrl.performed('attack'):
                    self.status = 'attack'
                    self.image_index = 0
                    if opponent:
                        self.to_right = (opponent.pos.x > self.pos.x)

        if self.status in ['walk', 'jump', 'jump attack']:
            # 水平运动状态
            if ctrl.performed('left'):
                self.direction.x = -1
                self.to_right = False
            elif ctrl.performed('right'):
                self.direction.x = 1
                self.to_right = True
            else:
                self.direction.x = 0

        # 纯 2D 横版格斗：Y 轴移动向量锁死为 0
        self.direction.y = 0

        if self.status == 'run':
            if ctrl.performed('attack'):
                if 'dash attack' in self.images:  # 部分人物有此动画 (如 bai, raymon, shuo)
                    self.status = 'dash attack'
                    self.image_index = 0
                    self.direction.x *= 2.0  # 冲刺攻击位移倍率 2.0
                    self.movement_locked = True
                    if opponent:
                        self.to_right = (opponent.pos.x > self.pos.x)
                else:
                    # Dora 没有 dash attack, 回退到普通攻击但给予冲刺滑行
                    self.status = 'attack'
                    self.image_index = 0
                    self.direction.x *= 1.5
                    self.movement_locked = True
                    if opponent:
                        self.to_right = (opponent.pos.x > self.pos.x)
            elif ctrl.performed('run left'):
                self.direction.x = -3
                self.to_right = False
            elif ctrl.performed('run right'):
                self.direction.x = 3
                self.to_right = True
            else:
                self.direction.x = 0

        if self.status == 'jump':
            if ctrl.performed('attack'):
                if 'jump attack' in self.images:  # 部分人物确动画
                    self.status = 'jump attack'
                    if opponent:
                        self.to_right = (opponent.pos.x > self.pos.x)
            elif ctrl.performed('super move 1'):
                self.status = 'super move 3'
                if opponent:
                    self.to_right = (opponent.pos.x > self.pos.x)
                
        if self.status in ['jump', 'jump attack']:
            # 跳起水平速度增益 (从 1.5 提升至 2.2，让空中方向盘摇杆移动显著变快)
            self.direction.x *= 2.2
