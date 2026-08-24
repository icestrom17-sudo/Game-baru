from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.core.window import Window
import random

class DarkKnightGame(Widget):
    def __init__(self, **kwargs):
        super(DarkKnightGame, self).__init__(**kwargs)
        # Karakter: Dark Knight Bermasker
        self.player_x = 100
        self.player_y = 100
        self.player_vx = 0
        self.player_vy = 0
        self.is_grounded = False
        self.mask_glow = 1.0  # Efek visual topeng

        # Sistem Boss: 6 Kesatria Cahaya Pengkhianat (Bergiliran / Cuphead Style)
        self.boss_hp = 100
        self.boss_state = 1  # Mewakili salah satu dari 6 kesatria
        self.boss_x = 700
        self.boss_y = 150
        self.boss_bullets = []

        Window.bind(on_key_down=self._on_key_down)
        Clock.schedule_interval(self.update, 1.0 / 60.0)

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        # Mekanik Kontrol ala Hollow Knight (Lompat & Dash)
        if keycode[1] == 'spacebar' and self.is_grounded:
            self.player_vy = 14  # Lompatan tinggi
            self.is_grounded = False
        elif keycode[1] == 'left':
            self.player_x -= 20  # Dash/Gerak cepat ke kiri
        elif keycode[1] == 'right':
            self.player_x += 20  # Dash/Gerak cepat ke kanan
        return True

    def update(self, dt):
        # Gravitasi & Fisika Lompat
        self.player_y += self.player_vy
        self.player_vy -= 0.65  # Tarikan gravitasi

        # Lantai Arena Kerajaan Cahaya
        if self.player_y <= 80:
            self.player_y = 80
            self.player_vy = 0
            self.is_grounded = True

        # Pola Serangan Bos (Cuphead Style: Tembakan proyektil cahaya beruntun)
        if random.random() < 0.05:
            self.boss_bullets.append({'x': self.boss_x, 'y': self.boss_y + 40, 'vx': -8, 'vy': random.choice([-2, 0, 2])})

        for bullet in self.boss_bullets[:]:
            bullet['x'] += bullet['vx']
            bullet['y'] += bullet['vy']
            if bullet['x'] < 0:
                self.boss_bullets.remove(bullet)

        # Render Grafis ke Layar
        self.canvas.clear()
        with self.canvas:
            # 1. Background: Kastil Kerajaan Cahaya yang Gelap & Megah
            Color(0.03, 0.03, 0.08, 1)
            Rectangle(pos=(0, 0), size=(Window.width, Window.height))

            # 2. Lantai Kerajaan
            Color(0.15, 0.15, 0.2, 1)
            Rectangle(pos=(0, 0), size=(Window.width, 80))

            # 3. Render Dark Knight (Kesatria Berjubah Gelap & Topeng Pucat)
            Color(0.1, 0.1, 0.12, 1)
            Rectangle(pos=(self.player_x, self.player_y), size=(35, 55)) # Jubah
            # Topeng ikonik yang bersinar
            Color(0.9, 0.9, 1.0, 1)
            Ellipse(pos=(self.player_x + 20, self.player_y + 35), size=(12, 12))

            # 4. Render Boss: Salah satu dari 6 Kesatria Cahaya Pengkhianat
            Color(1.0, 0.8, 0.2, 1) # Cahaya menyilaukan khas musuh
            Rectangle(pos=(self.boss_x, self.boss_y), size=(60, 90))

            # 5. Render Proyektil Peluru Cahaya (Cuphead Bullet-Hell Style)
            Color(1, 1, 0.5, 1)
            for bullet in self.boss_bullets:
                Ellipse(pos=(bullet['x'], bullet['y']), size=(12, 12))
