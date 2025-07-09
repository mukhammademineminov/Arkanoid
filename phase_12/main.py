import pygame
import sys
import random
import math
from game_objects import Paddle, Ball, Brick, PowerUp, Laser, Particle, Firework

# -- General Setup --
pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()

# -- Screen Setup --
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("PyGame Arkanoid")

# -- Colors --
BG_COLOR = pygame.Color('grey12')
BRICK_COLORS = [(178, 34, 34), (255, 165, 0), (255, 215, 0), (50, 205, 50)]

# -- Font Setup --
# !!! PHASE: TITLE SCREEN !!!
title_font = pygame.font.Font(None, 70)
# !!! END PHASE: TITLE SCREEN !!!
game_font = pygame.font.Font(None, 40)
message_font = pygame.font.Font(None, 30)

# -- Sound Setup --
try:
    bounce_sound = pygame.mixer.Sound('bounce.wav')
    brick_break_sound = pygame.mixer.Sound('brick_break.wav')
    game_over_sound = pygame.mixer.Sound('game_over.wav')
    laser_sound = pygame.mixer.Sound('laser.wav')
except pygame.error as e:
    print(f"Warning: Sound file not found. {e}")
    class DummySound:
        def play(self): pass
    bounce_sound, brick_break_sound, game_over_sound, laser_sound = DummySound(), DummySound(), DummySound(), DummySound()

# --- Mute Setup ---
muted = False
def play_sound(sound):
    if not muted:
        sound.play()

# -- Game Objects --
paddle = Paddle(screen_width, screen_height)
ball = Ball(screen_width, screen_height)

# --- Level Setup ---
levels = [
    # Level 1: 4 rows, 10 cols
    {'rows': 4, 'cols': 10, 'colors': BRICK_COLORS},
    # Level 2: 6 rows, 12 cols, more green
    {'rows': 6, 'cols': 12, 'colors': BRICK_COLORS + [(0, 191, 255)]},
    # Level 3: 8 rows, 14 cols, more blue
    {'rows': 8, 'cols': 14, 'colors': BRICK_COLORS + [(0, 191, 255), (138, 43, 226)]},
]
current_level = 0

def create_brick_wall(level_idx=0):
    bricks = []
    level = levels[level_idx]
    brick_rows = level['rows']
    brick_cols = level['cols']
    colors = level['colors']
    brick_width = 75 if brick_cols <= 10 else 55 if brick_cols <= 12 else 45
    brick_height = 20
    brick_padding = 5
    wall_start_y = 50
    for row in range(brick_rows):
        for col in range(brick_cols):
            x = col * (brick_width + brick_padding) + brick_padding
            y = row * (brick_height + brick_padding) + wall_start_y
            color = colors[row % len(colors)]
            bricks.append(Brick(x, y, brick_width, brick_height, color))
    return bricks

bricks = create_brick_wall(current_level)
power_ups = []
lasers = []
particles = []
fireworks = []
multi_balls = []  # For multi-ball power-up

# --- Game Variables ---
# !!! PHASE: TITLE SCREEN !!!
# The game now starts on the title screen
game_state = 'title_screen' 
# !!! END PHASE: TITLE SCREEN !!!
score = 0
lives = 3
display_message = ""
message_timer = 0
firework_timer = 0


