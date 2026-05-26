import pygame as pg
import random
import sys
import os
import math

# -----------------------------
# 実行ディレクトリを自動修正
# -----------------------------
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("Fixed directory:", os.getcwd())

# -----------------------------
# 初期設定
# -----------------------------
pg.init()
WIDTH, HEIGHT = 800, 600
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Gradius-like Shooter")
main_clock = pg.time.Clock()

# -----------------------------
# BGM 再生（完全版）
# -----------------------------
pg.mixer.init()
try:
    pg.mixer.music.load("BGM/senntou.wav")   # BGM
    pg.mixer.music.set_volume(0.6)        # 音量
    pg.mixer.music.play(-1)               # ループ再生
    print("[OK] BGM loaded")
except Exception as e:
    print("[ERROR] BGM load failed:", e)

# -----------------------------
# 安全な読み込み関数（画像・音声）
# -----------------------------
def load_image_safe(path):
    if not os.path.exists(path):
        print(f"[ERROR] File not found: {path}")
        surf = pg.Surface((30, 20))
        surf.fill((255, 80, 80))
        return surf

    try:
        img = pg.image.load(path)
        print(f"[OK] Loaded image: {path}")
        return img
    except Exception as e:
        print(f"[ERROR] Cannot load image: {path}")
        print("Reason:", e)
        surf = pg.Surface((30, 20))
        surf.fill((255, 80, 80))
        return surf

# コード1から追加：安全な音声読み込み関数
def load_sound_safe(path):
    if not os.path.exists(path):
        print(f"[ERROR] Sound file not found: {path}")
        return None

    try:
        sound = pg.mixer.Sound(path)
        print(f"[OK] Loaded sound: {path}")
        return sound
    except Exception as e:
        print(f"[ERROR] Cannot load sound: {path}")
        print("Reason:", e)
        return None

# -----------------------------
# Score（スコア表示）
# -----------------------------
class Score:
    def __init__(self):
        self.value = 0
        self.font = pg.font.Font(None, 36)

    def add(self, amount):
        self.value += amount

    def draw(self, surface):
        txt = self.font.render(f"Score: {self.value}", True, (255, 255, 255))
        surface.blit(txt, (10, 10))

