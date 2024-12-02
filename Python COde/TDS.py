import pygame
import random

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tower Defense Game")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARK_BLUE = (50, 50, 100)

clock = pygame.time.Clock()
FPS = 60

try:
    background_image = pygame.image.load("assets/background.webp").convert()
    enemy_image = pygame.image.load("assets/enemy.png").convert_alpha()
    bullet_image = pygame.image.load("assets/bullet.png").convert_alpha()
    scout_icon = pygame.image.load("assets/scout.png").convert_alpha()
    soldier_icon = pygame.image.load("assets/soldier.png").convert_alpha()
    sniper_icon = pygame.image.load("assets/sniper.png").convert_alpha()
    minigunner_icon = pygame.image.load("assets/minigunner.png").convert_alpha()
except pygame.error as e:
    print(f"Error loading assets: {e}")
    pygame.quit()

# --- Classes ---
class Bullet:
    def __init__(self, x, y, target, damage, speed):
        self.x = x
        self.y = y
        self.damage = damage
        self.speed = speed
        self.target = target
        self.image = pygame.transform.scale(bullet_image, (10, 10))

        direction = pygame.math.Vector2(target.x - x, target.y - y).normalize()
        self.dx = direction.x * speed
        self.dy = direction.y * speed

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, surface):
        surface.blit(self.image, (self.x - 5, self.y - 5))

    def check_collision(self):
        if self.target:
            distance = ((self.x - self.target.x) ** 2 + (self.y - self.target.y) ** 2) ** 0.5
            if distance < 15:  
                self.target.health -= self.damage
                return True
        return False


class Character:
    def __init__(self, name, damage, range_, cost, attack_speed, icon, upgrade_cost):
        self.name = name
        self.damage = damage
        self.range = range_
        self.cost = cost
        self.attack_speed = attack_speed
        self.icon = pygame.transform.scale(icon, (50, 50))
        self.upgrade_cost = upgrade_cost
        self.level = 1
        self.x, self.y = None, None
        self.last_attack_time = 0
        self.bullets = []

    def draw(self, surface):
        if self.x is not None and self.y is not None:
            pygame.draw.circle(surface, WHITE, (self.x, self.y), self.range, 1)
            surface.blit(self.icon, (self.x - 25, self.y - 25))
        for bullet in self.bullets:
            bullet.move()
            if bullet.check_collision():
                self.bullets.remove(bullet) 
            else:
                bullet.draw(surface)

    def attack(self, enemies, current_time):
        if current_time - self.last_attack_time >= self.attack_speed:
            for enemy in enemies:
                if self.in_range(enemy):
                    bullet = Bullet(self.x, self.y, enemy, self.damage, 5)
                    self.bullets.append(bullet)
                    self.last_attack_time = current_time
                    break

    def in_range(self, enemy):
        distance = ((self.x - enemy.x) ** 2 + (self.y - enemy.y) ** 2) ** 0.5
        return distance <= self.range

    def upgrade(self):
        self.level += 1
        self.damage += 5
        self.range += 20
        self.upgrade_cost += 50


class Enemy:
    def __init__(self, path, health, speed):
        self.path = path
        self.health = health
        self.max_health = health
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
            else:
                self.x += dx / distance * self.speed
                self.y += dy / distance * self.speed

    def draw(self, surface):
        surface.blit(self.image, (self.x - 20, self.y - 20))
        health_bar_width = 30
        pygame.draw.rect(surface, RED, (self.x - 15, self.y - 30, health_bar_width, 5))
        current_health_width = health_bar_width * (self.health / self.max_health)
        pygame.draw.rect(surface, GREEN, (self.x - 15, self.y - 30, current_health_width, 5))


class Player:
    def __init__(self, money):
        self.money = money
        self.health = 100
        self.selected_character = None
        self.towers = []

    def place_tower(self, x, y):
        if self.selected_character and self.money >= self.selected_character.cost:
            new_character = Character(
                self.selected_character.name,
                self.selected_character.damage,
                self.selected_character.range,
                self.selected_character.cost,
                self.selected_character.attack_speed,
                self.selected_character.icon,
                self.selected_character.upgrade_cost,
            )
            new_character.x, new_character.y = x, y
            self.towers.append(new_character)
            self.money -= new_character.cost
            self.selected_character = None

    def upgrade_tower(self, tower):
        if self.money >= tower.upgrade_cost:
            tower.upgrade()
            self.money -= tower.upgrade_cost