# -- Main Game Loop --
while True:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            # Mute toggle
            if event.key == pygame.K_m:
                muted = not muted
            # !!! PHASE: TITLE SCREEN !!!
            if event.key == pygame.K_SPACE:
                # If on title screen, start the game
                if game_state == 'title_screen':
                    game_state = 'playing'
                # If game is over, go back to title screen
                elif game_state in ['game_over', 'you_win']:
                    paddle.reset()
                    ball.reset()
                    multi_balls.clear()
                    current_level = 0
                    bricks = create_brick_wall(current_level)
                    score = 0
                    lives = 3
                    power_ups.clear()
                    lasers.clear()
                    particles.clear()
                    fireworks.clear()
                    game_state = 'title_screen'
                # Launch glued ball
                elif ball.is_glued:
                    ball.is_glued = False
            # !!! END PHASE: TITLE SCREEN !!!
            
            if event.key == pygame.K_f and paddle.has_laser:
                lasers.append(Laser(paddle.rect.centerx - 30, paddle.rect.top))
                lasers.append(Laser(paddle.rect.centerx + 30, paddle.rect.top))
                play_sound(laser_sound)

    # --- Drawing and Updating based on Game State ---
    screen.fill(BG_COLOR)

    if game_state == 'title_screen':
        # Draw the title
        title_surface = title_font.render("ARKANOID", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(screen_width / 2, screen_height / 2 - 50))
        screen.blit(title_surface, title_rect)
        
        # Draw the start message
        start_surface = game_font.render("Press SPACE to Start", True, (255, 255, 255))
        start_rect = start_surface.get_rect(center=(screen_width / 2, screen_height / 2 + 20))
        screen.blit(start_surface, start_rect)

        # Draw mute info
        mute_surface = message_font.render("Press M to Mute/Unmute", True, (200, 200, 200))
        mute_rect = mute_surface.get_rect(center=(screen_width / 2, screen_height / 2 + 70))
        screen.blit(mute_surface, mute_rect)
        # Show current mute state
        if muted:
            muted_surface = message_font.render("Muted", True, (255, 100, 100))
            muted_rect = muted_surface.get_rect(center=(screen_width / 2, screen_height / 2 + 100))
            screen.blit(muted_surface, muted_rect)
    elif game_state == 'playing':
        # --- Update all game objects ---
        paddle.update()
        keys = pygame.key.get_pressed()
        ball_status, collision_object = ball.update(paddle, keys[pygame.K_SPACE])
        # Update multi-balls
        for mball in multi_balls[:]:
            mball_status, _ = mball.update(paddle, False)
            if mball_status == 'lost':
                multi_balls.remove(mball)
        # ...existing code...
        if ball_status == 'lost':
            lives -= 1
            if lives <= 0:
                game_state = 'game_over'
                play_sound(game_over_sound)
            else:
                ball.reset()
                paddle.reset()
                multi_balls.clear()
        elif collision_object in ['wall', 'paddle']:
            play_sound(bounce_sound)
            for _ in range(5):
                particles.append(Particle(ball.rect.centerx, ball.rect.centery, (255, 255, 0), 1, 3, 1, 3, 0))

        for brick in bricks[:]:
            if ball.rect.colliderect(brick.rect):
                ball.speed_y *= -1
                for _ in range(15):
                    particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 4, 1, 4, 0.05))
                bricks.remove(brick)
                score += 10
                play_sound(brick_break_sound)
                if random.random() < 0.3:
                    power_up_type = random.choice(['grow', 'laser', 'glue', 'slow', 'shrink', 'multi', 'extra_life'])
                    power_up = PowerUp(brick.rect.centerx, brick.rect.centery, power_up_type)
                    power_ups.append(power_up)
                break
        
        # Multi-ball brick collision
        for mball in multi_balls:
            for brick in bricks[:]:
                if mball.rect.colliderect(brick.rect):
                    mball.speed_y *= -1
                    for _ in range(10):
                        particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 3, 1, 3, 0.05))
                    bricks.remove(brick)
                    score += 10
                    play_sound(brick_break_sound)
                    break
        
        for power_up in power_ups[:]:
            power_up.update()
            if power_up.rect.top > screen_height:
                power_ups.remove(power_up)
            elif paddle.rect.colliderect(power_up.rect):
                display_message = power_up.PROPERTIES[power_up.type]['message']
                message_timer = 120
                if power_up.type in ['grow', 'laser', 'glue']:
                    paddle.activate_power_up(power_up.type)
                elif power_up.type == 'slow':
                    ball.activate_power_up(power_up.type)
                elif power_up.type == 'shrink':
                    paddle.activate_power_up('shrink')
                elif power_up.type == 'multi':
                    # Add two more balls
                    for _ in range(2):
                        new_ball = Ball(screen_width, screen_height)
                        new_ball.rect.center = ball.rect.center
                        new_ball.speed_x = random.choice([-4, 4])
                        new_ball.speed_y = -4
                        multi_balls.append(new_ball)
                elif power_up.type == 'extra_life':
                    lives += 1
                power_ups.remove(power_up)
        
        for laser in lasers[:]:
            laser.update()
            if laser.rect.bottom < 0:
                lasers.remove(laser)
            else:
                for brick in bricks[:]:
                    if laser.rect.colliderect(brick.rect):
                        for _ in range(10):
                            particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 3, 1, 3, 0.05))
                        bricks.remove(brick)
                        lasers.remove(laser)
                        score += 10
                        play_sound(brick_break_sound)
                        break
        # --- Level progression ---
        if not bricks:
            current_level += 1
            if current_level < len(levels):
                bricks = create_brick_wall(current_level)
                ball.reset()
                paddle.reset()
                multi_balls.clear()
                display_message = f"Level {current_level+1}"
                message_timer = 90
            else:
                game_state = 'you_win'
        # --- Draw all game objects ---
        paddle.draw(screen)
        ball.draw(screen)
        for mball in multi_balls:
            mball.draw(screen)
        for brick in bricks:
            brick.draw(screen)
        for power_up in power_ups:
            power_up.draw(screen)
        for laser in lasers:
            laser.draw(screen)
        
        # --- Draw UI ---
        score_text = game_font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))
        lives_text = game_font.render(f"Lives: {lives}", True, (255, 255, 255))
        screen.blit(lives_text, (screen_width - lives_text.get_width() - 10, 10))
        level_text = game_font.render(f"Level: {current_level+1}", True, (255, 255, 255))
        screen.blit(level_text, (screen_width // 2 - 60, 10))

    elif game_state in ['game_over', 'you_win']:
        if game_state == 'you_win':
            firework_timer -= 1
            if firework_timer <= 0:
                fireworks.append(Firework(screen_width, screen_height))
                firework_timer = random.randint(20, 50)
            
            for firework in fireworks[:]:
                firework.update()
                if firework.is_dead():
                    fireworks.remove(firework)
            
            for firework in fireworks:
                firework.draw(screen)

            message = "YOU WIN!"
        else:
            message = "GAME OVER"
        text_surface = game_font.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(screen_width / 2, screen_height / 2 - 20))
        screen.blit(text_surface, text_rect)
        restart_surface = game_font.render("Press SPACE to return to Title", True, (255, 255, 255))
        restart_rect = restart_surface.get_rect(center=(screen_width / 2, screen_height / 2 + 30))
        screen.blit(restart_surface, restart_rect)
        # Show mute state
        if muted:
            muted_surface = message_font.render("Muted", True, (255, 100, 100))
            muted_rect = muted_surface.get_rect(center=(screen_width / 2, screen_height / 2 + 70))
            screen.blit(muted_surface, muted_rect)

    # --- Update effects and messages (these run in all states) ---
    if message_timer > 0:
        message_timer -= 1
        message_surface = message_font.render(display_message, True, (255, 255, 255))
        message_rect = message_surface.get_rect(center=(screen_width / 2, screen_height - 60))
        screen.blit(message_surface, message_rect)
        
    for particle in particles[:]:
        particle.update()
        if particle.size <= 0:
            particles.remove(particle)
    for particle in particles:
        particle.draw(screen)
    # !!! END PHASE: TITLE SCREEN !!!

    # --- Final Display Update ---
    pygame.display.flip()
    clock.tick(60)
