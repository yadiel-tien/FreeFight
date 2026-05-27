from random import randint, random

import pygame

from src.core.constants import SCREEN_WIDTH, SCREEN_HEIGHT
from src.core.support import resource_path


class PlayerInfoCard:
    def __init__(self, player_index, image, surface: pygame.Surface):
        self.player_index = player_index
        self.screen = surface
        self.avatar = pygame.transform.scale(image, (64, 64)) # 放大头像，更具冲击力
        
        from src.core.constants import SCREEN_WIDTH
        if player_index == 'p1':
            # P1 (左侧)：头像在最左边，血条向右伸展
            self.avatar_pos = (20, 20)
            self.blood_rect = pygame.rect.Rect(95, 30, 480, 24)
        else:
            # P2 (右侧)：头像在最右边，血条向左伸展
            self.avatar_pos = (SCREEN_WIDTH - 20 - 64, 20)
            self.blood_rect = pygame.rect.Rect(SCREEN_WIDTH - 95 - 480, 30, 480, 24)

    def display(self, health, shadow_health, max_health, energy=0) -> None:
        # 1. 绘制头像
        self.screen.blit(self.avatar, self.avatar_pos)
        
        # 2. 绘制黑色血条背景底槽与细白描边
        pygame.draw.rect(self.screen, (20, 20, 20), self.blood_rect, border_radius=4)
        pygame.draw.rect(self.screen, (80, 80, 80), self.blood_rect, 1, border_radius=4)
        
        # 3. 计算比例
        shadow_ratio = max(0.0, min(1.0, shadow_health / max_health))
        actual_ratio = max(0.0, min(1.0, health / max_health))
        
        # 4. 绘制红色残血阴影层 (Damage Shadow Bar)
        shadow_rect = self.blood_rect.copy().inflate(-4, -4)
        shadow_w = int(shadow_rect.w * shadow_ratio)
        
        if self.player_index == 'p1':
            # P1 正常从左往右增长
            shadow_rect.w = shadow_w
        else:
            # P2 镜像：右对齐往左生长
            shadow_rect.x = shadow_rect.right - shadow_w
            shadow_rect.w = shadow_w
            
        pygame.draw.rect(self.screen, (200, 30, 30), shadow_rect, border_radius=2)
        
        # 5. 绘制实际当前血条层 (Actual Health Bar)
        rect = self.blood_rect.copy().inflate(-4, -4)
        actual_w = int(rect.w * actual_ratio)
        
        if self.player_index == 'p1':
            rect.w = actual_w
        else:
            rect.x = rect.right - actual_w
            rect.w = actual_w
            
        # 根据实际血量比例动态变色 (绿 -> 黄 -> 红)
        if actual_ratio > 0.5:
            color = (0, 230, 100) # 亮绿
        elif actual_ratio > 0.2:
            color = (240, 200, 10) # 亮黄
        else:
            color = (255, 30, 30) # 亮红
            
        pygame.draw.rect(self.screen, color, rect, border_radius=2)
        
        # 6. 绘制能量槽 (Energy Gauge Bar) - 在血条下方
        import math
        energy_ratio = max(0.0, min(1.0, energy / 100.0))
        e_bar_h = 8
        e_bar_y = self.blood_rect.bottom + 4
        e_bar_rect = pygame.Rect(self.blood_rect.x, e_bar_y, self.blood_rect.width, e_bar_h)
        
        # 能量槽底色框
        pygame.draw.rect(self.screen, (15, 15, 30), e_bar_rect, border_radius=3)
        pygame.draw.rect(self.screen, (60, 60, 80), e_bar_rect, 1, border_radius=3)
        
        # 能量填充条 (动态变色：亮青 -> 金色)
        e_fill_rect = e_bar_rect.copy().inflate(-3, -3)
        e_fill_w = int(e_fill_rect.w * energy_ratio)
        
        if e_fill_w > 0:
            if self.player_index == 'p1':
                e_fill_rect.w = e_fill_w
            else:
                e_fill_rect.x = e_fill_rect.right - e_fill_w
                e_fill_rect.w = e_fill_w
            
            # 颜色根据能量等级渐变
            if energy_ratio < 0.3:
                e_color = (0, 180, 220)   # 亮青 (能量低)
            elif energy_ratio < 0.7:
                e_color = (80, 200, 255)  # 天蓝 (能量中)
            elif energy_ratio < 1.0:
                e_color = (200, 180, 40)  # 金黄 (能量高)
            else:
                # 满能量闪烁效果 (Full Energy Pulse)
                pulse = int(200 + 55 * math.sin(pygame.time.get_ticks() / 100))
                e_color = (255, pulse, 0)  # 耀眼橙金色呼吸闪烁
            
            pygame.draw.rect(self.screen, e_color, e_fill_rect, border_radius=2)


