import pygame
import sys

# Inisialisasi Pygame
pygame.init()

# Konfigurasi Layar (Resolusi 2D)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Kisah Kesatria Penghianatan (Revenge)")

clock = pygame.time.Clock()

# Warna (Simulasi Grafis Sederhana ala Metroidvania / Hollow Knight)
BG_COLOR = (15, 15, 20)       # Nuansa gelap kelam
PLAYER_COLOR = (200, 50, 50)  # Merah menyala (kesatria penuh dendam)
GROUND_COLOR = (50, 50, 70)   # Warna tanah pijakan
ENEMY_COLOR = (100, 100, 100) # Musuh pengkhianat kerajaan

# Properti Pemain (Kesatria)
player_x = 100
player_y = 400
player_width = 40
player_height = 60
player_vel_y = 0
is_jumping = False
gravity = 0.8
jump_strength = -14
speed = 5

# Loop Utama Game
running = True
while running:
    screen.fill(BG_COLOR)

    # 1. Tangkap Kontrol / Input Tombol (Keyboard HP / Termux-X11)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not is_jumping:
                player_vel_y = jump_strength
                is_jumping = True

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_x -= speed
    if keys[pygame.K_RIGHT]:
        player_x += speed

    # 2. Fisika Lompat & Gravitasi
    player_vel_y += gravity
    player_y += player_vel_y

    # Batas Lantai Tanah
    floor_level = 480 - player_height
    if player_y >= floor_level:
        player_y = floor_level
        player_vel_y = 0
        is_jumping = False

    # 3. Gambar Elemen Game ke Layar
    # Gambar Lantai
    pygame.draw.rect(screen, GROUND_COLOR, (0, 480, SCREEN_WIDTH, 120))
    
    # Gambar Kesatria (Kotak Merah Penuh Dendam)
    pygame.draw.rect(screen, PLAYER_COLOR, (player_x, player_y, player_width, player_height))
    
    # Gambar Bayangan Musuh Pengkhianat di Sebelah Kanan
    pygame.draw.rect(screen, ENEMY_COLOR, (600, 420, 40, 60))

    # Tampilkan teks narasi di atas layar
    font = pygame.font.SysFont(None, 24)
    narasi = font.render("Misi: Balas dendam pada kerajaan yang mengkhianati...", True, (150, 150, 150))
    screen.blit(narasi, (50, 30))

    pygame.display.flip()
    clock.tick(60)
