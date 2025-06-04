import pygame
import sys
import hashlib
import os
import uuid
import json
from pygame.locals import *

# Constants
SCREEN_WIDTH = 448
SCREEN_HEIGHT = 496
FPS = 60
CELL_SIZE = 16

USER_DB_FILE = "users.json"

# Colors
BLACK = (0, 0, 0)
NAVY = (0, 0, 128)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)
CYAN = (0, 255, 255)
GREEN = (0, 255, 0)
GREY = (128, 128, 128)

# Maze Layout (28x31) - 0 empty, 1 wall, 2 dot, 3 power pellet
MAZE_LAYOUT = [
    "1111111111111111111111111111",
    "1222222222221112222222222221",
    "1211112111121112111112111121",
    "1211112111121112111112111121",
    "1222222222222222222222222221",
    "1111112111111111111112111111",
    "1000022111111111111122000001",
    "1011122222221112222222221101",
    "1011111111121112111111111101",
    "1222222222222222222222222221",
    "1211112111111111111112111121",
    "1211112111111111111112111121",
    "1222222222221112222222222221",
    "1111111111111111111111111111",
    "1000000000001111000000000001",
    "1011111111101110111111111101",
    "1011111111101110111111111101",
    "1222222222221112222222222221",
    "1211112111121112111112111121",
    "1211112111121112111112111121",
    "1222222222222222222222222221",
    "1111112111111111111112111111",
    "1000022111111111111122000001",
    "1011122222221112222222221101",
    "1011111111121112111111111101",
    "1222222222222222222222222221",
    "1111111111111111111111111111",
    "                            ",
    "                            ",
    "                            ",
    "                            ",
]

MAZE_WIDTH = 28
MAZE_HEIGHT = 31

# Helper functions for user data

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'r') as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_users(users):
    with open(USER_DB_FILE, 'w') as f:
        json.dump(users, f)

# Authentication system

class Auth:
    def __init__(self):
        self.users = load_users()
        self.token = None
        self.current_user = None

    def register(self, username, password):
        if username in self.users:
            return False, "Kullanıcı zaten var."
        self.users[username] = hash_password(password)
        save_users(self.users)
        return True, "Kayıt başarılı."

    def login(self, username, password):
        if username not in self.users:
            return False, "Kullanıcı bulunamadı."
        if self.users[username] != hash_password(password):
            return False, "Şifre yanlış."
        self.token = str(uuid.uuid4())
        self.current_user = username
        return True, "Giriş başarılı."

    def is_authenticated(self):
        return self.token is not None

# Game Objects

