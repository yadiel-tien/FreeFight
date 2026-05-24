import pygame
import math

from src.ui.components.dialogue import Dialogue
from src.entities.player import Player
from src.scenes.scene import Scene, SceneStatus
from src.entities.sprites import DynamicBackGround
from src.core.support import resource_path, import_pic


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
            
            # 摄像机平滑追踪 (提速至 0.2x，紧跟角色剧烈搏击)
            self.camera_offset.x += (target_offset_x - self.camera_offset.x) * 0.2
            
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
                            
                            # 连击计数更新
                            attacker.combo_count += 1
                            attacker.max_combo = max(attacker.max_combo, attacker.combo_count)
                            attacker.combo_timer = 1.0
                            
                            # 双方动态顿帧 (Hit Stop) - 给予双方受伤害级别相符的定格感
                            if data['damage'] < 60:
                                attacker.hit_stop_timer = 0.08
                            elif data['damage'] < 100:
                                attacker.hit_stop_timer = 0.12
                            elif data['damage'] < 250:
                                attacker.hit_stop_timer = 0.18
                            else:
                                attacker.hit_stop_timer = 0.25
                            
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
        
        # 1. Midnight Violet 遮罩 (Midnight Violet Glass Mask)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 8, 24, 200))
        self.screen.blit(overlay, (0, 0))
        
        # 2. 绘制中央高光结算卡片 (Victory Plaque Card)
        card_w, card_h = 820, 460
        card_x = (SCREEN_WIDTH - card_w) // 2
        card_y = (SCREEN_HEIGHT - card_h) // 2
        
        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card_surf.fill((24, 18, 48, 230))  # 深色磨砂玻璃背景底盘
        
        # 绘制金色外边框与淡色内边框
        pygame.draw.rect(card_surf, (255, 190, 40), (0, 0, card_w, card_h), 3, border_radius=12)
        pygame.draw.rect(card_surf, (255, 220, 100, 50), (2, 2, card_w - 4, card_h - 4), 1, border_radius=10)
        self.screen.blit(card_surf, (card_x, card_y))
        
        # 3. 绘制胜利者高清半身像 (Half-length Portrait)
        if self.winner:
            try:
                half_len_path = f'assets/graphics/sprites/{self.winner.device_info["player_name"]}/half_length.png'
                portrait = import_pic(half_len_path)
                orig_w, orig_h = portrait.get_size()
                scale_h = 410
                scale_w = int(orig_w * (scale_h / orig_h))
                scaled_portrait = pygame.transform.scale(portrait, (scale_w, scale_h))
                
                # 绘制半身像在卡片左侧
                self.screen.blit(scaled_portrait, (card_x + 30, card_y + (card_h - scale_h) // 2))
            except Exception as e:
                # 降级安全处理：如果没有半身像，绘制缩放后的头像
                avatar = self.winner.blood_ui.avatar
                scaled_avatar = pygame.transform.scale(avatar, (200, 200))
                self.screen.blit(scaled_avatar, (card_x + 50, card_y + 100))
                
        # 4. 绘制右侧文字面板信息 (Drop-shadow Gold Text & HP Bonus Bar & Combo & Score)
        path = resource_path('assets/font/impact.ttf')
        zh_path = resource_path('assets/font/SimHei.ttf')
        
        from src.core.config import config
        lang = config.get('system', 'language')
        
        font_large = pygame.font.Font(path, 80)
        
        if lang == 'en_US':
            font_medium = pygame.font.Font(path, 42)
            font_small = pygame.font.Font(path, 26)
        else:
            font_medium = pygame.font.Font(zh_path, 36)
            font_small = pygame.font.Font(zh_path, 22)
            
        right_center_x = card_x + 380 + (card_w - 380) // 2
        
        # "VICTORY" 大标题 (金色金属质感 + 双层黑色下投影)
        vic_text = "VICTORY"
        text_surf = font_large.render(vic_text, True, (255, 200, 40))
        shadow_surf = font_large.render(vic_text, True, (0, 0, 0))
        
        vic_x = right_center_x - text_surf.get_width() // 2
        vic_y = card_y + 40
        self.screen.blit(shadow_surf, (vic_x + 3, vic_y + 3))
        self.screen.blit(text_surf, (vic_x, vic_y))
        
        if self.winner:
            # 计算各项得分 (Calculate score components)
            hp_val = int(self.winner.health)
            max_hp_val = int(self.winner.max_health)
            hp_score = hp_val * 10
            combo_score = self.winner.max_combo * 500
            is_perfect = hp_val == max_hp_val
            perfect_bonus = 5000 if is_perfect else 0
            total_score = hp_score + combo_score + perfect_bonus

            # 1. 绘制剩余生命值 (Remaining HP Text & Bar)
            if lang == 'en_US':
                hp_text = f"REMAINING HP: {hp_val} / {max_hp_val} (+{hp_score} PTS)"
            else:
                hp_text = f"剩余生命值: {hp_val} / {max_hp_val} (+{hp_score}分)"
            hp_surf = font_small.render(hp_text, True, (0, 255, 180))  # 亮霓虹绿代表生命力
            
            hp_x = right_center_x - hp_surf.get_width() // 2
            hp_y = card_y + 130
            self.screen.blit(hp_surf, (hp_x, hp_y))
            
            # HP 微型血量槽装饰绘制
            hp_ratio = max(0.0, min(1.0, self.winner.health / self.winner.max_health))
            bar_w, bar_h = 360, 14
            bar_x = right_center_x - bar_w // 2
            bar_y = card_y + 160
            pygame.draw.rect(self.screen, (40, 30, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            pygame.draw.rect(self.screen, (0, 255, 150), (bar_x, bar_y, int(bar_w * hp_ratio), bar_h), border_radius=4)
            pygame.draw.rect(self.screen, (255, 255, 255, 100), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
            
            # 2. 绘制最高连击数 (Max Combo Score)
            if lang == 'en_US':
                combo_text = f"MAX COMBO: {self.winner.max_combo} HITS (+{combo_score} PTS)"
            else:
                combo_text = f"最高连击数: {self.winner.max_combo} HITS (+{combo_score}分)"
            
            # 连击高亮亮橙色
            combo_surf = font_small.render(combo_text, True, (255, 140, 0))
            combo_x = right_center_x - combo_surf.get_width() // 2
            combo_y = card_y + 195
            self.screen.blit(combo_surf, (combo_x, combo_y))
            
            # 3. 绘制 Perfect 奖励与最终得分
            if is_perfect:
                # 闪烁的 Perfect 文字效果
                perf_brightness = int(180 + 75 * math.sin(pygame.time.get_ticks() / 150))
                perf_color = (255, perf_brightness, 50) # 呼吸亮黄/霓虹粉
                perf_text = "PERFECT VICTORY (+5000 PTS)" if lang == 'en_US' else "无伤完美通关奖励 (+5000分)!"
                perf_surf = font_small.render(perf_text, True, perf_color)
                perf_x = right_center_x - perf_surf.get_width() // 2
                perf_y = card_y + 235
                self.screen.blit(perf_surf, (perf_x, perf_y))
                
                score_y = card_y + 275
            else:
                score_y = card_y + 250
                
            # 最终得分 (大号炫目金色数字)
            score_text = f"SCORE: {total_score}" if lang == 'en_US' else f"最终得分: {total_score}"
            score_surf = font_medium.render(score_text, True, (255, 215, 0)) # 纯金色
            score_shadow = font_medium.render(score_text, True, (0, 0, 0))
            
            score_x = right_center_x - score_surf.get_width() // 2
            self.screen.blit(score_shadow, (score_x + 2, score_y + 2))
            self.screen.blit(score_surf, (score_x, score_y))

        # 5. 呼吸灯式底部按键返回提示 (Pulsing Return Hint with custom self-drawn keycaps)
        brightness = int(140 + 115 * math.sin(pygame.time.get_ticks() / 250))
        text_color = (brightness, brightness, brightness)
        
        # 获取确定键物理符号
        confirm_btn_symbol = "确定键"
        if self.winner:
            ctrl = self.winner.device_info['controller']
            from src.core.input import KeyBoard, Joystick
            if isinstance(ctrl, KeyBoard):
                confirm_btn_symbol = "⏎"
            elif isinstance(ctrl, Joystick):
                from src.core.input_config import UI_MAPPING
                ui_map = UI_MAPPING.get(ctrl.type, UI_MAPPING['xbox'])
                btn_name = ui_map.get('confirm', 'A')
                confirm_btn_symbol = btn_name.upper()
        else:
            confirm_btn_symbol = "⏎"
            
        if lang == 'en_US':
            prefix_text = "PRESS "
            suffix_text = " TO RETURN"
        else:
            prefix_text = "按下 "
            suffix_text = " 返回主页"
            
        # 渲染文本段，计算整体尺寸以便在右半侧完美水平居中
        prefix_surf = font_small.render(prefix_text, True, text_color)
        suffix_surf = font_small.render(suffix_text, True, text_color)
        
        # 根据按键类型微调键帽的宽度与绘制尺寸
        key_w = 40 if confirm_btn_symbol == "⏎" else 26
        key_h = 24
        
        # 总宽度 = 前缀宽 + 间距(6) + 键帽宽 + 间距(6) + 后缀宽
        total_w = prefix_surf.get_width() + 6 + key_w + 6 + suffix_surf.get_width()
        
        # 居中起始 x 坐标
        start_x = right_center_x - total_w // 2
        draw_y = card_y + 360
        
        # 1. 绘制前缀文本
        self.screen.blit(prefix_surf, (start_x, draw_y))
        
        # 2. 绘制自绘高亮按键键帽 (Tactile 3D Keycap Box)
        key_x = start_x + prefix_surf.get_width() + 6
        key_y = draw_y - 2 # 垂直微调对齐文本
        
        key_rect = pygame.Rect(key_x, key_y, key_w, key_h)
        # 绘制深灰按键底槽与动感呼吸发光描边
        pygame.draw.rect(self.screen, (40, 40, 40), key_rect, border_radius=5)
        pygame.draw.rect(self.screen, text_color, key_rect, 1, border_radius=5)
        
        # 3. 绘制按键内部符号
        if confirm_btn_symbol == "⏎":
            # 采用与主菜单自绘图标一致的高性能折线回车箭头
            cy = key_y + key_h // 2
            pygame.draw.lines(self.screen, text_color, False, [(key_x + 24, cy - 5), (key_x + 24, cy + 3), (key_x + 14, cy + 3)], 2)
            pygame.draw.lines(self.screen, text_color, False, [(key_x + 18, cy), (key_x + 13, cy + 3), (key_x + 18, cy + 6)], 2)
        else:
            # 绘制手柄物理按键字母 (如 A / X)
            btn_font = pygame.font.Font(resource_path('assets/font/impact.ttf'), 16)
            btn_surf = btn_font.render(confirm_btn_symbol, True, text_color)
            btn_rect = btn_surf.get_rect(center=key_rect.center)
            self.screen.blit(btn_surf, btn_rect)
            
        # 4. 绘制后缀文本
        suffix_x = key_x + key_w + 6
        self.screen.blit(suffix_surf, (suffix_x, draw_y))

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
            
            # 限制玩家不能超出当前摄像机视野边界 (保证所有人物都在画面中，彻底零帧空气墙拦截)
            if not self.dialogue.showing and not self.show_results:
                from src.settings import SCREEN_WIDTH
                margin = 60  # 加上半身宽度，保证整个身体在画面内
                left_limit = self.camera_offset.x + margin
                right_limit = self.camera_offset.x + SCREEN_WIDTH - margin
                if player.pos.x < left_limit:
                    player.pos.x = left_limit
                    player.rect.midbottom = player.pos
                elif player.pos.x > right_limit:
                    player.pos.x = right_limit
                    player.rect.midbottom = player.pos
            
            # 绘制角色的冲刺/大招残影特效 (Ghost Trails)
            for ghost in player.ghosts:
                ghost_img = ghost['image'].copy()
                ghost_img.set_alpha(int(ghost['alpha']))
                
                # 渲染残影 (应用摄像机偏移)
                ghost_offset_pos = pygame.math.Vector2(ghost['pos']) - self.camera_offset
                self.screen.blit(ghost_img, ghost_offset_pos)

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

        # 4. 最上层：UI (血条与连击数)
        from src.settings import SCREEN_WIDTH
        for player in players:
            player.blood_ui.display(player.health, player.shadow_health, player.max_health)
            
            # 绘制连击次数 (Combo Counter Display)
            if player.combo_count > 1:
                from src.core.support import resource_path
                path = resource_path('assets/font/impact.ttf')
                font = pygame.font.Font(path, 32)
                
                combo_str = f"{player.combo_count} HITS"
                shadow_surf = font.render(combo_str, True, (0, 0, 0))
                text_surf = font.render(combo_str, True, (255, 120, 0))  # 亮橙色
                
                # 动态计算位置以实现完美的对称血槽对齐
                if player.device_info['player_index'] == 'p1':
                    text_x = 95
                else:
                    text_x = SCREEN_WIDTH - 95 - text_surf.get_width()
                    
                text_y = 62
                self.screen.blit(shadow_surf, (text_x + 2, text_y + 2))
                self.screen.blit(text_surf, (text_x, text_y))

        # 绘制中央格斗 VS 徽章 (VS Badge in the center gap)
        from src.core.support import resource_path
        path = resource_path('assets/font/impact.ttf')
        vs_font = pygame.font.Font(path, 36)
        vs_shadow = vs_font.render("VS", True, (0, 0, 0))
        vs_text = vs_font.render("VS", True, (255, 200, 40)) # 亮金色
        
        vs_x = SCREEN_WIDTH // 2 - vs_text.get_width() // 2
        vs_y = 22
        self.screen.blit(vs_shadow, (vs_x + 2, vs_y + 2))
        self.screen.blit(vs_text, (vs_x, vs_y))
            
        # 5. 结算界面
        if self.show_results:
            self.draw_settlement()
            # 仅限制胜利者按确定键退出 (Only the winner can trigger the return to home screen via confirm key)
            if self.winner:
                winner_ctrl = self.winner.device_info['controller']
                if winner_ctrl.ui_performed('confirm'):
                    self.game_input.home_menu_index = 0
                    return SceneStatus.HOME
            else:
                # 备用退出逻辑 (如 Draw 无胜利者，则任何已加入玩家皆可按确定键退出)
                for device_info in self.game_input.controllers.values():
                    if device_info['player_index'] != 'p0':
                        if device_info['controller'].ui_performed('confirm'):
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
