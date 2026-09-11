from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line, Triangle
from kivy.graphics import PushMatrix, PopMatrix, Rotate
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
import random
import math
import os


# =================================================================
# TOMBOL PIL (bulat, semi transparan) - pengganti Button bawaan Kivy
# =================================================================
class PillButton(Widget):
    def __init__(self, text="", font_size=16, fill=(0.1, 0.11, 0.16, 0.82),
                 outline=(1, 1, 1, 0.22), text_color=(1, 1, 1, 0.95), **kwargs):
        super().__init__(**kwargs)
        self.fill_color = fill
        self.outline_color = outline
        self.pressed = False
        self.press_callbacks = []
        self.release_callbacks = []

        self.label = Label(text=text, font_size=font_size, bold=True, color=text_color)
        self.add_widget(self.label)

        self.bind(pos=self._sync, size=self._sync)
        self._sync()

    def _sync(self, *args):
        self.label.pos = self.pos
        self.label.size = self.size
        self._redraw()

    def _redraw(self):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.pressed:
                Color(self.fill_color[0] * 1.8 + 0.15, self.fill_color[1] * 1.8 + 0.15,
                      self.fill_color[2] * 1.8 + 0.15, self.fill_color[3])
            else:
                Color(*self.fill_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self.height / 2])

            Color(*self.outline_color)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.height / 2), width=1.4)

    def on_press(self, cb):
        self.press_callbacks.append(cb)

    def on_release_cb(self, cb):
        self.release_callbacks.append(cb)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.pressed = True
            self._redraw()
            for cb in self.press_callbacks:
                cb()
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.pressed = False
            self._redraw()
            for cb in self.release_callbacks:
                cb()
            return True
        return False


