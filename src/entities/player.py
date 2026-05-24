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
        player_index = int(info['player_index'][1:])
        self.pos = pygame.math.Vector2(300 * player_index, 700)
        self.rect = self.image.get_rect(midbottom=self.pos)
        self.speed = 150
        self.direction = pygame.math.Vector2()
        self.to_right = True

        # 战斗属性
        self.max_health = 1000
        self.health = 1000
        self.is_hit = False
        self.hit_timer = 0
        self.hit_stop_timer = 0 # 击中冻结时间 (Hit Stop)
        
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

        # 临时血条展示
        avatar = import_pic(f'assets/graphics/sprites/{info["player_name"]}/avatar.png')
        self.blood_ui = PlayerInfoCard(((player_index - 1) * 300 + 20, 20), avatar, self.display_surf)

        # 跳跃控制
        self.gravity = 800
        self.ground_y = 700
        self.jump_velocity = 0
        self.jump_strength = 500

        # 移动锁控制 (冲刺攻击后需释放按键重新按下才能移动)
        self.movement_locked = False

    def update_image(self, dt):
        # frames是一个系列动画图片的列表
        frames = self.images[self.status]
        # 增加动画播放速度
        self.image_index += dt * 10
        
        # 动画结束后动作
        if self.image_index >= len(frames):
            self.image_index = 0
            # 维持最后一帧的状态：跳跃或被击倒
            if self.status in ['jump', 'jump attack', 'knock down']:
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

        # 左右转向
        self.image = pygame.transform.flip(scaled, self.to_right, False)

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
        if self.status in self.attack_data:
            active_range = self.attack_data[self.status]['active']
            if active_range[0] <= self.image_index <= active_range[1]:
                # 判定盒尺寸优化：根据动作类型调整
                # 默认判定盒稍微宽一点
                hw = int(self.rect.width * 0.5)
                hh = int(self.rect.height * 0.3)
                
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

    def take_hit(self, damage, knockback, attacker_pos_x):
        if not self.is_hit and self.health > 0:
            self.health -= max(0, damage)
            self.is_hit = True
            # 受击僵直时间根据伤害调整
            self.hit_timer = 0.4 + (damage / 500) 
            # 顿帧 (Hit Stop): 增加受击瞬间的阻滞感
            self.hit_stop_timer = 0.12 # 120ms 的顿帧
            
            # 确定受击动画
            if self.pos.y < self.ground_y: # 在空中受击
                self.status = 'knock down'
            elif self.health <= 0:
                self.status = 'knock down'
            else:
                self.status = 'body hit' if damage < 100 else 'head hit'
            
            # 强制重置动画帧
            self.image_index = 0
            
            # 计算击退方向
            push_dir = 1 if self.pos.x > attacker_pos_x else -1
            # 击退距离限制，防止出界
            self.pos.x += push_dir * knockback

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
                    if self.status in ['body hit', 'head hit', 'knock down']:
                        self.status = 'idle'
                self.mov(dt)  # 受击状态依然运行物理（受击退、重力下落）
            else:
                self.handle_input()
                self.mov(dt)
        self.update_image(dt)
        # self.blood_ui.display 已移至 Level.run 统一最上层渲染

    def mov(self, dt):
        if self.direction.magnitude() == 0 and self.status in ['walk', 'run']:
            self.status = 'idle'
        
        # 死亡状态不能移动
        if self.status == 'knock down' and self.health <= 0:
            self.direction.update(0, 0)
            return

        # 不能移动的动画
        if self.status in ['idle', 'super move 1', 'super move 2', 'super move 3', 'finisher', 'attack', 'body hit', 'head hit', 'knock down']:
            self.direction.update(0, 0)

        # 计算跳起后垂直运动。落地后还原
        if self.status in ['jump', 'jump attack', 'super move 3', 'knock down']:
            if self.pos[1] <= self.ground_y:
                self.jump_velocity += self.gravity * dt
                self.pos.y += self.jump_velocity * dt
            else:
                self.pos.y = self.ground_y
                self.jump_velocity = 0
                if self.status != 'knock down': # 击倒动画特殊处理
                    self.status = 'idle'
        
        # 计算位置
        new_pos = self.pos + self.direction * self.speed * dt
        
        # 边界限制 (支持摄像机滚动，扩大舞台物理边界)
        from src.settings import SCREEN_WIDTH
        # 允许玩家走出初始屏幕，舞台总宽度设为 屏幕宽 + 1000 像素
        if -500 < new_pos.x < SCREEN_WIDTH + 500:
            self.pos.x = new_pos.x
        


        self.rect = self.image.get_rect(midbottom=self.pos)
    def handle_input(self):
        ctrl = self.device_info['controller']
        
        # 如果移动锁激活，且玩家已经松开了所有方向键，则解除锁定
        if self.movement_locked:
            if not (ctrl.performed('left') or ctrl.performed('right') or ctrl.performed('up') or ctrl.performed('down')):
                self.movement_locked = False

        # 连招链检测 (Attack -> Combo)
        if self.status == 'attack':
            if ctrl.performed('attack') and self.image_index >= 2.0:
                if 'combo' in self.images:
                    self.status = 'combo'
                    self.image_index = 0

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
                else:
                    # Dora 没有 dash attack, 回退到普通攻击但给予冲刺滑行
                    self.status = 'attack'
                    self.image_index = 0
                    self.direction.x *= 1.5
                    self.movement_locked = True
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
            elif ctrl.performed('super move 1'):
                self.status = 'super move 3'
            # 跳起水平速度增益
            self.direction.x *= 1.5
