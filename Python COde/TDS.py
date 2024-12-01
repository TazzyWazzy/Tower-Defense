import pygame
import random

# Initialize Pygame
pygame.init()

# Screen Dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tower Defense Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (169, 169, 169)

# FPS
clock = pygame.time.Clock()
FPS = 60

# Load Assets
try:
    background_image = pygame.image.load("assets/background.webp").convert()
    enemy_image = pygame.image.load("assets/enemy.png").convert_alpha()
    bullet_image = pygame.image.load("assets/bullet.png").convert_alpha()  # Bullet image
    scout_icon = pygame.transform.scale(pygame.image.load("assets/scout.png").convert_alpha(), (50, 50))
    soldier_icon = pygame.transform.scale(pygame.image.load("assets/soldier.png").convert_alpha(), (50, 50))
    sniper_icon = pygame.transform.scale(pygame.image.load("assets/sniper.png").convert_alpha(), (50, 50))
    minigunner_icon = pygame.transform.scale(pygame.image.load("assets/minigunner.png").convert_alpha(), (50, 50))
    print("All assets loaded successfully!")
except pygame.error as e:
    print(f"Error loading assets: {e}")
    pygame.quit()

# --- Classes ---
class Bullet:
    def __init__(self, x, y, target_x, target_y, damage, speed):
        self.x = x
        self.y = y
        self.damage = damage
        self.speed = speed
        self.target_x = target_x
        self.target_y = target_y
        self.image = pygame.transform.scale(bullet_image, (10, 10))
        self.angle = pygame.math.Vector2(target_x - x, target_y - y).angle_to(pygame.math.Vector2(1, 0))
    
    def move(self):
        dx = self.speed * pygame.math.cos(self.angle)
        dy = self.speed * pygame.math.sin(self.angle)
        self.x += dx
        self.y += dy

    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))

class Character:
    def __init__(self, name, damage, range_, cost, attack_speed, icon, upgrade_cost):
        self.name = name
        self.damage = damage
        self.range = range_
        self.cost = cost
        self.attack_speed = attack_speed
        self.icon = icon
        self.upgrade_cost = upgrade_cost
        self.x, self.y = None, None
        self.target = None
        self.last_attack_time = 0
        self.bullets = []

    def draw(self, surface):
        if self.x is not None and self.y is not None:
            pygame.draw.circle(surface, GRAY, (self.x, self.y), self.range, 1)  # Range indicator
            surface.blit(self.icon, (self.x - 25, self.y - 25))

        # Draw bullets
        for bullet in self.bullets:
            bullet.move()
            bullet.draw(surface)

    def attack(self, enemies, current_time):
        if self.target and (current_time - self.last_attack_time) > self.attack_speed:
            if self.in_range(self.target):
                bullet = Bullet(self.x, self.y, self.target.x, self.target.y, self.damage, 5)
                self.bullets.append(bullet)
                self.last_attack_time = current_time

    def in_range(self, enemy):
        if not enemy:
            return False
        dist = ((self.x - enemy.x) ** 2 + (self.y - enemy.y) ** 2) ** 0.5
        return dist <= self.range

    def upgrade(self, player):
        if player.money >= self.upgrade_cost:
            player.money -= self.upgrade_cost
            self.damage += 5
            self.range += 10
            self.attack_speed -= 100

class Enemy:
    def __init__(self, path, health, speed):
        self.path = path
        self.health = health
        self.speed = speed
        self.current_point = 0
        self.x, self.y = self.path[0]
        self.image = pygame.transform.scale(enemy_image, (40, 40))

    def move(self):
        if self.current_point < len(self.path) - 1:
            target_x, target_y = self.path[self.current_point + 1]
            dx, dy = target_x - self.x, target_y - self.y
            distance = (dx**2 + dy**2)**0.5
            if distance < self.speed:
                self.current_point += 1
                self.x, self.y = self.path[self.current_point]
            else:
                self.x += dx / distance * self.speed
                self.y += dy / distance * self.speed

    def draw(self, surface):
        surface.blit(self.image, (self.x - 20, self.y - 20))  # Center enemy image
        # Health Bar
        pygame.draw.rect(surface, RED, (self.x - 20, self.y - 30, 40, 5))  # Red bar (background)
        pygame.draw.rect(surface, GREEN, (self.x - 20, self.y - 30, 40 * (self.health / 100), 5))  # Green bar (health)