class HitSpark(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA).convert_alpha()
        # 绘制一个简单的闪光十字
        pygame.draw.line(self.image, (255, 255, 255), (0, 20), (40, 20), 4)
        pygame.draw.line(self.image, (255, 255, 255), (20, 0), (20, 40), 4)
        # 内部核心
        pygame.draw.circle(self.image, (255, 255, 0), (20, 20), 10)
        
        self.rect = self.image.get_rect(center=pos)
        self.start_time = pygame.time.get_ticks()
        self.duration = 100 # 极短的闪烁

    def update(self, dt):
        if pygame.time.get_ticks() - self.start_time > self.duration:
            self.kill()


class Particle(pygame.sprite.Sprite):
    # 类属性缓存图像，避免重复加载
    cached_ball = None

    def __init__(self, groups):
        super().__init__(groups)
        if Particle.cached_ball is None:
            Particle.cached_ball = pygame.image.load(resource_path('assets/graphics/element/ball.png')).convert_alpha()
        
        size = randint(8, 18)
        self.original_image = pygame.transform.scale(Particle.cached_ball, (size, size))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(randint(0, SCREEN_WIDTH), randint(SCREEN_HEIGHT - 50, SCREEN_HEIGHT)))
        
        self.alpha = float(randint(200, 255))
        self.start_time = pygame.time.get_ticks()
        self.life_time = randint(3000, 5000)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.direction = pygame.math.Vector2(randint(-2, 2), randint(-4, -1))
        self.speed = randint(20, 30)
        self.alpha_speed = -30 # 稍微快一点的淡出

        self.count = 0

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        
        # 左右随机摆动
        if current_time // 100 > self.count:
            self.direction.x += randint(-1, 1) * 0.2
            self.count += 1
            
        if elapsed > 500:
            self.alpha += dt * self.alpha_speed
            if self.alpha <= 0:
                self.kill()
                return
            
            # 重新创建带 alpha 的图像，避免 set_alpha 在某些混色模式下的方框问题
            self.image = self.original_image.copy()
            # 这种方式对带有 SRCALPHA 的 Surface 最稳定
            alpha_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            alpha_surf.fill((255, 255, 255, int(self.alpha)))
            self.image.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.pos += self.speed * self.direction * dt
        self.rect.center = self.pos
        if elapsed > self.life_time:
            self.kill()


class Particles:
    def __init__(self, probability, surface: pygame.Surface):
        self.group = pygame.sprite.Group()
        self.screen = surface
        self.probability = probability

    def update(self, dt):
        if random() < self.probability:
            Particle(self.group)
        self.group.update(dt)
        self.group.draw(self.screen)