# -----------------------------
# Player（画像3種：通常・上・下）
# -----------------------------
class Player(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # 画像読み込み
        self.img_normal = load_image_safe("fig/gura2.png")
        self.img_up     = load_image_safe("fig/gura3.png")
        self.img_down   = load_image_safe("fig/gura4.png")

        # 自動縮小（40%）
        def scale(img):
            w, h = img.get_size()
            return pg.transform.smoothscale(img, (int(w*0.4), int(h*0.4)))

        self.img_normal = scale(self.img_normal)
        self.img_up     = scale(self.img_up)
        self.img_down   = scale(self.img_down)

        # 初期画像
        self.image = self.img_normal
        self.rect = self.image.get_rect()
        self.rect.center = (100, HEIGHT // 2)

        self.speed = 5
        self.dy = 0  # 上下移動の状態

        self.shield = False  # シールド状態
        self.shield_stock = 3  # シールドストック（残り数）を追加

    def update(self):
        keys = pg.key.get_pressed()
        self.dy = 0

        if keys[pg.K_UP]:
            self.rect.y -= self.speed
            self.dy = -1
        if keys[pg.K_DOWN]:
            self.rect.y += self.speed
            self.dy = 1
        if keys[pg.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pg.K_RIGHT]:
            self.rect.x += self.speed

        # 状態に応じて画像切り替え
        if self.dy < 0:
            self.image = self.img_up
        elif self.dy > 0:
            self.image = self.img_down
        else:
            self.image = self.img_normal

        self.rect.clamp_ip(screen.get_rect())

    def draw_shield(self, surface):
        font = pg.font.Font(None, 30)
        txt = font.render(f"Shield: {self.shield_stock}",True,(0, 255, 255))
        surface.blit(txt, (10, 50))

        if self.shield:
            pg.draw.circle(surface,(0, 255, 255),self.rect.center,40,3) # シールド描画追加

# -----------------------------
# Bullet
# -----------------------------
class Bullet(pg.sprite.Sprite):
    def __init__(self, x, y, speed = 10):
        super().__init__()
        self.image = pg.Surface((10, 4))
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed

    def update(self):
        self.rect.x += self.speed
        if self.rect.x > WIDTH:
            self.kill()

# =========================================================
# Laser（貫通レーザー）
# =========================================================
class Laser(pg.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # レーザー画像
        self.image = pg.Surface((120, 12))
        self.image.fill((0, 255, 255))
        self.rect = self.image.get_rect(midleft=(x, y))
        self.speed = 18

    def update(self):
        self.rect.x += self.speed
        if self.rect.left > WIDTH:
            self.kill()

# -----------------------------
# Enemy（画像読み込み＋自動縮小）
# -----------------------------
class Enemy(pg.sprite.Sprite):
    def __init__(self, stage=1):  # ★ 変更：stage引数を追加
        super().__init__()
        # 画像読み込み
        self.image = load_image_safe("fig/enemy.png")

        # 自動縮小（40%）※コード2の設定を優先
        w, h = self.image.get_size()
        self.image = pg.transform.smoothscale(self.image, (int(w*0.1), int(h*0.1)))

        try:
            self.image = self.image.convert_alpha()
        except:
            pass

        self.rect = self.image.get_rect()
        self.rect.x = WIDTH + random.randint(0, 200)
        self.rect.y = random.randint(20, HEIGHT - 20)
        base = 3 + (stage - 1)                       # ★ 変更：ステージ毎に速度UP
        self.speed = random.randint(base, base + 3)  # ★ 変更：元は randint(4, 6)

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

class ChaserEnemy(pg.sprite.Sprite):
    def __init__(self, stage=1):  # ★ 変更：stage引数を追加
        """
        追従型敵（Playerの上下に追従して移動）
        """
        super().__init__()
        self.image = load_image_safe("fig/enemy.png")
        w, h = self.image.get_size()
        self.image = pg.transform.smoothscale(self.image, (int(w*0.1), int(h*0.1)))
        try:
            self.image = self.image.convert_alpha()
        except:
            pass
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH + random.randint(0, 200)
        self.rect.y = random.randint(20, HEIGHT - 20)
        self.speed_x = 4 + (stage - 1)  # ★ ステージ毎に速度UP
        self.speed_y = 1

    def update(self, player_rect: pg.Rect):
        if player_rect.centery < self.rect.centery: # Playerが上にいる → 敵は上に移動
            self.rect.y -= self.speed_y
        elif player_rect.centery > self.rect.centery:   # Playerが下にいる → 敵は下に移動
            self.rect.y += self.speed_y
        self.rect.x -= self.speed_x
        if self.rect.right < 0:
            self.kill()

class WavyEnemy(pg.sprite.Sprite):
    def __init__(self, stage=1):  # ★ 変更：stage引数を追加
        """
        うねうねする敵
        """
        super().__init__()
        self.image = load_image_safe("fig/enemy.png")
        w, h = self.image.get_size()
        self.image = pg.transform.smoothscale(self.image, (int(w*0.1), int(h*0.1)))
        try:
            self.image = self.image.convert_alpha()
        except:
            pass
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH + random.randint(0, 200)
        self.rect.y = random.randint(20, HEIGHT - 20)
        self.base_y = self.rect.y
        self.speed = 4 + (stage - 1)  # ★ ステージ毎に速度UP
        self.angle = 0
        self.wave_speed = 0.1
        self.wave_amp = 50

    def update(self):
        self.rect.x -= self.speed
        self.angle += self.wave_speed
        self.rect.y = self.base_y + math.sin(self.angle) * self.wave_amp
        if self.rect.right < 0:
            self.kill()

# ═══════════════════════════════════════════════════════════════
# ▼▼▼ 追加機能：ボス戦  ここから ▼▼▼
#   ・EnemyBullet : ボスが撃つ弾
#   ・Boss        : HP制ボス本体（ステージごとに難易度UP）
# ═══════════════════════════════════════════════════════════════
class EnemyBullet(pg.sprite.Sprite):
    def __init__(self, x, y, speed=7):
        super().__init__()
        self.image = pg.Surface((12, 6))
        self.image.fill((255, 80, 80))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

class Boss(pg.sprite.Sprite):
    BASE_HP = 30
    HP_PER_STAGE = 8

    def __init__(self, bullet_group, stage=1):
        super().__init__()
        img = load_image_safe("fig/boss.png")
        w, h = img.get_size()
        target_h = 240
        s = target_h / h if h else 1
        self.image = pg.transform.smoothscale(img, (max(1, int(w * s)), max(1, int(h * s))))
        try:
            self.image = self.image.convert_alpha()
        except Exception:
            pass

        self.rect = self.image.get_rect()
        self.target_x = WIDTH - 40 - self.rect.width
        self.rect.x = WIDTH + 10
        self.rect.centery = HEIGHT // 2

        self.stage = stage
        self.max_hp = Boss.BASE_HP + (stage - 1) * Boss.HP_PER_STAGE
        self.hp = self.max_hp
        self.dy = 2 + (stage - 1)
        self.bullet_speed = 7 + (stage - 1)
        self.shoot_interval = max(15, 50 - (stage - 1) * 5)
        self.shoot_timer = 0
        self.entering = True
        self.bullet_group = bullet_group

    def update(self):
        if self.entering:
            if self.rect.x > self.target_x:
                self.rect.x -= 4
                return
            self.rect.x = self.target_x
            self.entering = False
            return

        self.rect.y += self.dy
        if self.rect.top <= 40:
            self.rect.top = 40
            self.dy = abs(self.dy)
        elif self.rect.bottom >= HEIGHT - 10:
            self.rect.bottom = HEIGHT - 10
            self.dy = -abs(self.dy)

        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            self.bullet_group.add(
                EnemyBullet(self.rect.left, self.rect.centery, speed=self.bullet_speed)
            )

    def hit(self, damage=1):
        self.hp -= damage
        return self.hp <= 0
# ═══════════════════════════════════════════════════════════════
# ▲▲▲ 追加機能：ボス戦  ここまで（EnemyBullet / Boss クラス） ▲▲▲
# ═══════════════════════════════════════════════════════════════

# -----------------------------
# PowerUp（パワーアップアイテム）
# -----------------------------
class PowerUp(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pg.Surface((20, 20))
        self.image.fill((0, 255, 255))  # 水色のアイテム
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH + random.randint(0, 200)
        self.rect.y = random.randint(50, HEIGHT - 50)
        self.speed = 3

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

class PowerUp3Way(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pg.Surface((20, 20))
        self.image.fill((255, 100, 0))  # オレンジ色のアイテム
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH + random.randint(0, 200)
        self.rect.y = random.randint(50, HEIGHT - 50)
        self.speed = 3

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

# -----------------------------
# Background scroll
# -----------------------------
bg = pg.Surface((WIDTH, HEIGHT))
bg.fill((10, 10, 30))
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(80)]

def draw_background(scroll_x):
    screen.blit(bg, (0, 0))
    for x, y in stars:
        pg.draw.circle(screen, (200, 200, 255), ((x - scroll_x) % WIDTH, y), 2)

# -----------------------------
# アセットの読み込み（天国画像＆ゲームオーバーSE）※コード1から追加
# -----------------------------
heaven_raw = load_image_safe("fig/heaven.png")
heaven_img = pg.transform.smoothscale(heaven_raw, (WIDTH, HEIGHT))
gameover_se = load_sound_safe("BGM/heaven.wav")

fade_surface = pg.Surface((WIDTH, HEIGHT))
fade_surface.fill((255, 255, 255))
fade_timer = 0
heaven_timer = 0

# ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼（難易度スケーリング関数）
def kill_quota(s):
    """ステージsでボスが出現するために必要なザコ撃破数"""
    return 5 + (s - 1) * 2


def spawn_interval(s):
    """ステージsのザコスポーン間隔（フレーム）"""
    return max(12, 40 - (s - 1) * 4)
# ▲▲▲ 追加機能：ボス戦 ここまで ▲▲▲

# -----------------------------
# Main Game Loop
# -----------------------------
player = Player()
player_group = pg.sprite.Group(player)
bullet_group = pg.sprite.Group()
enemy_group = pg.sprite.Group()
chaser_enemy_group = pg.sprite.Group()    # 追従型敵グループ
wavy_enemy_group = pg.sprite.Group()    # うねうね敵グループ
laser_group = pg.sprite.Group()  # レーザーグループ追加
powerup_group = pg.sprite.Group()
threeway_group = pg.sprite.Group()
# ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼（スプライトグループ）
enemy_bullet_group = pg.sprite.Group()   # ★ ボスの弾を入れる新グループ
boss_group = pg.sprite.Group()           # ★ ボス本体を入れる新グループ
# ▲▲▲ 追加機能：ボス戦 ここまで ▲▲▲

score = Score()

enemy_spawn_timer = 0
scroll_x = 0

# コード1の状態管理を復活
game_state = "playing"
font = pg.font.Font(None, 80)
font_small = pg.font.Font(None, 40)
# ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼（フォント）
boss_label_font = pg.font.Font(None, 24)  # ★ HPバー上のラベル用
stage_font = pg.font.Font(None, 36)       # ★ STAGE表示用
# ▲▲▲ 追加機能：ボス戦 ここまで ▲▲▲

powerup_timer = 0
powerup_active = False
powerup_end_time = 0
threeway_timer = 0
threeway_active = False
threeway_end_time = 0

# 連射間隔
shot_interval = 15
shot_timer = 0
laser_cooldown = 0

# ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼（ゲーム状態フラグ／タイマー）
boss = None                               # ★ 現ボス参照（出てなければNone）
stage = 1                                 # ★ 現在のステージ番号
stage_kills = 0                           # ★ 現ステージで倒したザコ数
clear_timer = 0                           # ★ クリア演出残フレーム（>0で演出中）
CLEAR_FRAMES = 150                        # ★ クリア演出の長さ（2.5秒）
# ▲▲▲ 追加機能：ボス戦 ここまで ▲▲▲

while True:
    for ev in pg.event.get():
        if ev.type == pg.QUIT:
            pg.quit()
            sys.exit()

        if ev.type == pg.KEYDOWN:
            # プレイ中のキー操作
            if game_state == "playing":
                if ev.key == pg.K_SPACE:
                    if shot_timer <= 0:
                        bullet_speed = 10
                        if threeway_active:
                            bullet_group.add(Bullet(player.rect.right, player.rect.centery, bullet_speed))
                            bullet_group.add(Bullet(player.rect.right, player.rect.centery - 15, bullet_speed))
                            bullet_group.add(Bullet(player.rect.right, player.rect.centery + 15, bullet_speed))
                        else:
                            bullet_group.add(Bullet(player.rect.right, player.rect.centery, bullet_speed))
                        shot_timer = shot_interval

                elif ev.key == pg.K_x and laser_cooldown <= 0:
                    laser_group.add(Laser(player.rect.right, player.rect.centery))
                    laser_cooldown = 60

                if ev.key == pg.K_s:
                    if player.shield_stock > 0 and not player.shield:
                        player.shield = True
                        player.shield_stock -= 1

            # ゲームオーバー中のエンターキー（コンティニュー）※コード1から追加
            elif game_state == "gameover":
                if ev.key == pg.K_RETURN:  # Enterキー
                    if gameover_se:
                        gameover_se.stop()

                    # BGM再開
                    try:
                        pg.mixer.music.play(-1)
                    except:
                        pass

                    # ゲーム状態をリセット
                    game_state = "playing"
                    score.value = 0
                    scroll_x = 0
                    enemy_spawn_timer = 0
                    player.rect.center = (100, HEIGHT // 2)
                    player.shield = False
                    player.shield_stock = 3

                    # 画面上のエンティティを消去
                    enemy_group.empty()
                    chaser_enemy_group.empty()
                    wavy_enemy_group.empty()
                    bullet_group.empty()
                    laser_group.empty()
                    powerup_group.empty()
                    threeway_group.empty()
                    # ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼（リセット）
                    enemy_bullet_group.empty()
                    boss_group.empty()
                    boss = None
                    stage = 1
                    stage_kills = 0
                    clear_timer = 0
                    # ▲▲▲ 追加機能：ボス戦 ここまで ▲▲▲

                    powerup_active = False
                    threeway_active = False
                    shot_interval = 15

    # --- 更新処理 ---
    if game_state == "playing":
        scroll_x += 3

        if laser_cooldown > 0:
            laser_cooldown -= 1
        if shot_timer > 0:
            shot_timer -= 1

        # ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼（ステージ進行）
        # クリア演出のカウントダウン（終了で次ステージへ）
        if clear_timer > 0:
            clear_timer -= 1
            if clear_timer == 0:
                stage += 1
                stage_kills = 0
                enemy_group.empty()
                chaser_enemy_group.empty()
                wavy_enemy_group.empty()
                enemy_bullet_group.empty()
                enemy_spawn_timer = 0

        # ボス出現判定（ザコをノルマ分倒したら登場）
        if boss is None and clear_timer == 0 and stage_kills >= kill_quota(stage):
            enemy_group.empty()
            chaser_enemy_group.empty()
            wavy_enemy_group.empty()
            boss = Boss(enemy_bullet_group, stage=stage)
            boss_group.add(boss)
        # ▲▲▲ 追加機能：ボス戦 ここまで ▲▲▲

        # 敵の出現（★ボス/演出中/ノルマ達成時はスポーン停止）
        if boss is None and clear_timer == 0 and stage_kills < kill_quota(stage):
            enemy_spawn_timer += 1
            if enemy_spawn_timer > spawn_interval(stage):  # ★ ステージ毎にスポーン間隔短縮
                spawn_chance = random.random()
                if spawn_chance < 0.6:
                    enemy_group.add(Enemy(stage=stage))
                elif spawn_chance < 0.8:
                    chaser_enemy_group.add(ChaserEnemy(stage=stage))
                else:
                    wavy_enemy_group.add(WavyEnemy(stage=stage))
                enemy_spawn_timer = 0

        # パワーアップアイテムの出現
        powerup_timer += 1
        if powerup_timer > 300:
            powerup_group.add(PowerUp())
            powerup_timer = 0

        threeway_timer += 1
        if threeway_timer > 500:
            threeway_group.add(PowerUp3Way())
            threeway_timer = 0

        # グループの更新
        player_group.update()
        bullet_group.update()
        laser_group.update()
        enemy_group.update()
        chaser_enemy_group.update(player.rect)
        wavy_enemy_group.update()
        powerup_group.update()
        threeway_group.update()
        enemy_bullet_group.update()  # ★ 追加：敵弾の更新
        boss_group.update()          # ★ 追加：ボスの更新

        # パワーアップ取得処理
        if pg.sprite.spritecollide(player, powerup_group, True):
            powerup_active = True
            shot_interval = 1
            powerup_end_time = pg.time.get_ticks() + 8000

        if pg.sprite.spritecollide(player, threeway_group, True):
            threeway_active = True
            threeway_end_time = pg.time.get_ticks() + 8000

        # パワーアップ終了処理
        if powerup_active and pg.time.get_ticks() > powerup_end_time:
            powerup_active = False
            shot_interval = 15
        if threeway_active and pg.time.get_ticks() > threeway_end_time:
            threeway_active = False

        # --- 当たり判定（プレイヤー VS 敵）---
        # 関数にまとめて処理
        def handle_player_hit():
            global game_state, fade_timer
            if player.shield:
                player.shield = False
            else:
                game_state = "fading"
                fade_timer = 0
                pg.mixer.music.stop() # BGM停止

        if pg.sprite.spritecollide(player, enemy_group, True):
            handle_player_hit()
        if pg.sprite.spritecollide(player, chaser_enemy_group, True):
            handle_player_hit()
        if pg.sprite.spritecollide(player, wavy_enemy_group, True):
            handle_player_hit()
        # ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼（プレイヤー被弾）
        if pg.sprite.spritecollide(player, enemy_bullet_group, True):
            handle_player_hit()
        if boss is not None and not boss.entering:
            if pg.sprite.spritecollide(player, boss_group, False):
                handle_player_hit()
        # ▲▲▲ 追加機能：ボス戦 ここまで ▲▲▲

        # --- 当たり判定（攻撃 VS 敵）---
        hits = pg.sprite.groupcollide(bullet_group, enemy_group, True, True)
        if hits:
            killed = sum(len(v) for v in hits.values())
            score.add(100 * killed)
            stage_kills += killed  # ★ ボス戦：ノルマカウント
        hits2 = pg.sprite.groupcollide(bullet_group, chaser_enemy_group, True, True)
        if hits2:
            killed2 = sum(len(v) for v in hits2.values())
            score.add(50 * killed2)
            stage_kills += killed2  # ★ ボス戦：ノルマカウント
        hits3 = pg.sprite.groupcollide(bullet_group, wavy_enemy_group, True, True)
        if hits3:
            killed3 = sum(len(v) for v in hits3.values())
            score.add(150 * killed3)
            stage_kills += killed3  # ★ ボス戦：ノルマカウント

        laser_hits = pg.sprite.groupcollide(laser_group, enemy_group, False, True)
        if laser_hits:
            killed_l = sum(len(v) for v in laser_hits.values())
            score.add(100 * killed_l)
            stage_kills += killed_l  # ★ ボス戦：ノルマカウント
        laser_hits2 = pg.sprite.groupcollide(laser_group, chaser_enemy_group, False, True)
        if laser_hits2:
            killed_l2 = sum(len(v) for v in laser_hits2.values())
            score.add(50 * killed_l2)
            stage_kills += killed_l2  # ★ ボス戦：ノルマカウント
        laser_hits3 = pg.sprite.groupcollide(laser_group, wavy_enemy_group, False, True)
        if laser_hits3:
            killed_l3 = sum(len(v) for v in laser_hits3.values())
            score.add(150 * killed_l3)
            stage_kills += killed_l3  # ★ ボス戦：ノルマカウント

        # ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼（自弾/レーザー → ボス）
        if boss is not None:
            # 通常弾：1発1ダメージ・弾消滅
            boss_hits = pg.sprite.groupcollide(bullet_group, boss_group, True, False)
            for _bullet, hit_bosses in boss_hits.items():
                for b in hit_bosses:
                    if b.hit():
                        b.kill()
                        score.add(1000 * stage)
                        boss = None
                        enemy_bullet_group.empty()  # 残弾も掃除
                        clear_timer = CLEAR_FRAMES   # クリア演出開始
                    else:
                        score.add(50)
            # レーザー：当たったらレーザー消滅・3ダメージ（強武器扱い）
            if boss is not None:
                laser_boss_hits = pg.sprite.groupcollide(laser_group, boss_group, True, False)
                for _laser, hit_bosses in laser_boss_hits.items():
                    for b in hit_bosses:
                        if b.hit(3):
                            b.kill()
                            score.add(1000 * stage)
                            boss = None
                            enemy_bullet_group.empty()
                            clear_timer = CLEAR_FRAMES
                        else:
                            score.add(150)
        # ▲▲▲ 追加機能：ボス戦 ここまで ▲▲▲

    # --- 描画処理 ---
    if game_state in ["playing", "fading"]:
        draw_background(scroll_x)
        player_group.draw(screen)
        player.draw_shield(screen)
        bullet_group.draw(screen)
        laser_group.draw(screen)
        enemy_group.draw(screen)
        chaser_enemy_group.draw(screen)
        wavy_enemy_group.draw(screen)
        powerup_group.draw(screen)
        threeway_group.draw(screen)
        enemy_bullet_group.draw(screen)  # ★ ボス弾の描画
        boss_group.draw(screen)           # ★ ボスの描画
        score.draw(screen)

        # ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼（STAGE表示・進捗・HPバー）
        stage_txt = stage_font.render(f"STAGE {stage}", True, (255, 255, 255))
        screen.blit(stage_txt, (WIDTH - stage_txt.get_width() - 10, 10))
        if boss is None and clear_timer == 0:
            prog = boss_label_font.render(
                f"KILLS {min(stage_kills, kill_quota(stage))}/{kill_quota(stage)}",
                True, (255, 220, 100)
            )
            screen.blit(prog, (WIDTH - prog.get_width() - 10, 44))

        if boss is not None and boss.alive() and not boss.entering:
            bar_w, bar_h = 320, 14
            bar_x = WIDTH // 2 - bar_w // 2
            bar_y = 50
            ratio = max(0.0, boss.hp / boss.max_hp)
            pg.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
            pg.draw.rect(screen, (255, 60, 60), (bar_x, bar_y, int(bar_w * ratio), bar_h))
            pg.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2)
            label = boss_label_font.render(f"BOSS  STAGE {boss.stage}", True, (255, 255, 255))
            screen.blit(label, (bar_x, bar_y - 22))

        if clear_timer > 0:
            clear_txt = font.render(f"STAGE {stage} CLEAR!", True, (255, 220, 0))
            screen.blit(clear_txt, (WIDTH // 2 - clear_txt.get_width() // 2, HEIGHT // 2 - 60))
            if clear_timer < CLEAR_FRAMES // 2:
                nxt = stage_font.render(f"NEXT: STAGE {stage + 1}", True, (255, 255, 255))
                screen.blit(nxt, (WIDTH // 2 - nxt.get_width() // 2, HEIGHT // 2 + 20))
        # ▲▲▲ 追加機能：ボス戦 ここまで ▲▲▲

    # --- ゲームオーバー演出（コード1より復活） ---
    if game_state == "fading":
        fade_timer += 1
        alpha = int(255 * (fade_timer / 120))
        if alpha >= 255:
            alpha = 255
            game_state = "heaven"
            heaven_timer = 0

            # 天国の画面に切り替わった瞬間にSEを再生
            if gameover_se:
                gameover_se.play()

        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))

    elif game_state == "heaven":
        screen.blit(heaven_img, (0, 0))
        heaven_timer += 1
        if heaven_timer >= 120:
            game_state = "gameover"

    elif game_state == "gameover":
        screen.blit(heaven_img, (0, 0))
        txt = font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(txt, (WIDTH // 2 - 180, HEIGHT // 2 - 60))

        txt_continue = font_small.render("Press ENTER to Continue", True, (0, 0, 0))
        screen.blit(txt_continue, (WIDTH // 2 - 170, HEIGHT // 2 + 20))

    pg.display.update()
    main_clock.tick(60)
