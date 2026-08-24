from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.core.window import Window
import random


class DarkKnightGame(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # =========================
        # PLAYER
        # =========================
        self.player_x = 100
        self.player_y = 80

        self.player_vx = 0
        self.player_vy = 0

        self.player_speed = 300
        self.jump_power = 650
        self.gravity = 1800

        self.is_grounded = True

        # =========================
        # BOSS
        # =========================
        self.boss_hp = 100
        self.boss_max_hp = 100

        self.boss_x = 700
        self.boss_y = 150

        self.boss_bullets = []
        self.boss_timer = 0

        # =========================
        # PLAYER ATTACK
        # =========================
        self.player_attacks = []
        self.attack_cooldown = 0

        # =========================
        # TOUCH CONTROL
        # =========================
        self.move_left = False
        self.move_right = False

        self.create_controls()

        Window.bind(on_key_down=self._on_key_down)
        Window.bind(on_key_up=self._on_key_up)

        Clock.schedule_interval(self.update, 1 / 60)

    # =========================================================
    # TOUCH CONTROLS
    # =========================================================

    def create_controls(self):

        self.left_button = Button(
            text="<",
            font_size=32,
            size_hint=(None, None),
            size=(90, 90),
            opacity=0.75
        )

        self.right_button = Button(
            text=">",
            font_size=32,
            size_hint=(None, None),
            size=(90, 90),
            opacity=0.75
        )

        self.jump_button = Button(
            text="JUMP",
            font_size=20,
            size_hint=(None, None),
            size=(120, 90),
            opacity=0.75
        )

        self.attack_button = Button(
            text="ATTACK",
            font_size=18,
            size_hint=(None, None),
            size=(130, 90),
            opacity=0.75
        )

        self.add_widget(self.left_button)
        self.add_widget(self.right_button)
        self.add_widget(self.jump_button)
        self.add_widget(self.attack_button)

        self.left_button.bind(
            on_press=lambda *_: self.set_left(True)
        )
        self.left_button.bind(
            on_release=lambda *_: self.set_left(False)
        )

        self.right_button.bind(
            on_press=lambda *_: self.set_right(True)
        )
        self.right_button.bind(
            on_release=lambda *_: self.set_right(False)
        )

        self.jump_button.bind(
            on_press=lambda *_: self.jump()
        )

        self.attack_button.bind(
            on_press=lambda *_: self.attack()
        )

    def set_left(self, value):
        self.move_left = value

    def set_right(self, value):
        self.move_right = value

    # =========================================================
    # KEYBOARD
    # =========================================================

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]

        if key in ("left", "a"):
            self.move_left = True

        elif key in ("right", "d"):
            self.move_right = True

        elif key in ("spacebar", "up", "w"):
            self.jump()

        elif key in ("x", "j", "enter"):
            self.attack()

        return True

    def _on_key_up(self, keyboard, keycode):
        key = keycode[1]

        if key in ("left", "a"):
            self.move_left = False

        elif key in ("right", "d"):
            self.move_right = False

        return True

    # =========================================================
    # PLAYER ACTION
    # =========================================================

    def jump(self):

        if self.is_grounded:
            self.player_vy = self.jump_power
            self.is_grounded = False

    def attack(self):

        if self.attack_cooldown > 0:
            return

        # Proyektil pemain
        direction = 1

        self.player_attacks.append({
            "x": self.player_x + 55,
            "y": self.player_y + 45,
            "vx": 800 * direction
        })

        self.attack_cooldown = 0.35

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):

        # -------------------------
        # PLAYER MOVEMENT
        # -------------------------

        self.player_vx = 0

        if self.move_left:
            self.player_vx -= self.player_speed

        if self.move_right:
            self.player_vx += self.player_speed

        self.player_x += self.player_vx * dt

        # Batas arena
        max_x = max(0, self.width - 80)

        if self.player_x < 0:
            self.player_x = 0

        if self.player_x > max_x:
            self.player_x = max_x

        # -------------------------
        # GRAVITY
        # -------------------------

        self.player_y += self.player_vy * dt
        self.player_vy -= self.gravity * dt

        floor_y = 80

        if self.player_y <= floor_y:
            self.player_y = floor_y
            self.player_vy = 0
            self.is_grounded = True

        # -------------------------
        # ATTACK COOLDOWN
        # -------------------------

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        # -------------------------
        # PLAYER PROJECTILES
        # -------------------------

        for attack in self.player_attacks[:]:

            attack["x"] += attack["vx"] * dt

            # Hit boss
            if (
                attack["x"] > self.boss_x
                and attack["x"] < self.boss_x + 100
                and attack["y"] > self.boss_y
                and attack["y"] < self.boss_y + 140
            ):

                self.boss_hp -= 5
                self.player_attacks.remove(attack)

                if self.boss_hp < 0:
                    self.boss_hp = 0

            elif attack["x"] > self.width + 100:
                self.player_attacks.remove(attack)

        # -------------------------
        # BOSS ATTACK
        # -------------------------

        self.boss_timer += dt

        if self.boss_timer >= 1.2:

            self.boss_timer = 0

            self.boss_bullets.append({
                "x": self.boss_x,
                "y": self.boss_y + 60,
                "vx": -450,
                "vy": random.uniform(-80, 80)
            })

        # -------------------------
        # BOSS BULLETS
        # -------------------------

        for bullet in self.boss_bullets[:]:

            bullet["x"] += bullet["vx"] * dt
            bullet["y"] += bullet["vy"] * dt

            # Player hitbox
            if (
                bullet["x"] < self.player_x + 60
                and bullet["x"] + 25 > self.player_x
                and bullet["y"] < self.player_y + 90
                and bullet["y"] + 25 > self.player_y
            ):

                self.boss_bullets.remove(bullet)

            elif bullet["x"] < -100:
                self.boss_bullets.remove(bullet)

        self.draw_game()

    # =========================================================
    # DRAW
    # =========================================================

    def draw_game(self):

        self.canvas.clear()

        with self.canvas:

            # Background
            Color(0.02, 0.02, 0.06, 1)

            Rectangle(
                pos=(0, 0),
                size=(self.width, self.height)
            )

            # Moon / light
            Color(0.85, 0.9, 1, 1)

            Ellipse(
                pos=(self.width - 180, self.height - 180),
                size=(100, 100)
            )

            # Arena floor
            Color(0.12, 0.12, 0.18, 1)

            Rectangle(
                pos=(0, 0),
                size=(self.width, 80)
            )

            # Player
            Color(0.12, 0.12, 0.16, 1)

            Rectangle(
                pos=(self.player_x, self.player_y),
                size=(60, 90)
            )

            # Player mask glow
            Color(0.8, 0.85, 1, 1)

            Ellipse(
                pos=(
                    self.player_x + 10,
                    self.player_y + 55
                ),
                size=(40, 40)
            )

            # Boss
            if self.boss_hp > 0:

                Color(1, 0.25, 0.15, 1)

                Rectangle(
                    pos=(self.boss_x, self.boss_y),
                    size=(100, 140)
                )

                # Boss glow
                Color(1, 0.8, 0.2, 1)

                Ellipse(
                    pos=(
                        self.boss_x + 25,
                        self.boss_y + 80
                    ),
                    size=(50, 50)
                )

            # Player attacks
            Color(0.4, 0.9, 1, 1)

            for attack in self.player_attacks:

                Ellipse(
                    pos=(attack["x"], attack["y"]),
                    size=(25, 25)
                )

            # Boss bullets
            Color(1, 0.8, 0.2, 1)

            for bullet in self.boss_bullets:

                Ellipse(
                    pos=(bullet["x"], bullet["y"]),
                    size=(25, 25)
                )

            # Boss HP bar background
            Color(0.15, 0.15, 0.15, 1)

            Rectangle(
                pos=(self.boss_x, self.boss_y + 155),
                size=(100, 12)
            )

            # Boss HP
            Color(1, 0.1, 0.1, 1)

            Rectangle(
                pos=(self.boss_x, self.boss_y + 155),
                size=(
                    100 * (self.boss_hp / self.boss_max_hp),
                    12
                )
            )

    # =========================================================
    # RESIZE
    # =========================================================

    def on_size(self, *args):

        if hasattr(self, "left_button"):

            self.left_button.pos = (
                20,
                20
            )

            self.right_button.pos = (
                120,
                20
            )

            self.jump_button.pos = (
                self.width - 270,
                20
            )

            self.attack_button.pos = (
                self.width - 135,
                20
            )