class ShockWave(pygame.sprite.Sprite):
    def __init__(self, rect, groups, player_name, status):
        super().__init__(groups)
        self.rect = pygame.Rect(rect)
        self.player_name = player_name.lower()
        self.status = status
        
        # 扩大判定盒尺寸以容纳膨胀光圈
        self.max_w = int(self.rect.width * 1.6)
        self.max_h = int(self.rect.height * 1.6)
        self.image = pygame.Surface((self.max_w, self.max_h), pygame.SRCALPHA).convert_alpha()
        
        self.rect = self.image.get_rect(center=self.rect.center)
        self.start_time = pygame.time.get_ticks()
        self.duration = 350 # 350ms 华丽气浪持续时间
        
        # 根据不同角色的元素设定，定义其专属色系与元素类型
        if self.player_name == 'bai':
            self.color = (180, 240, 255) # 冰晶蓝 (Ice Crystal Blue)
            self.element = 'ice'
        elif self.player_name == 'dora':
            self.color = (255, 75, 0) # 炽炎橙 (Blazing Orange-Red)
            self.element = 'fire'
        elif self.player_name == 'raymon':
            self.color = (180, 0, 255) # 邪能紫 (Plasma Purple-Violet)
            self.element = 'thunder'
        elif self.player_name == 'shuo':
            self.color = (0, 255, 120) # 翡翠绿 (Neon Jade Green)
            self.element = 'wind'
        else:
            self.color = (255, 200, 40) # 经典金
            self.element = 'generic'

    def update(self, dt):
        elapsed = pygame.time.get_ticks() - self.start_time
        ratio = elapsed / self.duration
        if ratio >= 1.0:
            self.kill()
            return
            
        self.image.fill((0, 0, 0, 0))
        alpha = int(200 * (1.0 - ratio))
        current_w = int(self.max_w * (0.3 + 0.7 * ratio))
        current_h = int(self.max_h * (0.3 + 0.7 * ratio))
        
        draw_rect = pygame.Rect(0, 0, current_w, current_h)
        draw_rect.center = (self.max_w // 2, self.max_h // 2)
        
        cx, cy = self.max_w // 2, self.max_h // 2
        dw_w, dw_h = current_w // 2, current_h // 2
        import math
        
        # --- 针对不同角色绘制完全跳出“简单圆形”的顶级元素姿态 ---
        if self.element == 'ice':
            # Bai (冰霜): 晶莹坚硬的八角冰霜结晶星与冰锥射线 (No generic circles!)
            points = []
            for i in range(8):
                angle = i * 45
                rad = math.radians(angle)
                # 交替长短半径形成晶莹的八角冰星
                r = dw_w if i % 2 == 0 else dw_w // 2
                px = cx + int(r * math.cos(rad))
                py = cy + int(r * math.sin(rad))
                points.append((px, py))
                
            # 绘制冰星半透明内核与高亮白框
            pygame.draw.polygon(self.image, (*self.color, int(alpha * 0.3)), points)
            pygame.draw.polygon(self.image, (255, 255, 255, alpha), points, 2)
            
            # 绘制冰晶四射棱线
            for pt in points:
                pygame.draw.line(self.image, (255, 255, 255, int(alpha * 0.65)), (cx, cy), pt, 1)
            
        elif self.element == 'fire':
            # Dora (烈焰): 混乱有机膨胀的火山火球大爆发与火星粒子 (No perfect circles!)
            from random import seed, randint, random
            # 使用 start_time 设定随机种子，确保同一道冲击波在生命周期内形状随机但每帧稳定
            seed(self.start_time)
            for i in range(6):
                offset_x = randint(-24, 24)
                offset_y = randint(-24, 24)
                radius = int((dw_w * 0.7) * (0.8 + 0.4 * random()))
                
                # 绘制火山红、炽燃橙、核心黄三层重叠火焰颗粒，营造真实火浪爆发感
                pygame.draw.circle(self.image, (255, 30, 0, int(alpha * 0.25)), (cx + offset_x, cy + offset_y), radius)
                pygame.draw.circle(self.image, (255, 120, 0, int(alpha * 0.45)), (cx + offset_x, cy + offset_y), int(radius * 0.75))
                pygame.draw.circle(self.image, (255, 230, 0, int(alpha * 0.85)), (cx + offset_x, cy + offset_y), int(radius * 0.4))
            
        elif self.element == 'thunder':
            # Raymon (紫电): 激荡狂野的八向雷电闪击电网 (No circles at all!)
            from random import randint
            # 绘制 8 个方向疯狂激射的折线雷电束
            for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                rad = math.radians(angle + randint(-12, 12))
                max_dist = int(dw_w * 1.1)
                
                # 随机 4 段雷击折线
                pts = [(cx, cy)]
                for step in range(1, 4):
                    dist = (max_dist * step) // 3
                    px = cx + int(dist * math.cos(rad)) + randint(-16, 16)
                    py = cy + int(dist * math.sin(rad)) + randint(-16, 16)
                    pts.append((px, py))
                
                # 绘制电弧紫色外发光与白亮核心
                pygame.draw.lines(self.image, (*self.color, int(alpha * 0.6)), False, pts, 4)
                pygame.draw.lines(self.image, (255, 255, 255, alpha), False, pts, 2)
                
        elif self.element == 'wind':
            # Shuo (风暴): 四股螺旋向外激流旋转的绿色狂风风蚀气流 (No concentric circles!)
            # 绘制随着扩张速度逆时针疯狂旋转的螺旋气浪
            for spiral in range(4):
                start_angle = spiral * 90 + int(ratio * 360) # 动感风场涡旋自转
                points = []
                for step in range(8):
                    angle = start_angle + step * 25
                    rad = math.radians(angle)
                    # 气流线圈不断螺旋半径放大
                    r = int(dw_w * (step / 8.0))
                    px = cx + int(r * math.cos(rad))
                    py = cy + int(r * math.sin(rad))
                    points.append((px, py))
                
                pygame.draw.lines(self.image, (*self.color, alpha), False, points, 2)
                pygame.draw.lines(self.image, (200, 255, 220, int(alpha * 0.55)), False, points, 4)
            
        else:
            # 降级备份圈
            pygame.draw.ellipse(self.image, (*self.color, alpha), draw_rect, max(1, int(4 * (1.0 - ratio))))
            pygame.draw.ellipse(self.image, (*self.color, int(alpha * 0.25)), draw_rect.inflate(-6, -6))