class GameMap:
    def __init__(self):
        self.path = [
            (100, 700), (250, 700), (250, 600), (350, 600),
            (350, 400), (600, 400), (600, 300), (750, 300),
            (750, 100), (600, 100), (450, 200), (300, 200),
            (150, 100), (100, 100)
        ]

    def draw(self, surface):
        surface.blit(background_image, (0, 0))
        for i in range(len(self.path) - 1):
            pygame.draw.line(surface, BLACK, self.path[i], self.path[i + 1], 5)


# --- Functions ---
def draw_unit_panel():
    panel_rect = pygame.Rect(SCREEN_WIDTH - 200, 0, 200, SCREEN_HEIGHT)
    pygame.draw.rect(screen, DARK_BLUE, panel_rect)

    y_offset = 50
    for char in characters:
        screen.blit(char.icon, (SCREEN_WIDTH - 150, y_offset))
        cost_text = pygame.font.Font(None, 24).render(f"${char.cost}", True, WHITE)
        screen.blit(cost_text, (SCREEN_WIDTH - 120, y_offset + 60))
        y_offset += 120

    money_text = pygame.font.Font(None, 30).render(f"Money: ${player.money}", True, WHITE)
    screen.blit(money_text, (SCREEN_WIDTH - 180, SCREEN_HEIGHT - 50))


def draw_hp_and_wave():
    bar_width = 400
    bar_height = 30
    x = (SCREEN_WIDTH - bar_width) // 2
    y = 20

    pygame.draw.rect(screen, RED, (x, y, bar_width, bar_height))
    current_hp_width = int(player.health / 100 * bar_width)
    pygame.draw.rect(screen, GREEN, (x, y, current_hp_width, bar_height))

    hp_text = pygame.font.Font(None, 36).render(f"Base HP: {player.health}", True, WHITE)
    screen.blit(hp_text, (x + bar_width // 2 - hp_text.get_width() // 2, y + 5))

    wave_text = pygame.font.Font(None, 36).render(f"Wave: {wave}/{max_wave}", True, WHITE)
    screen.blit(wave_text, (x + bar_width // 2 - wave_text.get_width() // 2, y + 40))


# --- Initialization ---
player = Player(money=500)
game_map = GameMap()

characters = [
    Character("Scout", damage=5, range_=100, cost=50, attack_speed=1000, icon=scout_icon, upgrade_cost=50),
    Character("Soldier", damage=10, range_=150, cost=100, attack_speed=1500, icon=soldier_icon, upgrade_cost=75),
    Character("Sniper", damage=20, range_=300, cost=200, attack_speed=2000, icon=sniper_icon, upgrade_cost=100),
    Character("Minigunner", damage=50, range_=200, cost=400, attack_speed=300, icon=minigunner_icon, upgrade_cost=150),
]

enemies = []
enemy_spawn_timer = 0
spawn_interval = 2500  
wave = 0
max_wave = 20
enemies_per_wave = 5 + wave  
enemies_spawned_this_wave = 0

# --- Main Game Loop ---
running = True
while running:
    screen.fill(BLACK)
    game_map.draw(screen)

    current_time = pygame.time.get_ticks()
    if (
        current_time - enemy_spawn_timer > spawn_interval
        and enemies_spawned_this_wave < enemies_per_wave
        and wave <= max_wave
    ):
        enemy_spawn_timer = current_time
        enemies.append(Enemy(game_map.path, health=100 + wave * 10, speed=0.5 + wave * 0.05))
        enemies_spawned_this_wave += 1

    if enemies_spawned_this_wave >= enemies_per_wave and not enemies:
        wave += 1
        enemies_spawned_this_wave = 0
        player.money += wave * 50 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if mouse_x > SCREEN_WIDTH - 200:  
                for i, char in enumerate(characters):
                    if mouse_y in range(50 + i * 120, 50 + (i + 1) * 120):
                        player.selected_character = char
                        break
            else:  # Placing a character
                player.place_tower(mouse_x, mouse_y)

    # Enemy Movement
    for enemy in enemies[:]:
        enemy.move()
        enemy.draw(screen)
        if enemy.current_point == len(game_map.path) - 1:
            player.health -= 10
            enemies.remove(enemy)
        elif enemy.health <= 0:
            enemies.remove(enemy)

    for tower in player.towers:
        tower.attack(enemies, current_time)
        tower.draw(screen)

    draw_unit_panel()
    draw_hp_and_wave()

    # Check Game Over
    if player.health <= 0 or wave > max_wave:
        running = False

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
