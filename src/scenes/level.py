import pygame

from src.ui.components.dialogue import Dialogue
from src.entities.player import Player
from src.scenes.scene import Scene, SceneStatus
from src.entities.sprites import DynamicBackGround
from src.core.support import resource_path


class Level(Scene):
    def __init__(self, game_input, surface: pygame.Surface):
        super().__init__(game_input, surface)
        self.dialogue = Dialogue(game_input, self.screen)
        self.display_sprites = pygame.sprite.Group()
        self.effect_sprites = pygame.sprite.Group()
        self.create_player()
        DynamicBackGround(self.display_sprites)
        
        # 摄像机与震动
        self.camera_offset = pygame.math.Vector2()
        self.shake_timer = 0
        self.shake_intensity = 0

        # 调试模式：显示判定框 (设置为 True 开启)
        self.debug_mode = False 

        # 结算逻辑
        self.match_ended = False
        self.winner = None
        self.settlement_timer = 0
        self.show_results = False

    def apply_shake(self, duration, intensity):
        self.shake_timer = duration
        self.shake_intensity = intensity

    def update_camera(self, dt):
        players = [sprite for sprite in self.display_sprites if isinstance(sprite, Player)]
        if players:
            avg_x = sum(p.pos.x for p in players) / len(players)
            from src.settings import SCREEN_WIDTH
            target_offset_x = avg_x - SCREEN_WIDTH / 2
            
            # 摄像机平滑追踪
            self.camera_offset.x += (target_offset_x - self.camera_offset.x) * 0.1
            
            # 限制滚动范围
            max_scroll = 500 
            self.camera_offset.x = max(-max_scroll, min(max_scroll, self.camera_offset.x))
            
            # 处理屏幕震动
            if self.shake_timer > 0:
                self.shake_timer -= dt
                import random
                self.camera_offset.x += random.uniform(-self.shake_intensity, self.shake_intensity)
                self.camera_offset.y = random.uniform(-self.shake_intensity, self.shake_intensity)
            else:
                self.camera_offset.y = 0

    def create_player(self):
        for info in self.game_input.controllers.values():
            if info['player_index'] != 'p0':
                Player(info, self.display_sprites, self.dialogue, self.screen)

    def check_collisions(self):
        if self.match_ended: return

        players = [sprite for sprite in self.display_sprites if isinstance(sprite, Player)]
        # 1. 攻击碰撞检测
        for attacker in players:
            hitbox = attacker.get_hitbox()
            if hitbox:
                for target in players:
                    if target != attacker and not target.is_hit and target.health > 0:
                        hurtbox = target.get_hurtbox()
                        if hitbox.colliderect(hurtbox):
                            data = attacker.attack_data[attacker.status]
                            target.take_hit(data['damage'], data['knockback'], attacker.pos.x)
                            
                            # 双方顿帧 (Hit Stop)
                            attacker.hit_stop_timer = 0.12
                            
                            # 触发震屏
                            self.apply_shake(0.15, 8 if data['damage'] > 100 else 4)

                            # 生成打击特效 (在碰撞点)
                            from src.ui.ui import HitSpark
                            spark_pos = hitbox.clip(hurtbox).center
                            HitSpark(spark_pos, self.effect_sprites)
                            
                            # 检测是否产生胜者
                            if target.health <= 0:
                                self.match_ended = True
                                self.settlement_timer = 2.0 # 2秒后显示结算界面
                                for p in players:
                                    if p.health > 0:
                                        self.winner = p
                                        if 'victory' in p.images: p.status = 'victory'
                                        elif 'show off' in p.images: p.status = 'show off'
                                        p.image_index = 0
        
        # 2. 实体挤压碰撞 (防止穿模)
        for i in range(len(players)):
            for j in range(i + 1, len(players)):
                players[i].resolve_player_collision(players[j])

    def draw_settlement(self):
        from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # 绘制胜利文字
        from src.core.config import config
        lang = config.get('system', 'language')
        
        # 使用系统字体或素材字体
        path = resource_path('assets/font/impact.ttf')
        font = pygame.font.Font(path, 100)
        
        win_text = f"{self.winner.device_info['player_name'].upper()} WIN!" if self.winner else "MATCH OVER"
        text_surf = font.render(win_text, True, 'orange')
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50))
        self.screen.blit(text_surf, text_rect)
        
        # 提示按键
        small_font = pygame.font.Font(path, 30)
        hint = "PRESS START/MENU TO RETURN" if lang == 'en_US' else "按下 菜单键 返回主页"
        hint_surf = small_font.render(hint, True, 'white')
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 80))
        self.screen.blit(hint_surf, hint_rect)

    def run(self, dt):
        # 1. 处理逻辑
        if not self.dialogue.showing:
            if not self.show_results:
                self.check_collisions()
                self.update_camera(dt)
            self.effect_sprites.update(dt)
            
            # 结算计时
            if self.match_ended and not self.show_results:
                self.settlement_timer -= dt
                if self.settlement_timer <= 0:
                    self.show_results = True

        # 2. 分层渲染 (应用摄像机偏移)
        # 第一层：背景 (非 Player 类)
        for sprite in self.display_sprites:
            if not isinstance(sprite, Player):
                sprite.update(0 if self.dialogue.showing else dt)
                offset_pos = sprite.rect.topleft - self.camera_offset
                self.screen.blit(sprite.image, offset_pos)

        # 第二层：玩家 (根据 Y 轴排序实现纵深感)
        players = sorted([s for s in self.display_sprites if isinstance(s, Player)], key=lambda p: p.rect.y)
        for player in players:
            player.update(0 if self.dialogue.showing else dt)
            offset_pos = player.rect.topleft - self.camera_offset
            self.screen.blit(player.image, offset_pos)

            # 调试渲染：绘制判定框
            if self.debug_mode:
                # 绘制受击盒 (绿色)
                hurtbox = player.get_hurtbox()
                pygame.draw.rect(self.screen, (0, 255, 0), hurtbox.move(-self.camera_offset.x, -self.camera_offset.y), 2)
                # 绘制攻击盒 (红色)
                hitbox = player.get_hitbox()
                if hitbox:
                    pygame.draw.rect(self.screen, (255, 0, 0), hitbox.move(-self.camera_offset.x, -self.camera_offset.y), 2)
        
        # 第三层：特效
        for sprite in self.effect_sprites:
            offset_pos = sprite.rect.topleft - self.camera_offset
            self.screen.blit(sprite.image, offset_pos)

        # 4. 最上层：UI (血条)
        for player in players:
            player.blood_ui.display(player.health, player.max_health)
            
        # 5. 结算界面
        if self.show_results:
            self.draw_settlement()
            # 监听返回按键
            for device_info in self.game_input.controllers.values():
                if device_info['player_index'] != 'p0':
                    if device_info['controller'].ui_performed('menu'):
                        self.game_input.home_menu_index = 0
                        return SceneStatus.HOME

        # 6. 处理场景内部弹窗
        if self.dialogue.showing:
            if self.dialogue.run():
                self.game_input.home_menu_index = 0
                return SceneStatus.HOME
        else:
            # 监听系统级退出请求 (仅限已加入游戏的玩家设备)
            for instance_id, device_info in self.game_input.controllers.items():
                if device_info['player_index'] != 'p0':
                    ctrl = device_info['controller']
                    if ctrl.ui_performed('menu'):
                        from src.core.logger import logger
                        logger.info(f"[MATCH] Menu requested by {device_info['player_index']} ({device_info['player_name']}) on instance {instance_id}")
                        from src.core.config import config
                        lang = config.get('system', 'language')
                        msg = '确定要退出游戏吗？' if lang == 'zh_CN' else 'Quit match?'
                        self.dialogue.show(msg, device_info)
                        return SceneStatus.FIGHTING
                    
        return SceneStatus.FIGHTING

    def de_init(self):
        self.game_input.reset()