class Wall(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.image.fill(NAVY)
        self.rect = self.image.get_rect(topleft=pos)

class Dot(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((4, 4))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(pos[0]+CELL_SIZE//2, pos[1]+CELL_SIZE//2))

class PowerPellet(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill(WHITE)
        pygame.draw.circle(self.image, ORANGE, (4,4), 4)
        self.rect = self.image.get_rect(center=(pos[0]+CELL_SIZE//2, pos[1]+CELL_SIZE//2))

class Pacman(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.size = 10  # Küçük Pacman
        self.images = {
            'LEFT': pygame.Surface((self.size, self.size), pygame.SRCALPHA),
            'RIGHT': pygame.Surface((self.size, self.size), pygame.SRCALPHA),
            'UP': pygame.Surface((self.size, self.size), pygame.SRCALPHA),
            'DOWN': pygame.Surface((self.size, self.size), pygame.SRCALPHA),
        }
        for im in self.images.values():
            im.fill((0, 0, 0, 0))
            pygame.draw.circle(im, YELLOW, (self.size//2, self.size//2), self.size//2)
        self.image = self.images['LEFT']
        self.rect = self.image.get_rect(center=(pos[0]+CELL_SIZE//2, pos[1]+CELL_SIZE//2))
        self.direction = pygame.Vector2(0, 0)
        self.next_direction = pygame.Vector2(0, 0)
        self.speed = CELL_SIZE  # Kare kare gitmesi için hız CELL_SIZE olmalı

    def update(self, walls):
        # Kare merkezindeysek yön değiştir
        if (self.rect.centerx - CELL_SIZE//2) % CELL_SIZE == 0 and (self.rect.centery - CELL_SIZE//2) % CELL_SIZE == 0:
            if self.next_direction.length_squared() > 0:
                new_rect = self.rect.move(self.next_direction.x * CELL_SIZE, self.next_direction.y * CELL_SIZE)
                if not any(new_rect.colliderect(w.rect) for w in walls):
                    self.direction = self.next_direction
            # İleriye hareket mümkün mü?
            new_rect = self.rect.move(self.direction.x * CELL_SIZE, self.direction.y * CELL_SIZE)
            if any(new_rect.colliderect(w.rect) for w in walls):
                self.direction = pygame.Vector2(0, 0)
        # Hareket et
        self.rect = self.rect.move(self.direction.x, self.direction.y)

        # Yön görseli
        if self.direction.x > 0:
            self.image = self.images['RIGHT']
        elif self.direction.x < 0:
            self.image = self.images['LEFT']
        elif self.direction.y < 0:
            self.image = self.images['UP']
        elif self.direction.y > 0:
            self.image = self.images['DOWN']

class Ghost(pygame.sprite.Sprite):
    COLORS = [RED, PINK, CYAN, ORANGE]
    def __init__(self, pos, color_index=0):
        super().__init__()
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.color = Ghost.COLORS[color_index % len(Ghost.COLORS)]
        self.image.fill(self.color)
        self.rect = self.image.get_rect(topleft=pos)
        self.speed = 1
        self.direction = pygame.Vector2(1, 0)

    def update(self, walls):
        # Simple AI: Move in the current direction until hitting a wall, then turn randomly
        new_pos = self.rect.move(self.direction.x * self.speed, self.direction.y * self.speed)
        if any(new_pos.colliderect(w.rect) for w in walls):
            # change direction clockwise (right -> down -> left -> up -> right ...)
            if self.direction.x == 1:
                self.direction = pygame.Vector2(0, 1)
            elif self.direction.y == 1:
                self.direction = pygame.Vector2(-1, 0)
            elif self.direction.x == -1:
                self.direction = pygame.Vector2(0, -1)
            elif self.direction.y == -1:
                self.direction = pygame.Vector2(1, 0)
            # recalculate new position after turn
            new_pos = self.rect.move(self.direction.x * self.speed, self.direction.y * self.speed)
            if any(new_pos.colliderect(w.rect) for w in walls):
                # if still blocked, reverse direction
                self.direction = -self.direction
        else:
            self.rect = new_pos

# Main game class

class PacmanGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Labirentten Kacis")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 20)
        self.running = True
        self.score = 0

        # Ses dosyalarını yükle
        pygame.mixer.init()
        self.eat_sound = pygame.mixer.Sound("eat.wav")
        self.power_sound = pygame.mixer.Sound("power.wav")

        self.walls = pygame.sprite.Group()
        self.dots = pygame.sprite.Group()
        self.power_pellets = pygame.sprite.Group()
        self.ghosts = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()

        self.load_maze()

        self.pacman = Pacman((CELL_SIZE * 13, CELL_SIZE * 23))
        self.all_sprites.add(self.pacman)

        # Create ghosts
        ghost_positions = [(CELL_SIZE * 13, CELL_SIZE * 11), (CELL_SIZE * 14, CELL_SIZE * 11), (CELL_SIZE * 12, CELL_SIZE * 11), (CELL_SIZE * 15, CELL_SIZE * 11)]
        for i, pos in enumerate(ghost_positions):
            ghost = Ghost(pos, i)
            self.ghosts.add(ghost)
            self.all_sprites.add(ghost)

        self.power_mode = False
        self.power_mode_timer = 0

    def load_maze(self):
        self.walls.empty()
        self.dots.empty()
        self.power_pellets.empty()
        for row_index, row in enumerate(MAZE_LAYOUT):
            for col_index, char in enumerate(row):
                x = col_index * CELL_SIZE
                y = row_index * CELL_SIZE
                if char == '1':
                    wall = Wall((x, y))
                    self.walls.add(wall)
                    self.all_sprites.add(wall)
                elif char == '2':
                    dot = Dot((x, y))
                    self.dots.add(dot)
                    self.all_sprites.add(dot)
                elif char == '3':
                    pellet = PowerPellet((x, y))
                    self.power_pellets.add(pellet)
                    self.all_sprites.add(pellet)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False

        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:
            self.pacman.next_direction = pygame.Vector2(-1, 0)
        elif keys[K_RIGHT]:
            self.pacman.next_direction = pygame.Vector2(1, 0)
        elif keys[K_UP]:
            self.pacman.next_direction = pygame.Vector2(0, -1)
        elif keys[K_DOWN]:
            self.pacman.next_direction = pygame.Vector2(0, 1)
        else:
            # no input - keep current direction
            pass

    def update(self):
        self.pacman.update(self.walls)
        self.ghosts.update(self.walls)

        # Check dot collisions
        dot_hit = pygame.sprite.spritecollideany(self.pacman, self.dots)
        if dot_hit:
            dot_hit.kill()
            self.score += 10
            self.eat_sound.play()  # Ses çal

        # Check power pellet collisions
        pellet_hit = pygame.sprite.spritecollideany(self.pacman, self.power_pellets)
        if pellet_hit:
            pellet_hit.kill()
            self.score += 50
            self.power_mode = True
            self.power_mode_timer = pygame.time.get_ticks()
            self.power_sound.play()  # Ses çal

        # Power mode expiration after 7 seconds
        if self.power_mode and pygame.time.get_ticks() - self.power_mode_timer > 7000:
            self.power_mode = False

        # Check ghost collisions
        ghost_hits = pygame.sprite.spritecollide(self.pacman, self.ghosts, False)
        for ghost in ghost_hits:
            if self.power_mode:
                ghost.rect.topleft = (CELL_SIZE * 13, CELL_SIZE * 11)  # send ghost back to start
                self.score += 200
            else:
                self.game_over()

        # Check win condition
        if len(self.dots) == 0 and len(self.power_pellets) == 0:
            self.win_game()

    def draw(self):
        self.screen.fill(BLACK)
        self.all_sprites.draw(self.screen)

        # Draw score
        score_text = self.font.render(f"Skor: {self.score}", True, WHITE)
        self.screen.blit(score_text, (8, SCREEN_HEIGHT - 30))

        # Draw power mode
        if self.power_mode:
            power_text = self.font.render("POWER MODE!", True, ORANGE)
            self.screen.blit(power_text, (SCREEN_WIDTH - 140, SCREEN_HEIGHT - 30))

        pygame.display.flip()

    def game_over(self):
        self.show_message("Oyun bitti! Kaybettiniz.")
        self.running = False

    def win_game(self):
        self.show_message(f"Tebrikler! Skorunuz: {self.score}")
        self.running = False

    def show_message(self, message):
        self.screen.fill(BLACK)
        text = self.font.render(message, True, WHITE)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, rect)
        pygame.display.flip()
        pygame.time.wait(3000)

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

# User interface for login and registration

def draw_text(surface, text, font, color, pos):
    text_obj = font.render(text, True, color)
    surface.blit(text_obj, pos)

def draw_button(surface, rect, text, font, color, hover_color, mouse_pos):
    if rect.collidepoint(mouse_pos):
        pygame.draw.rect(surface, hover_color, rect, border_radius=8)
    else:
        pygame.draw.rect(surface, color, rect, border_radius=8)
    text_surf = font.render(text, True, BLACK)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)

def input_box(screen, font, prompt, is_password=False):
    box_rect = pygame.Rect(100, 250, 250, 40)
    color_inactive = GREY
    color_active = WHITE
    color = color_inactive
    active = False
    user_text = ''
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if box_rect.collidepoint(event.pos):
                    active = True
                    color = color_active
                else:
                    active = False
                    color = color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        user_text = user_text[:-1]
                    else:
                        if len(user_text) < 20:
                            user_text += event.unicode

        screen.fill((30, 30, 30))
        draw_text(screen, prompt, font, WHITE, (box_rect.x, box_rect.y - 40))
        pygame.draw.rect(screen, color, box_rect, border_radius=8)
        display_text = '*' * len(user_text) if is_password else user_text
        txt_surface = font.render(display_text, True, BLACK)
        screen.blit(txt_surface, (box_rect.x + 10, box_rect.y + 8))
        pygame.display.flip()
    return user_text

def start_auth_screen():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Labirentten Kacis")
    font = pygame.font.SysFont('Arial', 28, bold=True)
    clock = pygame.time.Clock()

    auth = Auth()
    message = ""
    state = "CHOICE"

    # Butonlar
    button_login = pygame.Rect(100, 200, 250, 50)
    button_register = pygame.Rect(100, 270, 250, 50)
    button_quit = pygame.Rect(100, 340, 250, 50)

    while True:
        clock.tick(FPS)
        screen.fill((30, 30, 30))
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if state == "CHOICE" and event.type == pygame.MOUSEBUTTONDOWN:
                if button_login.collidepoint(event.pos):
                    state = "LOGIN"
                elif button_register.collidepoint(event.pos):
                    state = "REGISTER"
                elif button_quit.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        if state == "CHOICE":
            draw_text(screen, "Labirentten Kacis", font, ORANGE, (140, 100))
            draw_button(screen, button_login, "Giriş Yap", font, CYAN, WHITE, mouse_pos)
            draw_button(screen, button_register, "Kayıt Ol", font, GREEN, WHITE, mouse_pos)
            draw_button(screen, button_quit, "Çıkış", font, RED, WHITE, mouse_pos)
        elif state == "LOGIN":
            username = input_box(screen, font, "Kullanıcı Adı Giriniz:")
            password = input_box(screen, font, "Şifre Giriniz:", is_password=True)
            success, message = auth.login(username, password)
            if success:
                return auth
            else:
                state = "CHOICE"
                screen.fill((30, 30, 30))
                draw_text(screen, message, font, RED, (100, 420))
                pygame.display.flip()
                pygame.time.wait(2000)
        elif state == "REGISTER":
            username = input_box(screen, font, "Yeni Kullanıcı Adı Giriniz:")
            password = input_box(screen, font, "Yeni Şifre Giriniz:", is_password=True)
            success, message = auth.register(username, password)
            screen.fill((30, 30, 30))
            draw_text(screen, message, font, GREEN if success else RED, (100, 420))
            pygame.display.flip()
            pygame.time.wait(2000)
            state = "CHOICE"

        pygame.display.flip()

def main():
    auth = start_auth_screen()
    if auth.is_authenticated():
        game = PacmanGame()
        game.run()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