# =================================================================
# GAME UTAMA
# =================================================================
class DarkKnightGame(Widget):

    GRAVITY = 1900
    MOVE_SPEED = 300
    JUMP_POWER = 700
    DASH_SPEED = 1100
    DASH_TIME = 0.16
    DASH_COOLDOWN = 0.7
    MELEE_COOLDOWN = 0.24
    MELEE_RANGE = 62
    GUN_COOLDOWN = 0.42
    GUN_SPEED = 1150
    BULLET_RADIUS = 7

    LASER_TELEGRAPH_TIME = 0.7
    LASER_ACTIVE_TIME = 0.45
    SWORD_TELEGRAPH_TIME = 0.55
    SWORD_ACTIVE_TIME = 0.25
    STUCK_CHANCE = 0.45
    VULNERABLE_DURATION = 10.0
    BOSS_WALK_SPEED = 220
    BOSS_MAX_HP = 220
    INVULN_TIME = 1.0
    FLOOR_Y = 80
    MAX_MASKS = 5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.room_order = ["gerbang", "lorong", "istirahat", "kabut", "reruntuhan", "arena_bos"]
        self.rooms = self._build_rooms()
        self.current_room = "gerbang"

        self.player_x = 150
        self.player_y = self.FLOOR_Y
        self.player_vx = 0
        self.player_vy = 0
        self.facing = 1
        self.is_grounded = True
        self.masks = self.MAX_MASKS
        self.invuln_timer = 0
        self.game_over = False
        self.victory = False

        self.respawn_room = "gerbang"
        self.respawn_x = 150
        self.respawn_y = self.FLOOR_Y

        self.move_left = False
        self.move_right = False
        self.state = "idle"
        self.anim_timer = 0

        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.trail = []

        self.melee_cooldown = 0
        self.melee_anim = 0
        self.gun_cooldown = 0
        self.gun_flash = 0
        self.player_bullets = []

        self.enemy_bullets = []
        self.camera_x = 0
        self.map_open = False

        self.notice_text = ""
        self.notice_timer = 0

        # Bintang parallax global
        self.stars = [
            (random.uniform(0, 3000), random.uniform(300, 900),
             random.uniform(0.15, 0.5), random.uniform(2, 4))
            for _ in range(60)
        ]

        # Boss (hanya aktif di ruangan arena_bos)
        self._reset_boss()

        self._build_ui()

        Window.bind(on_key_down=self._on_key_down)
        Window.bind(on_key_up=self._on_key_up)

        Clock.schedule_interval(self.update, 1 / 60)

    # =============================================================
    # DEFINISI DUNIA / RUANGAN
    # =============================================================
    ENEMY_DIMS = {
        "crawler": (32, 24),
        "flyer": (28, 20),
        "spitter": (36, 36),
    }

    def _build_rooms(self):
        rooms = {
            "gerbang": {
                "name": "Gerbang Reruntuhan",
                "w": 1500,
                "platforms": [
                    {"x": 500, "y": 220, "w": 180, "h": 22},
                    {"x": 900, "y": 320, "w": 160, "h": 22},
                ],
                "spikes": [],
                "doors": [{"x": 1450, "y": self.FLOOR_Y, "w": 50, "h": 160, "to": "lorong", "tx": 120}],
                "enemies": [
                    {"kind": "crawler", "base_x": 500, "y": self.FLOOR_Y, "hp": 1, "alive": True, "t": 0},
                    {"kind": "crawler", "base_x": 1000, "y": self.FLOOR_Y, "hp": 1, "alive": True, "t": 0},
                ],
                "bench": None,
            },
            "lorong": {
                "name": "Lorong Sunyi",
                "w": 2000,
                "platforms": [
                    {"x": 300, "y": 240, "w": 160, "h": 22},
                    {"x": 620, "y": 360, "w": 180, "h": 22},
                    {"x": 1000, "y": 260, "w": 160, "h": 22},
                    {"x": 1400, "y": 380, "w": 200, "h": 22},
                ],
                "spikes": [{"x": 1150, "y": self.FLOOR_Y, "w": 90, "h": 16}],
                "doors": [
                    {"x": 0, "y": self.FLOOR_Y, "w": 50, "h": 160, "to": "gerbang", "tx": 1360},
                    {"x": 1950, "y": self.FLOOR_Y, "w": 50, "h": 160, "to": "istirahat", "tx": 120},
                ],
                "enemies": [
                    {"kind": "crawler", "base_x": 300, "y": self.FLOOR_Y, "hp": 1, "alive": True, "t": 0},
                    {"kind": "flyer", "base_x": 900, "y": 300, "hp": 1, "alive": True, "t": 0},
                    {"kind": "spitter", "base_x": 1500, "y": self.FLOOR_Y + 40, "hp": 1, "alive": True, "t": 0, "cd": 0},
                    {"kind": "crawler", "base_x": 1700, "y": self.FLOOR_Y, "hp": 1, "alive": True, "t": 0},
                ],
                "bench": None,
            },
            "istirahat": {
                "name": "Tempat Istirahat",
                "w": 900,
                "platforms": [],
                "spikes": [],
                "doors": [
                    {"x": 0, "y": self.FLOOR_Y, "w": 50, "h": 160, "to": "lorong", "tx": 1860},
                    {"x": 850, "y": self.FLOOR_Y, "w": 50, "h": 160, "to": "kabut", "tx": 120},
                ],
                "enemies": [],
                "bench": {"x": 450, "y": self.FLOOR_Y},
            },
            "kabut": {
                "name": "Kabut Terlarang",
                "w": 2200,
                "platforms": [
                    {"x": 260, "y": 300, "w": 160, "h": 22},
                    {"x": 560, "y": 400, "w": 160, "h": 22},
                    {"x": 900, "y": 280, "w": 180, "h": 22},
                    {"x": 1250, "y": 400, "w": 160, "h": 22},
                    {"x": 1600, "y": 300, "w": 200, "h": 22},
                ],
                "spikes": [
                    {"x": 600, "y": self.FLOOR_Y, "w": 100, "h": 16},
                    {"x": 1900, "y": self.FLOOR_Y, "w": 90, "h": 16},
                ],
                "doors": [
                    {"x": 0, "y": self.FLOOR_Y, "w": 50, "h": 160, "to": "istirahat", "tx": 760},
                    {"x": 2150, "y": self.FLOOR_Y, "w": 50, "h": 160, "to": "reruntuhan", "tx": 120},
                ],
                "enemies": [
                    {"kind": "flyer", "base_x": 400, "y": 320, "hp": 1, "alive": True, "t": 0},
                    {"kind": "flyer", "base_x": 1200, "y": 280, "hp": 1, "alive": True, "t": 0},
                    {"kind": "spitter", "base_x": 800, "y": self.FLOOR_Y + 40, "hp": 1, "alive": True, "t": 0, "cd": 0},
                    {"kind": "crawler", "base_x": 1700, "y": self.FLOOR_Y, "hp": 1, "alive": True, "t": 0},
                    {"kind": "crawler", "base_x": 2000, "y": self.FLOOR_Y, "hp": 1, "alive": True, "t": 0},
                ],
                "bench": None,
            },
            "reruntuhan": {
                "name": "Reruntuhan Tua",
                "w": 2000,
                "platforms": [
                    {"x": 300, "y": 260, "w": 160, "h": 22},
                    {"x": 650, "y": 380, "w": 160, "h": 22},
                    {"x": 1000, "y": 260, "w": 180, "h": 22},
                    {"x": 1400, "y": 400, "w": 200, "h": 22},
                ],
                "spikes": [{"x": 950, "y": self.FLOOR_Y, "w": 110, "h": 16}],
                "doors": [
                    {"x": 0, "y": self.FLOOR_Y, "w": 50, "h": 160, "to": "kabut", "tx": 2060},
                    {"x": 1950, "y": self.FLOOR_Y, "w": 50, "h": 160, "to": "arena_bos", "tx": 120},
                ],
                "enemies": [
                    {"kind": "crawler", "base_x": 300, "y": self.FLOOR_Y, "hp": 1, "alive": True, "t": 0},
                    {"kind": "crawler", "base_x": 700, "y": self.FLOOR_Y, "hp": 1, "alive": True, "t": 0},
                    {"kind": "spitter", "base_x": 1100, "y": self.FLOOR_Y + 40, "hp": 1, "alive": True, "t": 0, "cd": 0},
                    {"kind": "flyer", "base_x": 1500, "y": 320, "hp": 1, "alive": True, "t": 0},
                ],
                "bench": None,
            },
            "arena_bos": {
                "name": "Sarang Akar Iblis",
                "w": 1400,
                "platforms": [],
                "spikes": [],
                "doors": [{"x": 0, "y": self.FLOOR_Y, "w": 50, "h": 160, "to": "reruntuhan", "tx": 1860}],
                "enemies": [],
                "bench": None,
                "boss": True,
            },
        }

        for room in rooms.values():
            for e in room["enemies"]:
                e["x"] = e["base_x"]
                if "base_y" not in e:
                    e["base_y"] = e["y"]
                dims = self.ENEMY_DIMS.get(e["kind"], (30, 26))
                e["w"], e["h"] = dims

        return rooms

    def _reset_boss(self):
        room = self.rooms["arena_bos"]
        self.boss_home_x = room["w"] - 220
        self.boss_x = self.boss_home_x
        self.boss_y = self.FLOOR_Y
        self.boss_hp = self.BOSS_MAX_HP
        self.boss_max_hp = self.BOSS_MAX_HP
        self.boss_state = "cooldown"
        self.boss_timer = 1.4
        self.boss_glow = 0
        self.boss_flash = 0
        self.current_attack = None
        self.sword_target_x = self.player_x
        self.sword_stuck_x = None
        self.boss_pulling = False

    # =============================================================
    # UI (tombol pil)
    # =============================================================
    def _build_ui(self):
        self.left_button = PillButton(text="<", font_size=34, size_hint=(None, None), size=(110, 110))
        self.right_button = PillButton(text=">", font_size=34, size_hint=(None, None), size=(110, 110))
        self.jump_button = PillButton(text="JUMP", font_size=17, size_hint=(None, None), size=(120, 95))
        self.dash_button = PillButton(text="DASH", font_size=17, size_hint=(None, None), size=(120, 95))
        self.melee_button = PillButton(text="PEDANG", font_size=16,
                                        fill=(0.35, 0.1, 0.1, 0.82), size_hint=(None, None), size=(140, 95))
        self.gun_button = PillButton(text="PISTOL", font_size=16,
                                      fill=(0.1, 0.2, 0.35, 0.82), size_hint=(None, None), size=(140, 95))
        self.map_button = PillButton(text="MAP", font_size=15, size_hint=(None, None), size=(100, 60))

        for b in (self.left_button, self.right_button, self.jump_button, self.dash_button,
                  self.melee_button, self.gun_button, self.map_button):
            self.add_widget(b)

        self.left_button.on_press(lambda: self.set_left(True))
        self.left_button.on_release_cb(lambda: self.set_left(False))
        self.right_button.on_press(lambda: self.set_right(True))
        self.right_button.on_release_cb(lambda: self.set_right(False))
        self.jump_button.on_press(self.jump)
        self.dash_button.on_press(self.dash)
        self.melee_button.on_press(self.melee_attack)
        self.gun_button.on_press(self.ranged_attack)
        self.map_button.on_press(self.toggle_map)

        # Panel label ruangan
        self.room_label = Label(text="", font_size="18sp", bold=True,
                                 size_hint=(None, None), size=(400, 30),
                                 color=(1, 1, 1, 0.9))
        self.add_widget(self.room_label)

        self.notice_label = Label(text="", font_size="15sp",
                                   size_hint=(None, None), size=(500, 30),
                                   color=(1, 1, 1, 0.85))
        self.add_widget(self.notice_label)

        # Overlay status (mati / menang)
        self.status_label = Label(text="", font_size=38, bold=True,
                                   size_hint=(None, None), size=(500, 70), opacity=0)
        self.add_widget(self.status_label)

        self.retry_button = PillButton(text="COBA LAGI", font_size=18,
                                        size_hint=(None, None), size=(220, 70), opacity=0)
        self.retry_button.on_press(self._do_retry)
        self.add_widget(self.retry_button)

        # Panel peta
        self.map_close_button = PillButton(text="Tutup Peta", font_size=16,
                                            size_hint=(None, None), size=(180, 60), opacity=0)
        self.map_close_button.on_press(self.toggle_map)
        self.add_widget(self.map_close_button)

        self._update_room_label()

    def _update_room_label(self):
        room = self.rooms[self.current_room]
        self.room_label.text = room["name"]

    def _show_notice(self, text, dur=2.0):
        self.notice_text = text
        self.notice_timer = dur

    def toggle_map(self):
        self.map_open = not self.map_open
        opac = 1 if self.map_open else 0
        self.map_close_button.opacity = opac
        self.map_close_button.disabled = not self.map_open

    # =============================================================
    # KEYBOARD
    # =============================================================
    def _on_key_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]
        if key in ("left", "a"):
            self.set_left(True)
        elif key in ("right", "d"):
            self.set_right(True)
        elif key in ("spacebar", "up", "w"):
            self.jump()
        elif key in ("x", "j", "enter"):
            self.melee_attack()
        elif key in ("c", "v"):
            self.ranged_attack()
        elif key in ("shift", "z", "k"):
            self.dash()
        elif key == "m":
            self.toggle_map()
        return True

    def _on_key_up(self, keyboard, keycode):
        key = keycode[1]
        if key in ("left", "a"):
            self.move_left = False
        elif key in ("right", "d"):
            self.move_right = False
        return True

    def set_left(self, value):
        self.move_left = value
        if value:
            self.facing = -1

    def set_right(self, value):
        self.move_right = value
        if value:
            self.facing = 1

    # =============================================================
    # AKSI PEMAIN
    # =============================================================
    def jump(self):
        if self.game_over or self.victory or self.map_open:
            return
        if self.is_grounded and not self.is_dashing:
            self.player_vy = self.JUMP_POWER
            self.is_grounded = False

    def melee_attack(self):
        if self.game_over or self.victory or self.map_open:
            return
        if self.melee_cooldown > 0 or self.is_dashing:
            return
        self.melee_cooldown = self.MELEE_COOLDOWN
        self.melee_anim = 0.18
        self._do_melee_hit()

    def _do_melee_hit(self):
        room = self.rooms[self.current_room]

        if self.facing > 0:
            hit_x1 = self.player_x + 30
            hit_x2 = self.player_x + 30 + self.MELEE_RANGE
        else:
            hit_x1 = self.player_x - self.MELEE_RANGE
            hit_x2 = self.player_x + 30
        hit_y1 = self.player_y
        hit_y2 = self.player_y + 90

        for e in room["enemies"]:
            if not e["alive"]:
                continue
            ew, eh = e["w"], e["h"]
            ex1, ex2 = e["x"] - ew / 2, e["x"] + ew / 2
            ey1, ey2 = e["y"], e["y"] + eh
            if hit_x1 < ex2 and hit_x2 > ex1 and hit_y1 < ey2 and hit_y2 > ey1:
                e["hp"] -= 1
                if e["hp"] <= 0:
                    e["alive"] = False

        if (self.current_room == "arena_bos" and self.boss_hp > 0
                and self.boss_state == "vulnerable"):
            bx1, bx2 = self.boss_x, self.boss_x + 100
            by1, by2 = self.boss_y, self.boss_y + 140
            if hit_x1 < bx2 and hit_x2 > bx1 and hit_y1 < by2 and hit_y2 > by1:
                self.boss_hp = max(0, self.boss_hp - 10)

    def ranged_attack(self):
        if self.game_over or self.victory or self.map_open:
            return
        if self.gun_cooldown > 0 or self.is_dashing:
            return
        self.gun_cooldown = self.GUN_COOLDOWN
        self.gun_flash = 0.08
        self.player_bullets.append({
            "x": self.player_x + (60 if self.facing > 0 else -10),
            "y": self.player_y + 50,
            "vx": self.GUN_SPEED * self.facing
        })

    def dash(self):
        if self.game_over or self.victory or self.map_open:
            return
        if self.dash_cooldown > 0 or self.is_dashing:
            return
        self.is_dashing = True
        self.dash_timer = self.DASH_TIME
        self.dash_cooldown = self.DASH_COOLDOWN
        self.invuln_timer = max(self.invuln_timer, self.DASH_TIME + 0.05)
        self.player_vy = 0

    def _do_retry(self):
        if not (self.game_over or self.victory):
            return
        self.game_over = False
        self.masks = self.MAX_MASKS
        self.invuln_timer = self.INVULN_TIME
        self.current_room = self.respawn_room
        self.player_x = self.respawn_x
        self.player_y = self.respawn_y
        self.player_vx = 0
        self.player_vy = 0
        self.enemy_bullets = []
        self.status_label.opacity = 0
        self.retry_button.opacity = 0
        self.retry_button.disabled = True
        self._update_room_label()

        if self.victory:
            # Main lagi dari awal total
            self.victory = False
            self.rooms = self._build_rooms()
            self._reset_boss()
            self.current_room = "gerbang"
            self.player_x = 150
            self.player_y = self.FLOOR_Y
            self.respawn_room = "gerbang"
            self.respawn_x = 150
            self.respawn_y = self.FLOOR_Y
            self._update_room_label()

    # =============================================================
    # UPDATE UTAMA
    # =============================================================
    def update(self, dt):
        self.anim_timer += dt

        if self.notice_timer > 0:
            self.notice_timer -= dt
            self.notice_label.text = self.notice_text if self.notice_timer > 0 else ""

        if self.game_over or self.victory:
            self.status_label.opacity = 1
            self.retry_button.opacity = 1
            self.retry_button.disabled = False
            self._layout_ui()
            self.draw_game()
            return

        if self.map_open:
            self._layout_ui()
            self.draw_game()
            return

        self._update_player(dt)
        self._update_camera()
        self._update_player_bullets(dt)
        self._update_enemies(dt)
        self._update_enemy_bullets(dt)
        self._check_doors()
        self._check_bench()

        if self.current_room == "arena_bos":
            self._update_boss(dt)

        if self.masks <= 0 and not self.game_over:
            self.game_over = True
            self.status_label.text = "KAMU MATI"
            self.status_label.color = (0.9, 0.15, 0.15, 1)

        if self.current_room == "arena_bos" and self.boss_hp <= 0 and not self.victory:
            self.victory = True
            self.status_label.text = "AKAR IBLIS TUMBANG!"
            self.status_label.color = (1, 0.85, 0.3, 1)

        self._layout_ui()
        self.draw_game()

    # ---------------------------------------------------------
    def _update_player(self, dt):
        room = self.rooms[self.current_room]

        if self.melee_cooldown > 0:
            self.melee_cooldown -= dt
        if self.melee_anim > 0:
            self.melee_anim -= dt
        if self.gun_cooldown > 0:
            self.gun_cooldown -= dt
        if self.gun_flash > 0:
            self.gun_flash -= dt
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
        self.player_x = max(0, min(self.player_x, room["w"] - 60))

        prev_y = self.player_y

        if not self.is_dashing:
            self.player_y += self.player_vy * dt
            self.player_vy -= self.GRAVITY * dt

        self.is_grounded = False

        if self.player_y <= self.FLOOR_Y:
            self.player_y = self.FLOOR_Y
            self.player_vy = 0
            self.is_grounded = True

        for p in room["platforms"]:
            if self.player_vy <= 0:
                px, py, pw, ph = p["x"], p["y"], p["w"], p["h"]
                if (self.player_x + 55 > px and self.player_x < px + pw
                        and prev_y >= py + ph - 2 and self.player_y <= py + ph):
                    self.player_y = py + ph
                    self.player_vy = 0
                    self.is_grounded = True

        # Duri
        if self.invuln_timer <= 0:
            for s in room["spikes"]:
                if (self.player_x + 50 > s["x"] and self.player_x < s["x"] + s["w"]
                        and self.player_y < s["y"] + s["h"] + 10):
                    self._damage_player(1)
                    self.player_vy = 600
                    self.player_x -= 40 * self.facing

        for tr in self.trail[:]:
            tr[3] -= dt * 2.2
            if tr[3] <= 0:
                self.trail.remove(tr)

        if self.is_dashing:
            self.state = "dash"
        elif self.melee_anim > 0:
            self.state = "attack"
        elif not self.is_grounded:
            self.state = "jump"
        elif self.player_vx != 0:
            self.state = "run"
        else:
            self.state = "idle"

        if self.invuln_timer <= 0:
            for b in self.enemy_bullets[:]:
                if self._hit_player(b["x"], b["y"], 10):
                    self.enemy_bullets.remove(b)
                    self._damage_player(1)
            for e in room["enemies"]:
                if e["alive"] and self._hit_player(e["x"], e["y"] + 15, 20):
                    self._damage_player(1)

    def _hit_player(self, x, y, r):
        return (x + r > self.player_x and x - r < self.player_x + 60
                and y + r > self.player_y and y - r < self.player_y + 90)

    def _damage_player(self, amount):
        if self.invuln_timer > 0:
            return
        self.masks -= amount
        self.invuln_timer = self.INVULN_TIME
        if self.masks < 0:
            self.masks = 0

    def _update_camera(self):
        room = self.rooms[self.current_room]
        target = self.player_x - self.width / 2
        target = max(0, min(target, max(0, room["w"] - self.width)))
        self.camera_x += (target - self.camera_x) * 0.15

    def _check_doors(self):
        room = self.rooms[self.current_room]
        for d in room["doors"]:
            if (self.player_x + 50 > d["x"] and self.player_x < d["x"] + d["w"]
                    and self.player_y < d["y"] + d["h"]):
                self.current_room = d["to"]
                self.player_x = d["tx"]
                self.player_y = self.FLOOR_Y
                self.player_vx = 0
                self.player_vy = 0
                self.enemy_bullets = []
                new_room = self.rooms[self.current_room]
                self.camera_x = max(0, min(self.player_x - self.width / 2,
                                            max(0, new_room["w"] - self.width)))
                self._update_room_label()
                self._show_notice(new_room["name"])
                return

    def _check_bench(self):
        room = self.rooms[self.current_room]
        bench = room.get("bench")
        if bench and abs(self.player_x - bench["x"]) < 50:
            if self.masks < self.MAX_MASKS:
                self._show_notice("Beristirahat... HP dipulihkan")
            self.masks = self.MAX_MASKS
            self.respawn_room = self.current_room
            self.respawn_x = bench["x"]
            self.respawn_y = self.FLOOR_Y

    # ---------------------------------------------------------
    def _update_player_bullets(self, dt):
        room = self.rooms[self.current_room]
        r = self.BULLET_RADIUS

        for atk in self.player_bullets[:]:
            atk["x"] += atk["vx"] * dt
            bx, by = atk["x"], atk["y"]
            hit = False

            for e in room["enemies"]:
                if not e["alive"]:
                    continue
                ew, eh = e["w"], e["h"]
                ex1, ex2 = e["x"] - ew / 2, e["x"] + ew / 2
                ey1, ey2 = e["y"], e["y"] + eh
                if bx + r > ex1 and bx - r < ex2 and by + r > ey1 and by - r < ey2:
                    e["hp"] -= 1
                    if e["hp"] <= 0:
                        e["alive"] = False
                    hit = True
                    break

            if (not hit and self.current_room == "arena_bos" and self.boss_hp > 0
                    and self.boss_state == "vulnerable"):
                bx1, bx2 = self.boss_x, self.boss_x + 100
                by1, by2 = self.boss_y, self.boss_y + 140
                if bx + r > bx1 and bx - r < bx2 and by + r > by1 and by - r < by2:
                    self.boss_hp = max(0, self.boss_hp - 6)
                    hit = True

            if hit or bx < self.camera_x - 100 or bx > self.camera_x + self.width + 100:
                if atk in self.player_bullets:
                    self.player_bullets.remove(atk)

    # ---------------------------------------------------------
    # MUSUH KECIL (crawler / flyer / spitter)
    # ---------------------------------------------------------
    def _update_enemies(self, dt):
        room = self.rooms[self.current_room]
        for e in room["enemies"]:
            if not e["alive"]:
                continue
            e["t"] += dt

            if e["kind"] == "crawler":
                e["x"] = e["base_x"] + math.sin(e["t"] * 1.1) * 70

            elif e["kind"] == "flyer":
                e["x"] = e["base_x"] + math.sin(e["t"] * 0.7) * 45
                e["y"] = e["base_y"] + math.sin(e["t"] * 2.0) * 28

            elif e["kind"] == "spitter":
                e["x"] = e["base_x"]
                e["cd"] -= dt
                if e["cd"] <= 0:
                    e["cd"] = 2.2
                    dx = self.player_x - e["x"]
                    dy = self.player_y - e["y"]
                    dist = max(1, math.hypot(dx, dy))
                    self.enemy_bullets.append({
                        "x": e["x"], "y": e["y"],
                        "vx": dx / dist * 260, "vy": dy / dist * 260
                    })

            if "y" not in e:
                e["y"] = e["base_y"] if "base_y" in e else e.get("y", self.FLOOR_Y)

        # inisialisasi y untuk enemy yang pakai base_y (flyer)
        for e in room["enemies"]:
            if "base_y" not in e:
                e["base_y"] = e["y"]

    def _update_enemy_bullets(self, dt):
        for b in self.enemy_bullets[:]:
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
            if (b["x"] < self.camera_x - 150 or b["x"] > self.camera_x + self.width + 150
                    or b["y"] < -50 or b["y"] > 1200):
                self.enemy_bullets.remove(b)

    # ---------------------------------------------------------
    # BOSS - RAJA TENGKORAK (laser + tebasan pedang + jendela lemah)
    # ---------------------------------------------------------
    def _update_boss(self, dt):
        if self.boss_hp <= 0:
            self.boss_state = "dead"
            return

        self.boss_glow = (math.sin(self.anim_timer * 3) + 1) / 2
        self.boss_timer -= dt

        if self.boss_state == "cooldown":
            if self.boss_timer <= 0:
                self._start_next_attack()

        elif self.boss_state == "laser_telegraph":
            self.boss_flash = (math.sin(self.anim_timer * 18) + 1) / 2
            if self.boss_timer <= 0:
                self.boss_state = "laser_active"
                self.boss_timer = self.LASER_ACTIVE_TIME

        elif self.boss_state == "laser_active":
            if self._player_in_laser_band() and self.is_grounded:
                self._damage_player(1)
            if self.boss_timer <= 0:
                self._end_attack()

        elif self.boss_state == "sword_telegraph":
            self.boss_flash = (math.sin(self.anim_timer * 18) + 1) / 2
            if self.boss_timer <= 0:
                self.boss_state = "sword_active"
                self.boss_timer = self.SWORD_ACTIVE_TIME

        elif self.boss_state == "sword_active":
            if self._player_in_sword_column():
                self._damage_player(1)
            if self.boss_timer <= 0:
                if random.random() < self.STUCK_CHANCE:
                    self._trigger_sword_stuck()
                else:
                    self._end_attack()

        elif self.boss_state == "vulnerable":
            self._update_vulnerable(dt)

    def _player_in_laser_band(self):
        band_bottom = self.FLOOR_Y - 10
        band_top = self.FLOOR_Y + 100
        return self.player_y < band_top and (self.player_y + 90) > band_bottom

    def _player_in_sword_column(self):
        half = 65
        x1, x2 = self.sword_target_x - half, self.sword_target_x + half
        return (self.player_x + 60) > x1 and self.player_x < x2

    def _start_next_attack(self):
        self.current_attack = random.choice(["laser", "sword"])
        if self.current_attack == "laser":
            self.boss_state = "laser_telegraph"
            self.boss_timer = self.LASER_TELEGRAPH_TIME
        else:
            self.sword_target_x = self.player_x
            self.boss_state = "sword_telegraph"
            self.boss_timer = self.SWORD_TELEGRAPH_TIME

    def _trigger_sword_stuck(self):
        room = self.rooms["arena_bos"]
        self.sword_stuck_x = random.uniform(room["w"] * 0.3, room["w"] * 0.6)
        self.boss_state = "vulnerable"
        self.boss_timer = self.VULNERABLE_DURATION
        self.boss_pulling = False

    def _update_vulnerable(self, dt):
        dx = self.sword_stuck_x - self.boss_x
        if abs(dx) > 6 and not self.boss_pulling:
            step = min(abs(dx), self.BOSS_WALK_SPEED * dt)
            self.boss_x += step * (1 if dx > 0 else -1)
        else:
            self.boss_pulling = True

        if self.boss_timer <= 0:
            self.boss_x = self.boss_home_x
            self.boss_pulling = False
            self.sword_stuck_x = None
            self._end_attack()

    def _end_attack(self):
        self.boss_state = "cooldown"
        self.boss_timer = random.uniform(1.0, 1.6)

    # =============================================================
    # GAMBAR
    # =============================================================
    def w2s(self, x):
        return x - self.camera_x

    def draw_game(self):
        self.canvas.before.clear()

        with self.canvas.before:
            self._draw_background()

            if not self.map_open:
                room = self.rooms[self.current_room]
                self._draw_platforms(room)
                self._draw_spikes(room)
                self._draw_doors(room)
                self._draw_bench(room)
                self._draw_enemies(room)
                self._draw_enemy_bullets()

                if self.current_room == "arena_bos":
                    self._draw_throne(room)
                    self._draw_boss_attacks()
                    self._draw_boss()

                self._draw_player_trail()
                self._draw_player()
                self._draw_player_bullets()
                self._draw_ui()
            else:
                self._draw_map()

    def _draw_background(self):
        Color(0.02, 0.02, 0.06, 1)
        Rectangle(pos=(0, 0), size=(self.width, self.height))

        Color(0.85, 0.9, 1, 1)
        Ellipse(pos=(self.width - 180, self.height - 180), size=(100, 100))

        for sx, sy, parallax, size in self.stars:
            sxs = self.w2s(sx * parallax) % (self.width + 40) - 20
            Color(1, 1, 1, 0.4)
            Ellipse(pos=(sxs, sy if sy < self.height else self.height - 40), size=(size, size))

        if not self.map_open:
            Color(0.12, 0.12, 0.18, 1)
            Rectangle(pos=(0, 0), size=(self.width, self.FLOOR_Y))

    def _draw_platforms(self, room):
        Color(0.16, 0.16, 0.24, 1)
        for p in room["platforms"]:
            x = self.w2s(p["x"])
            if -220 < x < self.width + 220:
                RoundedRectangle(pos=(x, p["y"]), size=(p["w"], p["h"]), radius=[6])

    def _draw_spikes(self, room):
        Color(0.75, 0.15, 0.2, 1)
        for s in room["spikes"]:
            x = self.w2s(s["x"])
            count = max(1, int(s["w"] / 18))
            for i in range(count):
                sx = x + i * 18
                Triangle(points=[sx, s["y"], sx + 9, s["y"] + s["h"] + 14, sx + 18, s["y"]])

    def _draw_doors(self, room):
        for d in room["doors"]:
            x = self.w2s(d["x"])
            if -100 < x < self.width + 100:
                Color(0.5, 0.7, 1, 0.35)
                RoundedRectangle(pos=(x, d["y"]), size=(d["w"], d["h"]), radius=[10])
                Color(0.7, 0.85, 1, 0.6)
                Line(rounded_rectangle=(x, d["y"], d["w"], d["h"], 10), width=2)

    def _draw_bench(self, room):
        bench = room.get("bench")
        if not bench:
            return
        x = self.w2s(bench["x"])
        Color(0.45, 0.32, 0.2, 1)
        Rectangle(pos=(x - 40, bench["y"] + 20), size=(80, 10))
        Rectangle(pos=(x - 32, bench["y"]), size=(8, 22))
        Rectangle(pos=(x + 24, bench["y"]), size=(8, 22))
        glow = 6 * math.sin(self.anim_timer * 2)
        Color(1, 0.9, 0.6, 0.5)
        Ellipse(pos=(x - 10, bench["y"] + 34 + glow), size=(20, 14))

    def _draw_enemies(self, room):
        for e in room["enemies"]:
            if not e["alive"]:
                continue
            x = self.w2s(e["x"])
            y = e["y"]
            if x < -60 or x > self.width + 60:
                continue

            if e["kind"] == "crawler":
                Color(0.4, 0.15, 0.5, 1)
                RoundedRectangle(pos=(x - 16, y), size=(32, 24), radius=[8])
                Color(1, 0.3, 0.3, 1)
                Ellipse(pos=(x - 8, y + 8), size=(7, 7))
                Ellipse(pos=(x + 3, y + 8), size=(7, 7))

            elif e["kind"] == "flyer":
                wing = 6 * math.sin(self.anim_timer * 10)
                Color(0.2, 0.3, 0.55, 1)
                Ellipse(pos=(x - 14, y), size=(28, 20))
                Color(0.3, 0.45, 0.75, 0.8)
                Triangle(points=[x - 14, y + 10, x - 26, y + 16 + wing, x - 14, y + 18])
                Triangle(points=[x + 14, y + 10, x + 26, y + 16 - wing, x + 14, y + 18])
                Color(1, 0.85, 0.3, 1)
                Ellipse(pos=(x - 4, y + 6), size=(8, 8))

            elif e["kind"] == "spitter":
                pulse = 3 * math.sin(self.anim_timer * 4)
                Color(0.55, 0.2, 0.15, 1)
                Ellipse(pos=(x - 18, y - 4), size=(36, 36 + pulse))
                Color(1, 0.6, 0.2, 1)
                Ellipse(pos=(x - 6, y + 8), size=(12, 12))

    def _draw_enemy_bullets(self):
        Color(1, 0.5, 0.3, 1)
        for b in self.enemy_bullets:
            x = self.w2s(b["x"])
            Ellipse(pos=(x - 7, b["y"] - 7), size=(14, 14))

    def _draw_throne(self, room):
        x = self.w2s(self.boss_home_x)
        Color(0.12, 0.1, 0.14, 1)
        Rectangle(pos=(x - 20, self.FLOOR_Y), size=(140, 20))
        Color(0.1, 0.08, 0.12, 1)
        RoundedRectangle(pos=(x - 10, self.FLOOR_Y + 20), size=(120, 170), radius=[10])
        Color(0.22, 0.2, 0.24, 1)
        for i in range(5):
            sx = x - 10 + i * 24
            Triangle(points=[sx, self.FLOOR_Y + 190, sx + 16, self.FLOOR_Y + 190, sx + 8, self.FLOOR_Y + 222])

    def _draw_boss_attacks(self):
        if self.boss_state == "laser_telegraph":
            alpha = 0.25 + 0.35 * self.boss_flash
            Color(1, 0.2, 0.2, alpha)
            Rectangle(pos=(0, self.FLOOR_Y - 10), size=(self.width, 4))

        elif self.boss_state == "laser_active":
            Color(0.75, 0.25, 1, 0.85)
            Rectangle(pos=(0, self.FLOOR_Y - 10), size=(self.width, 110))
            Color(1, 0.9, 1, 0.5)
            for i in range(8):
                px = (self.anim_timer * 300 + i * 90) % (self.width + 40) - 20
                py = self.FLOOR_Y + 30 + 10 * math.sin(self.anim_timer * 6 + i)
                Ellipse(pos=(px, py), size=(10, 10))

        elif self.boss_state == "sword_telegraph":
            x = self.w2s(self.sword_target_x)
            alpha = 0.2 + 0.3 * self.boss_flash
            Color(1, 0.2, 0.2, alpha)
            Rectangle(pos=(x - 65, 0), size=(130, self.height))

        elif self.boss_state == "sword_active":
            x = self.w2s(self.sword_target_x)
            Color(0.85, 0.85, 1, 0.8)
            Rectangle(pos=(x - 65, 0), size=(130, self.height))

        if self.sword_stuck_x is not None:
            sx = self.w2s(self.sword_stuck_x)
            wiggle = 3 * math.sin(self.anim_timer * 25) if self.boss_pulling else 0
            Color(0.75, 0.78, 0.85, 1)
            Line(points=[sx + wiggle, self.FLOOR_Y, sx + 8 + wiggle, self.FLOOR_Y + 110], width=6)
            Color(0.5, 0.4, 0.2, 1)
            Rectangle(pos=(sx - 14 + wiggle, self.FLOOR_Y + 95), size=(30, 10))

    def _draw_boss(self):
        if self.boss_hp <= 0:
            return

        x = self.w2s(self.boss_x)
        y = self.boss_y
        telegraphing = self.boss_state in ("laser_telegraph", "sword_telegraph")
        outline_alpha = self.boss_flash if telegraphing else 0
        vulnerable = self.boss_state == "vulnerable"

        # Jubah ungu compang-camping
        Color(0.22, 0.06, 0.28, 1)
        Triangle(points=[x + 8, y + 140, x - 14, y + 35, x + 35, y + 90])
        Triangle(points=[x + 92, y + 140, x + 116, y + 35, x + 70, y + 90])

        # Badan/jubah utama
        body_color = (0.55, 0.08, 0.6, 1) if vulnerable else (0.13, 0.11, 0.16, 1)
        Color(*body_color)
        RoundedRectangle(pos=(x, y), size=(100, 110), radius=[15, 15, 25, 25])

        # Rusuk tulang
        Color(0.9, 0.88, 0.8, 1)
        for i in range(4):
            ry = y + 38 + i * 14
            Line(points=[x + 20, ry, x + 80, ry], width=3)

        # Tengkorak
        Color(0.92, 0.9, 0.82, 1)
        Ellipse(pos=(x + 25, y + 108), size=(50, 46))
        Rectangle(pos=(x + 35, y + 100), size=(30, 14))

        # Mata menyala merah
        eye_glow = 0.6 + 0.4 * self.boss_glow
        Color(1, 0.15, 0.15, eye_glow)
        Ellipse(pos=(x + 34, y + 128), size=(10, 10))
        Ellipse(pos=(x + 56, y + 128), size=(10, 10))

        # Mahkota
        Color(0.85, 0.7, 0.2, 1)
        Triangle(points=[x + 28, y + 152, x + 38, y + 152, x + 33, y + 172])
        Triangle(points=[x + 45, y + 152, x + 55, y + 152, x + 50, y + 178])
        Triangle(points=[x + 62, y + 152, x + 72, y + 152, x + 67, y + 172])
        Rectangle(pos=(x + 26, y + 150), size=(48, 8))

        # Pedang digenggam (kalau nggak lagi tertancap di tanah)
        if self.sword_stuck_x is None:
            Color(0.8, 0.82, 0.88, 1)
            Line(points=[x + 95, y + 90, x + 132, y + 50], width=5)

        if outline_alpha > 0:
            Color(1, 1, 1, outline_alpha)
            Line(rounded_rectangle=(x, y, 100, 110, 20), width=3)

        if vulnerable:
            Color(1, 0.9, 0.3, 0.7 + 0.3 * self.boss_glow)
            Line(rounded_rectangle=(x - 4, y - 4, 108, 118, 22), width=3)

        # HP bar
        Color(0.15, 0.15, 0.15, 1)
        Rectangle(pos=(x - 30, y + 180), size=(160, 12))
        Color(0.8, 0.2, 0.85, 1)
        Rectangle(pos=(x - 30, y + 180), size=(160 * (self.boss_hp / self.boss_max_hp), 12))

        # Sisa waktu jendela lemah
        if vulnerable:
            Color(1, 0.9, 0.3, 1)
            frac = max(0, self.boss_timer) / self.VULNERABLE_DURATION
            Rectangle(pos=(x - 30, y + 196), size=(160 * frac, 6))

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

        # Jubah robek berjumbai (beberapa lapis, meniru kain sobek)
        cape_sway = -facing * (14 + 8 * math.sin(self.anim_timer * 4))
        Color(0.04, 0.04, 0.06, 1)
        Triangle(points=[x + 20, y + 65, x + 14 + cape_sway * 0.6, y + 20, x + 32, y + 45])
        Triangle(points=[x + 28, y + 72, x + 26 + cape_sway * 0.85, y + 28, x + 40, y + 55])
        Triangle(points=[x + 34, y + 70, x + 32 + cape_sway, y + 5, x + 46, y + 50])

        # Kaki
        Color(0.06, 0.06, 0.08, 1)
        leg_off = walk_cycle * 10
        RoundedRectangle(pos=(x + 12, y - 2 + max(0, leg_off)), size=(14, 30), radius=[4])
        RoundedRectangle(pos=(x + 34, y - 2 + max(0, -leg_off)), size=(14, 30), radius=[4])

        # Badan zirah gelap
        Color(0.08, 0.08, 0.11, 1)
        RoundedRectangle(pos=(x, y + 20 + idle_bounce), size=(60, 55), radius=[8])

        # Bahu berlapis baja (pauldron)
        Color(0.15, 0.14, 0.17, 1)
        Triangle(points=[x - 8, y + 66 + idle_bounce, x + 16, y + 80 + idle_bounce, x + 6, y + 53 + idle_bounce])
        Triangle(points=[x + 44, y + 66 + idle_bounce, x + 68, y + 80 + idle_bounce, x + 54, y + 53 + idle_bounce])

        # Tudung penuh menutupi kepala (tanpa wajah terlihat)
        hood_color = (0.07, 0.07, 0.1, 1) if not self.is_dashing else (0.08, 0.22, 0.32, 1)
        Color(*hood_color)
        RoundedRectangle(pos=(x + 6, y + 62 + idle_bounce), size=(48, 30), radius=[16])
        Triangle(points=[x + 12, y + 90 + idle_bounce, x + 48, y + 90 + idle_bounce, x + 30, y + 120 + idle_bounce])

        # Mata menyala samar dalam bayangan tudung
        eye_color = (1, 0.55, 0.15, 0.9) if self.melee_anim > 0 else (0.3, 0.75, 1, 0.85)
        Color(*eye_color)
        eye_x = x + 27 if facing > 0 else x + 15
        Ellipse(pos=(eye_x, y + 79 + idle_bounce), size=(7, 5))

        # --- Senjata ---
        if self.melee_anim > 0:
            progress = 1 - (self.melee_anim / 0.18)
            reach = 25 + progress * 50
            Color(0.75, 0.8, 0.85, 0.95)
            Line(points=[x + 30 + facing * 15, y + 55,
                         x + 30 + facing * reach, y + 35 + progress * 35], width=5)
            Color(0.3, 0.22, 0.15, 1)
            Ellipse(pos=(x + 30 + facing * 12 - 5, y + 50), size=(10, 10))
        else:
            gx = x + 40 if facing > 0 else x - 8
            Color(0.15, 0.15, 0.17, 1)
            Rectangle(pos=(gx, y + 45), size=(16, 8))

            if self.gun_flash > 0:
                flash_x = gx + (16 if facing > 0 else 0)
                Color(1, 0.85, 0.3, 0.9)
                Triangle(points=[flash_x, y + 49, flash_x + 14 * facing, y + 55, flash_x + 14 * facing, y + 43])

    def _draw_player_bullets(self):
        Color(1, 0.9, 0.4, 1)
        r = self.BULLET_RADIUS
        for atk in self.player_bullets:
            x = self.w2s(atk["x"])
            Ellipse(pos=(x - r, atk["y"] - r), size=(r * 2, r * 2))

    def _draw_ui(self):
        # Pip HP (mask) di kiri atas
        pip_size = 22
        gap = 8
        for i in range(self.MAX_MASKS):
            px = 20 + i * (pip_size + gap)
            py = self.height - 44
            if i < self.masks:
                Color(0.9, 0.95, 1, 1)
            else:
                Color(0.25, 0.25, 0.3, 1)
            RoundedRectangle(pos=(px, py), size=(pip_size, pip_size), radius=[5])
            Color(1, 1, 1, 0.25)
            Line(rounded_rectangle=(px, py, pip_size, pip_size, 5), width=1.2)

        # Cooldown dash
        bar_y = self.height - 70
        Color(0.2, 0.2, 0.2, 1)
        Rectangle(pos=(20, bar_y), size=(100, 8))
        dash_ready = 1 - max(0, self.dash_cooldown) / self.DASH_COOLDOWN
        Color(0.5, 0.85, 1, 1)
        Rectangle(pos=(20, bar_y), size=(100 * dash_ready, 8))

    def _draw_map(self):
        panel_w, panel_h = min(560, self.width - 60), 340
        px = (self.width - panel_w) / 2
        py = (self.height - panel_h) / 2

        Color(0.06, 0.06, 0.1, 0.95)
        RoundedRectangle(pos=(px, py), size=(panel_w, panel_h), radius=[18])
        Color(1, 1, 1, 0.15)
        Line(rounded_rectangle=(px, py, panel_w, panel_h, 18), width=1.5)

        n = len(self.room_order)
        spacing = panel_w / (n + 1)
        cy = py + panel_h / 2 + 20

        for i, rid in enumerate(self.room_order):
            cx = px + spacing * (i + 1)
            is_here = rid == self.current_room
            is_boss = self.rooms[rid].get("boss", False)

            if is_here:
                Color(1, 0.85, 0.3, 1)
            elif is_boss:
                Color(0.8, 0.25, 0.25, 1)
            else:
                Color(0.55, 0.6, 0.8, 1)

            Ellipse(pos=(cx - 12, cy - 12), size=(24, 24))

            if i < n - 1:
                Color(0.4, 0.4, 0.5, 0.6)
                Line(points=[cx + 12, cy, cx + spacing - 12, cy], width=2)

    def _layout_ui(self):
        self.left_button.pos = (20, 20)
        self.right_button.pos = (145, 20)

        gap = 15
        row_gap = 12
        bottom_y = 20
        top_y = bottom_y + 95 + row_gap

        self.gun_button.pos = (self.width - self.gun_button.width - 20, bottom_y)
        self.melee_button.pos = (self.gun_button.x - gap - self.melee_button.width, bottom_y)
        self.dash_button.pos = (self.width - self.dash_button.width - 20, top_y)
        self.jump_button.pos = (self.dash_button.x - gap - self.jump_button.width, top_y)

        self.map_button.pos = (self.width - self.map_button.width - 20, self.height - 70)

        self.room_label.pos = (self.width / 2 - 200, self.height - 34)
        self.notice_label.pos = (self.width / 2 - 250, self.height - 100)

        self.status_label.center = (self.width / 2, self.height / 2 + 40)
        self.retry_button.pos = (self.width / 2 - 110, self.height / 2 - 60)

        self.map_close_button.pos = (self.width / 2 - 90, self.height / 2 - 170)

    def on_size(self, *args):
        self._layout_ui()