class Player:
    def __init__(self, money):
        self.money = money
        self.selected_character = None
        self.towers = []

    def place_tower(self, x, y):
        if self.selected_character and self.money >= self.selected_character.cost:
            if not self.is_occupied(x, y):  # Check for collisions
                new_tower = Character(
                    self.selected_character.name,
                    self.selected_character.damage,
                    self.selected_character.range,
                    self.selected_character.cost,
                    self.selected_character.attack_speed,
                    self.selected_character.icon,
                    self.selected_character.upgrade_cost
                )
                new_tower.x, new_tower.y = x, y
                self.towers.append(new_tower)
                self.money -= self.selected_character.cost

    def is_occupied(self, x, y):
        for tower in self.towers:
            if abs(tower.x - x) < 50 and abs(tower.y - y) < 50:
                return True
        return False

class GameMap:
    def __init__(self):
        self.path = [
            (50, 500), (200, 500), (200, 300), (400, 300),
            (400, 600), (600, 600), (600, 200), (800, 200),
            (800, 400), (950, 400)
        ]

    def draw(self, surface):
        surface.blit(background_image, (0, 0))
        # Draw the path
        for i in range(len(self.path) - 1):
            pygame.draw.line(surface, BLACK, self.path[i], self.path[i + 1], 3)

# --- Main Function ---
def main():
    running = True
    game_map = GameMap()
    player = Player(money=300)
    wave = 1
    wave_timer = pygame.time.get_ticks()
    enemies = []

    # Character Options
    characters = [
        Character("Scout", 5, 100, 50, 1000, scout_icon, 100),
        Character("Soldier", 10, 120, 80, 1200, soldier_icon, 150),
        Character("Sniper", 20, 200, 150, 2000, sniper_icon, 200),
        Character("Minigunner", 15, 150, 200, 800, minigunner_icon, 250),
    ]

    while running:
        screen.fill(WHITE)
        game_map.draw(screen)

        # Draw UI
        pygame.draw.rect(screen, BLACK, (0, 700, SCREEN_WIDTH, 68))
        for i, char in enumerate(characters):
            screen.blit(char.icon, (10 + i * 70, 710))
            pygame.draw.rect(screen, WHITE, (10 + i * 70, 710, 50, 50), 2)

        # Display Money
        font = pygame.font.SysFont(None, 36)
        money_text = font.render(f"Money: ${player.money}", True, WHITE)
        screen.blit(money_text, (850, 710))

        # Handle Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if y < 700:  # Map area
                    player.place_tower(x, y)
                else:  # Bottom UI
                    for i, char in enumerate(characters):
                        if 10 + i * 70 < x < 60 + i * 70 and 710 < y < 760:
                            player.selected_character = char

        # Spawn new waves
        if len(enemies) == 0 and wave <= 20:
            wave_timer = pygame.time.get_ticks()
            for _ in range(wave * 4):  # Increased enemies per wave
                enemies.append(Enemy(game_map.path, 50 + wave * 10, 0.5 + wave * 0.01))  # Slower enemies
            wave += 1

        # Move and draw enemies
        for enemy in enemies:
            enemy.move()
            enemy.draw(screen)

        # Draw and attack with towers
        for tower in player.towers:
            tower.draw(screen)
            tower.attack(enemies, pygame.time.get_ticks())

        # Draw upgrades for towers
        for tower in player.towers:
            if pygame.mouse.get_pressed()[0]:
                tower.upgrade(player)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()


