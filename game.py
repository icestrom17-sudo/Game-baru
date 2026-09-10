cat > game.py << 'PYEOF'
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line, Triangle
from kivy.core.window import Window
import random
import math


class DarkKnightGame(Widget):

    # =========================================================
    # KONSTANTA
    # =========================================================
    GRAVITY = 1900
    MOVE_SPEED = 320
    JUMP_POWER = 720
    DASH_SPEED = 1150
    DASH_TIME = 0.16
    DASH_COOLDOWN = 0.7
    ATTACK_COOLDOWN = 0.28
    INVULN_TIME = 1.0
    LEVEL_WIDTH = 2600
    FLOOR_Y = 80

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # =========================
        # PLAYER
        # =========================
        self.player_x = 120
        self.player_y = self.FLOOR_Y
        self.player_vx = 0
        self.player_vy = 0
        self.facing = 1
        self.is_grounded = True
        self.player_hp = 100
        self.player_max_hp = 100
        self.invuln_timer = 0
        self.game_over = False

        self.move_left = False
        self.move_right = False

        self.state = "idle"
        self.anim_timer = 0

        # Dash
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.trail = []

        # Attack
        self.attack_cooldown = 0
        self.attack_anim = 0
        self.player_attacks = []

        # Kamera
        self.camera_x = 0

        # Platform untuk eksplorasi
        self.platforms = [
            {"x": 350, "y": 220, "w": 180, "h": 24},
            {"x": 620, "y": 340, "w": 160, "h": 24},
            {"x": 900, "y": 200, "w": 200, "h": 24},
            {"x": 1200, "y": 300, "w": 160, "h": 24},
            {"x": 1450, "y": 420, "w": 180, "h": 24},
            {"x": 1750, "y": 260, "w": 200, "h": 24},
            {"x": 2050, "y": 380, "w": 160, "h": 24},
        ]

        # Orb HP di beberapa platform
        self.pickups = [
            {"x": 430, "y": 264, "taken": False},
            {"x": 950, "y": 244, "taken": False},
            {"x": 1780, "y": 304, "taken": False},
        ]

        # Bintang parallax
        self.stars = [
            (random.uniform(0, self.LEVEL_WIDTH), random.uniform(300, 900),
             random.uniform(0.15, 0.5), random.uniform(2, 4))
            for _ in range(70)
        ]

        # =========================
        # BOSS
        # =========================
        self.boss_home_x = self.LEVEL_WIDTH - 260
        self.boss_x = self.boss_home_x
        self.boss_y = self.FLOOR_Y
        self.boss_hp = 300
        self.boss_max_hp = 300
        self.boss_bullets = []
        self.boss_hazards = []
        self.boss_state = "cooldown"
        self.boss_timer = 1.2
        self.boss_glow = 0
        self.boss_flash = 0
        self.boss_facing = -1
        self.boss_dash_vx = 0
        self.current_attack = None
        self.pending_slam_x = 0
        self.victory = False

        # Label status (YOU DIED / BOSS DEFEATED)
        self.status_label = Label(
            text="", font_size=40, bold=True,
            size_hint=(None, None), size=(500, 90), opacity=0
        )
        self.add_widget(self.status_label)

        self.create_controls()

        Window.bind(on_key_down=self._on_key_down)
        Window.bind(on_key_up=self._on_key_up)

        Clock.schedule_interval(self.update, 1 / 60)

    # =========================================================
    # TOUCH CONTROLS
    # =========================================================
    def create_controls(self):
        self.left_button = self._make_button("<", 90, 90, 32)
        self.right_button = self._make_button(">", 90, 90, 32)
        self.jump_button = self._make_button("JUMP", 120, 90, 18)
        self.attack_button = self._make_button("ATTACK", 130, 90, 16)
        self.dash_button = self._make_button("DASH", 120, 90, 18)

        for b in (self.left_button, self.right_button, self.jump_button,
                  self.attack_button, self.dash_button):
            self.add_widget(b)

        self.left_button.bind(on_press=lambda *_: self.set_left(True))
        self.left_button.bind(on_release=lambda *_: self.set_left(False))
        self.right_button.bind(on_press=lambda *_: self.set_right(True))
        self.right_button.bind(on_release=lambda *_: self.set_right(False))
        self.jump_button.bind(on_press=lambda *_: self.jump())
        self.attack_button.bind(on_press=lambda *_: self.attack())
        self.dash_button.bind(on_press=lambda *_: self.dash())

    def _make_button(self, text, w, h, fs):
        return Button(text=text, font_size=fs, size_hint=(None, None),
                       size=(w, h), opacity=0.75)

    def set_left(self, value):
        self.move_left = value
        if value:
            self.facing = -1

    def set_right(self, value):
        self.move_right = value
        if value:
            self.facing = 1

    # =========================================================
    # KEYBOARD
    # =========================================================
    def _on_key_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]
        if key in ("left", "a"):
            self.set_left(True)
        elif key in ("right", "d"):
            self.set_right(True)
        elif key in ("spacebar", "up", "w"):
            self.jump()
        elif key in ("x", "j", "enter"):
            self.attack()
        elif key in ("shift", "z", "k"):
            self.dash()
        return True

    def _on_key_up(self, keyboard, keycode):
        key = keycode[1]
        if key in ("left", "a"):
            self.move_left = False
        elif key in ("right", "d"):
            self.move_right = False
        return True

    # =========================================================
    # AKSI PEMAIN
    # =========================================================
    def jump(self):
        if self.game_over:
            return
        if self.is_grounded and not self.is_dashing:
            self.player_vy = self.JUMP_POWER
            self.is_grounded = False

    def attack(self):
        if self.game_over or self.attack_cooldown > 0 or self.is_dashing:
            return
        self.attack_cooldown = self.ATTACK_COOLDOWN
        self.attack_anim = 0.22
        self.player_attacks.append({
            "x": self.player_x + (55 if self.facing > 0 else -25),
            "y": self.player_y + 45,
            "vx": 900 * self.facing
        })

    def dash(self):
        if self.game_over or self.dash_cooldown > 0 or self.is_dashing:
            return
        self.is_dashing = True
        self.dash_timer = self.DASH_TIME
        self.dash_cooldown = self.DASH_COOLDOWN
        self.invuln_timer = max(self.invuln_timer, self.DASH_TIME + 0.05)
        self.player_vy = 0

    # =========================================================
    # UPDATE UTAMA
    # =========================================================
    def update(self, dt):
        self.anim_timer += dt

        if self.game_over or self.victory:
            self._update_status_label()
            self.draw_game()
            return

        self._update_player(dt)
        self._update_camera()
        self._update_player_attacks(dt)
        self._update_pickups()
        self._update_boss(dt)
        self._update_boss_bullets(dt)
        self._update_boss_hazards(dt)

        if self.player_hp <= 0 and not self.game_over:
            self.game_over = True
            self.status_label.text = "YOU DIED"
            self.status_label.color = (0.9, 0.15, 0.15, 1)

        if self.boss_hp <= 0 and not self.victory:
            self.victory = True
            self.status_label.text = "BOSS DEFEATED!"
            self.status_label.color = (1, 0.85, 0.3, 1)

        self.draw_game()

    def _update_status_label(self):
        self.status_label.opacity = 1
        self.status_label.center = self.center

    # ---------------------------------------------------------
    def _update_player(self, dt):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        if self.attack_anim > 0:
            self.attack_anim -= dt
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.invuln_timer > 0:
            self.invuln_timer -= dt

        if self.is_dashing:
            self.dash_timer -= dt
            self.trail.append([self.player_x, self.player_y, self.facing, 0.5])
            self.player_vx = self.DASH_SPEED * self.facing
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.player_vx = 0
        else:
            self.player_vx = 0
            if self.move_left:
                self.player_vx -= self.MOVE_SPEED
            if self.move_right:
                self.player_vx += self.MOVE_SPEED

        self.player_x += self.player_vx * dt
        self.player_x = max(0, min(self.player_x, self.LEVEL_WIDTH - 60))

        prev_y = self.player_y

        if not self.is_dashing:
            self.player_y += self.player_vy * dt
            self.player_vy -= self.GRAVITY * dt

        self.is_grounded = False

        if self.player_y <= self.FLOOR_Y:
            self.player_y = self.FLOOR_Y
            self.player_vy = 0
            self.is_grounded = True

        for p in self.platforms:
            if self.player_vy <= 0:
                px, py, pw, ph = p["x"], p["y"], p["w"], p["h"]
                if (self.player_x + 55 > px and self.player_x < px + pw
                        and prev_y >= py + ph - 2 and self.player_y <= py + ph):
                    self.player_y = py + ph
                    self.player_vy = 0
                    self.is_grounded = True

        for tr in self.trail[:]:
            tr[3] -= dt * 2.2
            if tr[3] <= 0:
                self.trail.remove(tr)

        if self.is_dashing:
            self.state = "dash"
        elif self.attack_anim > 0:
            self.state = "attack"
        elif not self.is_grounded:
            self.state = "jump"
        elif self.player_vx != 0:
            self.state = "run"
        else:
            self.state = "idle"

        if self.invuln_timer <= 0:
            for b in self.boss_bullets[:]:
                if self._hit_player(b["x"], b["y"], 14):
                    self.boss_bullets.remove(b)
                    self._damage_player(8)

    def _hit_player(self, x, y, r):
        return (x + r > self.player_x and x - r < self.player_x + 60
                and y + r > self.player_y and y - r < self.player_y + 90)

    def _damage_player(self, amount):
        self.player_hp -= amount
        self.invuln_timer = self.INVULN_TIME
        if self.player_hp < 0:
            self.player_hp = 0

    def _update_camera(self):
        target = self.player_x - self.width / 2
        target = max(0, min(target, max(0, self.LEVEL_WIDTH - self.width)))
        self.camera_x += (target - self.camera_x) * 0.12

    def _update_pickups(self):
        for pk in self.pickups:
            if pk["taken"]:
                continue
            if (abs(pk["x"] - self.player_x) < 40
                    and abs(pk["y"] - self.player_y) < 60):
                pk["taken"] = True
                self.player_hp = min(self.player_max_hp, self.player_hp + 15)

    # ---------------------------------------------------------
    def _update_player_attacks(self, dt):
        for atk in self.player_attacks[:]:
            atk["x"] += atk["vx"] * dt

            if (abs(atk["x"] - (self.boss_x + 50)) < 60
                    and atk["y"] > self.boss_y and atk["y"] < self.boss_y + 160
                    and self.boss_hp > 0):
                self.boss_hp = max(0, self.boss_hp - 6)
                self.player_attacks.remove(atk)
            elif atk["x"] < self.camera_x - 100 or atk["x"] > self.camera_x + self.width + 100:
                self.player_attacks.remove(atk)

    # ---------------------------------------------------------
    # BOSS AI - GAYA CUPHEAD (telegraph -> serangan -> jeda)
    # ---------------------------------------------------------
    def _boss_phase(self):
        frac = self.boss_hp / self.boss_max_hp
        if frac > 0.66:
            return 1
        elif frac > 0.33:
            return 2
        return 3

    def _update_boss(self, dt):
        if self.boss_hp <= 0:
            self.boss_state = "dead"
            return

        self.boss_glow = (math.sin(self.anim_timer * 3) + 1) / 2
        self.boss_facing = -1 if self.player_x < self.boss_x else 1
        self.boss_timer -= dt

        if self.boss_state == "cooldown":
            if self.boss_timer <= 0:
                self._start_next_attack()

        elif self.boss_state == "telegraph":
            self.boss_flash = (math.sin(self.anim_timer * 20) + 1) / 2
            if self.boss_timer <= 0:
                self._execute_attack()

        elif self.boss_state == "charging":
            self.boss_x += self.boss_dash_vx * dt
            if self._hit_player(self.boss_x + 50, self.boss_y + 70, 60):
                self._damage_player(15)
            if self.boss_timer <= 0:
                self.boss_state = "returning"
                self.boss_timer = 0.6

        elif self.boss_state == "returning":
            dx = self.boss_home_x - self.boss_x
            self.boss_x += dx * 6 * dt
            if abs(dx) < 4 or self.boss_timer <= 0:
                self.boss_x = self.boss_home_x
                self._end_attack()

        elif self.boss_state == "attacking":
            if self.boss_timer <= 0:
                self._end_attack()

    def _start_next_attack(self):
        phase = self._boss_phase()
        options = ["spread", "aimed"]
        if phase >= 2:
            options.append("slam")
        if phase >= 3:
            options.append("charge")

        self.current_attack = random.choice(options)
        self.boss_state = "telegraph"
        self.boss_timer = 0.6 if phase < 3 else 0.4

        if self.current_attack == "slam":
            self.pending_slam_x = self.player_x
            self.boss_hazards.append({
                "type": "slam", "x": self.pending_slam_x,
                "radius": 0, "max_radius": 140,
                "timer": self.boss_timer, "dur": self.boss_timer
            })
        elif self.current_attack == "charge":
            self.boss_hazards.append({
                "type": "charge_line", "y": self.boss_y,
                "timer": self.boss_timer, "dur": self.boss_timer
            })

    def _execute_attack(self):
        if self.current_attack == "spread":
            dx = self.player_x - self.boss_x
            dy = self.player_y - self.boss_y
            base_angle = math.atan2(dy, dx)
            for off in (-0.35, 0, 0.35):
                ang = base_angle + off
                self.boss_bullets.append({
                    "x": self.boss_x + 20, "y": self.boss_y + 90,
                    "vx": math.cos(ang) * 420, "vy": math.sin(ang) * 420
                })
            self.boss_state = "attacking"
            self.boss_timer = 0.3

        elif self.current_attack == "aimed":
            dx = self.player_x - self.boss_x
            dy = self.player_y - self.boss_y
            dist = max(1, math.hypot(dx, dy))
            self.boss_bullets.append({
                "x": self.boss_x + 20, "y": self.boss_y + 90,
                "vx": dx / dist * 500, "vy": dy / dist * 500
            })
            self.boss_state = "attacking"
            self.boss_timer = 0.3

        elif self.current_attack == "slam":
            self.boss_state = "attacking"
            self.boss_timer = 0.15
            if abs(self.player_x - self.pending_slam_x) < 130 and self.is_grounded:
                self._damage_player(18)

        elif self.current_attack == "charge":
            self.boss_dash_vx = 1400 * (-1 if self.boss_x > self.player_x else 1)
            self.boss_state = "charging"
            self.boss_timer = 0.5

    def _end_attack(self):
        phase = self._boss_phase()
        self.boss_state = "cooldown"
        self.boss_timer = random.uniform(1.4, 2.2) if phase < 3 else random.uniform(0.8, 1.3)

    def _update_boss_bullets(self, dt):
        for b in self.boss_bullets[:]:
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
            if (b["x"] < self.camera_x - 150 or b["x"] > self.camera_x + self.width + 150
                    or b["y"] < -50 or b["y"] > 1200):
                self.boss_bullets.remove(b)

    def _update_boss_hazards(self, dt):
        for hz in self.boss_hazards[:]:
            hz["timer"] -= dt
            if hz["type"] == "slam":
                progress = 1 - max(0, hz["timer"]) / hz["dur"]
                hz["radius"] = hz["max_radius"] * progress
            if hz["timer"] <= -0.3:
                self.boss_hazards.remove(hz)

    # =========================================================
    # GAMBAR
    # =========================================================
    def w2s(self, x):
        return x - self.camera_x

    def draw_game(self):
        self.canvas.before.clear()

        with self.canvas.before:
            self._draw_background()
            self._draw_platforms()
            self._draw_pickups()
            self._draw_hazards()
            self._draw_boss()
            self._draw_boss_bullets()
            self._draw_player_trail()
            self._draw_player()
            self._draw_player_attacks()
            self._draw_ui()

    def _draw_background(self):
        Color(0.02, 0.02, 0.06, 1)
        Rectangle(pos=(0, 0), size=(self.width, self.height))

        Color(0.85, 0.9, 1, 1)
        Ellipse(pos=(self.width - 180, self.height - 180), size=(100, 100))

        for sx, sy, parallax, size in self.stars:
            sxs = self.w2s(sx * parallax)
            if -20 < sxs < self.width + 20:
                Color(1, 1, 1, 0.5)
                Ellipse(pos=(sxs, sy), size=(size, size))

        Color(0.12, 0.12, 0.18, 1)
        Rectangle(pos=(0, 0), size=(self.width, self.FLOOR_Y))

    def _draw_platforms(self):
        Color(0.16, 0.16, 0.24, 1)
        for p in self.platforms:
            x = self.w2s(p["x"])
            if -220 < x < self.width + 220:
                RoundedRectangle(pos=(x, p["y"]), size=(p["w"], p["h"]), radius=[6])

    def _draw_pickups(self):
        for pk in self.pickups:
            if pk["taken"]:
                continue
            x = self.w2s(pk["x"])
            if -30 < x < self.width + 30:
                pulse = 4 * math.sin(self.anim_timer * 4)
                Color(0.3, 1, 0.5, 0.9)
                Ellipse(pos=(x - 10, pk["y"] - 10 + pulse), size=(20, 20))

    def _draw_hazards(self):
        for hz in self.boss_hazards:
            if hz["type"] == "slam":
                x = self.w2s(hz["x"])
                Color(1, 0.2, 0.15, 0.55)
                Line(circle=(x, self.FLOOR_Y, hz["radius"]), width=3)
            elif hz["type"] == "charge_line":
                flash = 0.3 + 0.5 * abs(math.sin(self.anim_timer * 25))
                Color(1, 0.15, 0.15, flash)
                Rectangle(pos=(0, hz["y"] - 5), size=(self.width, 190))

    def _draw_boss(self):
        if self.boss_hp <= 0:
            return

        x = self.w2s(self.boss_x)
        y = self.boss_y

        outline_alpha = 0
        if self.boss_state == "telegraph":
            outline_alpha = self.boss_flash

        phase = self._boss_phase()
        body_color = [(0.75, 0.2, 0.2), (0.55, 0.15, 0.45), (0.3, 0.1, 0.55)][phase - 1]

        Color(*body_color, 1)
        RoundedRectangle(pos=(x, y), size=(100, 150), radius=[14])

        # tanduk
        Color(0.15, 0.05, 0.05, 1)
        Triangle(points=[x + 15, y + 150, x + 30, y + 150, x + 18, y + 190])
        Triangle(points=[x + 85, y + 150, x + 70, y + 150, x + 82, y + 190])

        # inti / mata menyala
        glow_size = 40 + 12 * self.boss_glow
        Color(1, 0.85, 0.25, 0.9)
        Ellipse(pos=(x + 50 - glow_size / 2, y + 85 - glow_size / 2),
                size=(glow_size, glow_size))

        if outline_alpha > 0:
            Color(1, 1, 1, outline_alpha)
            Line(rounded_rectangle=(x, y, 100, 150, 14), width=3)

        # HP bar boss
        Color(0.15, 0.15, 0.15, 1)
        Rectangle(pos=(x - 30, y + 165), size=(160, 12))
        Color(0.9, 0.15, 0.15, 1)
        Rectangle(pos=(x - 30, y + 165), size=(160 * (self.boss_hp / self.boss_max_hp), 12))

    def _draw_boss_bullets(self):
        Color(1, 0.8, 0.2, 1)
        for b in self.boss_bullets:
            x = self.w2s(b["x"])
            Ellipse(pos=(x - 10, b["y"] - 10), size=(20, 20))

    def _draw_player_trail(self):
        for tr in self.trail:
            x, y, facing, alpha = tr
            xs = self.w2s(x)
            Color(0.5, 0.8, 1, alpha)
            RoundedRectangle(pos=(xs, y), size=(60, 90), radius=[10])

    def _draw_player(self):
        if self.invuln_timer > 0 and not self.is_dashing:
            if int(self.invuln_timer * 12) % 2 == 0:
                return

        x = self.w2s(self.player_x)
        y = self.player_y
        facing = self.facing

        walk_cycle = math.sin(self.anim_timer * 10) if self.state == "run" else 0
        idle_bounce = math.sin(self.anim_timer * 3) * 2 if self.state == "idle" else 0

        # jubah
        cape_sway = -facing * (10 + 6 * math.sin(self.anim_timer * 4))
        Color(0.05, 0.05, 0.08, 1)
        Triangle(points=[
            x + 30, y + 70,
            x + 30 + cape_sway, y + 10,
            x + 45, y + 60
        ])

        # kaki
        Color(0.08, 0.08, 0.1, 1)
        leg_off = walk_cycle * 10
        RoundedRectangle(pos=(x + 12, y - 2 + max(0, leg_off)), size=(14, 30), radius=[4])
        RoundedRectangle(pos=(x + 34, y - 2 + max(0, -leg_off)), size=(14, 30), radius=[4])

        # badan
        Color(0.1, 0.1, 0.13, 1)
        RoundedRectangle(pos=(x, y + 20 + idle_bounce), size=(60, 55), radius=[10])

        # topeng
        mask_color = (0.85, 0.9, 1, 1) if not self.is_dashing else (0.5, 0.85, 1, 1)
        Color(*mask_color)
        RoundedRectangle(pos=(x + 8, y + 65 + idle_bounce), size=(44, 34), radius=[10])

        # tanduk kecil
        Color(*mask_color)
        Triangle(points=[x + 10, y + 95 + idle_bounce, x + 18, y + 95 + idle_bounce, x + 12, y + 110 + idle_bounce])
        Triangle(points=[x + 50, y + 95 + idle_bounce, x + 42, y + 95 + idle_bounce, x + 48, y + 110 + idle_bounce])

        # mata
        eye_color = (1, 0.6, 0.15, 1) if self.attack_anim > 0 else (0.1, 0.6, 1, 1)
        Color(*eye_color)
        eye_x = x + 28 if facing > 0 else x + 14
        Ellipse(pos=(eye_x, y + 78 + idle_bounce), size=(9, 9))

        # tebasan senjata saat menyerang
        if self.attack_anim > 0:
            progress = 1 - (self.attack_anim / 0.22)
            reach = 20 + progress * 45
            Color(0.6, 0.95, 1, 0.85)
            Line(points=[
                x + 30 + facing * 20, y + 55,
                x + 30 + facing * reach, y + 40 + progress * 30
            ], width=4)

    def _draw_player_attacks(self):
        Color(0.4, 0.9, 1, 1)
        for atk in self.player_attacks:
            x = self.w2s(atk["x"])
            Ellipse(pos=(x, atk["y"]), size=(22, 22))

    def _draw_ui(self):
        # HP pemain
        Color(0.15, 0.15, 0.15, 1)
        Rectangle(pos=(20, self.height - 34), size=(200, 16))
        hp_frac = max(0, self.player_hp / self.player_max_hp)
        Color(0.2, 0.9, 0.3, 1)
        Rectangle(pos=(20, self.height - 34), size=(200 * hp_frac, 16))

        # cooldown dash (indikator kecil)
        Color(0.2, 0.2, 0.2, 1)
        Rectangle(pos=(20, self.height - 54), size=(100, 8))
        dash_ready = 1 - max(0, self.dash_cooldown) / self.DASH_COOLDOWN
        Color(0.5, 0.85, 1, 1)
        Rectangle(pos=(20, self.height - 54), size=(100 * dash_ready, 8))

    # =========================================================
    # RESIZE
    # =========================================================
    def on_size(self, *args):
        if hasattr(self, "left_button"):
            self.left_button.pos = (20, 20)
            self.right_button.pos = (120, 20)
            self.jump_button.pos = (self.width - 410, 20)
            self.attack_button.pos = (self.width - 280, 20)
            self.dash_button.pos = (self.width - 140, 20)

        if hasattr(self, "status_label"):
            self.status_label.center = self.center
PYEOF
