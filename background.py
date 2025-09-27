import pygame
import random
import sys
import time
import os
import math

pygame.init()
pygame.mixer.init()


def run_splash_screen():
    splash_image = pygame.image.load("Screenshot 2025-06-19 225939 .png")
    splash_image = pygame.transform.scale(splash_image, (WIDTH, HEIGHT))

    button_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT - 180, 300, 70)
    button_text = BIG_FONT.render("Start Game", True, BLACK)

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    return  # Exit the splash screen and continue to name prompt

        screen.blit(splash_image, (0, 0))

        # Optional loading dots animation
        dots = int((time.time() * 2) % 4)
        loading_text = FONT.render("Loading" + "." * dots, True, (0, 0, 0))
        screen.blit(loading_text, (WIDTH // 2 - loading_text.get_width() // 2, HEIGHT - 80))

        # Draw start button
        pygame.draw.rect(screen,(255,215,0), button_rect, border_radius=12)
        pygame.draw.rect(screen, BLACK, button_rect, 3, border_radius=12)
        screen.blit(button_text, (button_rect.centerx - button_text.get_width() // 2,
                                  button_rect.centery - button_text.get_height() // 2))

        pygame.display.flip()#(230, 230, 250)


# --- Constants ---
#WIDTH, HEIGHT = 1000, 600
WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (180,180,180)
BLUE = (70,130,255)
YELLOW = (255,215,0)
GREEN = (0,200,0)
RED = (255,0,0)

FONT = pygame.font.SysFont("Segoe UI Emoji",25)
BIG_FONT = pygame.font.SysFont("Segoe UI Emoji",50)
SMALL_FONT = pygame.font.SysFont("Segoe UI Emoji", 20)

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH , HEIGHT), pygame.FULLSCREEN | pygame.SCALED)


pygame.display.set_caption("Stacking Plates Game")
clock = pygame.time.Clock()

# --- Game States ---
run_splash_screen()
current_screen = "name_prompt"
selected_level = 0
start_time = elapsed_time = score = 0
max_time_per_level = 300
CONTENT_RECT = pygame.Rect(
    int(WIDTH * 0.05),
    int(HEIGHT * 0.08),
    int(WIDTH * 0.90),
    int(HEIGHT * 0.84)
)

STACK_COUNT = 3
PLATE_HEIGHT, STACK_WIDTH = 23, 180
move_history = []
paused = False
pause_start_time = 0

# --- Name Prompt Input State ---
name_input_box = pygame.Rect(CONTENT_RECT.centerx - 150, CONTENT_RECT.centery - 30, 300, 50)
input_active = True
input_text = ""
input_error = ""

# --- Player and Leaderboard ---
player_name = ""
leaderboard_data = []

# --- Audio ---
try:
    pygame.mixer.music.load('background.mp3')
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)
    sound_move = pygame.mixer.Sound('move.wav'); sound_move.set_volume(0.5)
    sound_win = pygame.mixer.Sound('win.wav'); sound_win.set_volume(0.7)
    sound_timeout = pygame.mixer.Sound('timeout.wav'); sound_timeout.set_volume(0.7)

except pygame.error:
    sound_move = sound_win = None

# --- Level Config ---
base_total_plates = 4
plates_increment = 2
base_stacks = 3
MAX_LEVELS = 5
completed_levels = [True] + [False]*(MAX_LEVELS-1)



# --- Button Class ---
class Button:
    def __init__(self, rect, text, enabled=True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.enabled = enabled

    def draw(self, s):
        clr = BLUE if self.enabled else GRAY
        pygame.draw.rect(s, clr, self.rect, border_radius=8)
        pygame.draw.rect(s, BLACK, self.rect, 2, border_radius=8)
        t = FONT.render(self.text, True, BLACK)
        s.blit(t, (self.rect.centerx - t.get_width()//2, self.rect.centery - t.get_height()//2))

    def is_clicked(self, pos):
        return self.enabled and self.rect.collidepoint(pos)

# --- Buttons ---
button_width = 300
button_height = 60
button_spacing = 20
start_y = CONTENT_RECT.centery - ((button_height + button_spacing) * 2)

home_buttons = [
    Button((CONTENT_RECT.centerx - button_width // 2, start_y + i * (button_height + button_spacing), button_width, button_height), label)
    for i, label in enumerate(["Play", "Levels", "Help", "Quit", "Leaderboard"])
]


# Centered Level Buttons Setup
# Updated button size and spacing
cols = 3
rows = (MAX_LEVELS + cols - 1) // cols

button_w, button_h = 220, 80   # 🔺 Increased size
spacing_x, spacing_y = 50, 50  # 🔺 Increased spacing

grid_w = cols * button_w + (cols - 1) * spacing_x
grid_h = rows * button_h + (rows - 1) * spacing_y

start_x = CONTENT_RECT.centerx - grid_w // 2
start_y = CONTENT_RECT.centery - grid_h // 2 + 40  # Shifted down slightly for spacing under heading

level_buttons = []
for i in range(MAX_LEVELS):
    row = i // cols
    col = i % cols
    x = start_x + col * (button_w + spacing_x)
    y = start_y + row * (button_h + spacing_y)
    rect = (x, y, button_w, button_h)
    level_buttons.append(Button(rect, f"Level {i+1}", enabled=completed_levels[i]))



back_button = Button((10,10,140,40), "← Back")
win_back_button = Button((CONTENT_RECT.centerx-220, CONTENT_RECT.bottom-90, 180, 50), "Back to Home")
win_next_button = Button((CONTENT_RECT.centerx+40, CONTENT_RECT.bottom-90, 180, 50), "Next Level")
timeout_retry_button = Button((CONTENT_RECT.centerx-220, CONTENT_RECT.bottom-90, 180, 50), "Retry")
timeout_exit_button = Button((CONTENT_RECT.centerx+40, CONTENT_RECT.bottom-90, 180, 50), "Exit")
clear_lb_button = Button((CONTENT_RECT.centerx - 120, CONTENT_RECT.bottom - 100, 240, 60), "Clear Leaderboard")
# Updated pause_button text to use Unicode characters
pause_button = Button((WIDTH - 150, 10, 140, 40), "⏸️")

# --- Utility Functions ---
def draw_text_center(txt, font, color, y):
    t = font.render(txt, True, color)
    screen.blit(t, (WIDTH // 2 - t.get_width() // 2, y))

def draw_box():
    pygame.draw.rect(screen, (230,230,250), CONTENT_RECT, border_radius=12)
    pygame.draw.rect(screen, BLACK, CONTENT_RECT, 3, border_radius=12)

def draw_gradient(s, top, bottom):
    
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(top[0]*(1-t)+bottom[0]*t)
        g = int(top[1]*(1-t)+bottom[1]*t)
        b = int(top[2]*(1-t)+bottom[2]*t)
        pygame.draw.line(s, (r,g,b), (0, y), (WIDTH, y))  # This is fine

def init_game(level):
    global stacks, total_plates, STACK_COUNT, plates, selected_stack
    global start_time, elapsed_time, score, move_history, max_time_per_level, paused, pause_start_time

    total_plates = base_total_plates + plates_increment * level
    STACK_COUNT = base_stacks + (level // 2)
    plates = list(range(1, total_plates + 1))
    random.shuffle(plates)
    stacks = [[] for _ in range(STACK_COUNT)]
    sel = 0
    for plate in plates:
        stacks[sel].append(plate)
        sel = (sel + 1) % (STACK_COUNT - 1)

    selected_stack = None
    start_time = time.time()
    elapsed_time = score = 0
    move_history = []
    paused = False
    pause_start_time = 0

    max_time_per_level = 45 * (level + 1)

def is_valid_move(f, t):
    if not stacks[f]: return False
    return not stacks[t] or stacks[f][-1] > stacks[t][-1]

def move_plate(f, t):
    global score
    if is_valid_move(f, t):
        plate = stacks[f].pop()
        stacks[t].append(plate)
        move_history.append((f, t, plate))
        score += 1
        if sound_move: sound_move.play()
        return True
    return False

def undo_move():
    global score
    if move_history:
        f, t, plate = move_history.pop()
        if stacks[t] and stacks[t][-1] == plate:
            stacks[t].pop()
            stacks[f].append(plate)
            score += 1
            if sound_move:
                sound_move.play()

def is_win():
    return any(len(s)==total_plates and all(s[i]<s[i+1] for i in range(len(s)-1)) for s in stacks)

def get_clicked_stack(pos):
    x, y = pos
    if not CONTENT_RECT.collidepoint(pos): return None
    idx = (x - CONTENT_RECT.left) // (CONTENT_RECT.width // STACK_COUNT)
    return idx if 0 <= idx < STACK_COUNT else None

def save_leaderboard():
    with open("leaderboard.txt", "w") as f:
        for name, level, moves, t in leaderboard_data:
            f.write(f"{name},{level},{moves},{t}\n")

def load_leaderboard():
    global leaderboard_data
    if os.path.exists("leaderboard.txt"):
        with open("leaderboard.txt", "r") as f:
            leaderboard_data = [line.strip().split(",") for line in f.readlines()]
            leaderboard_data = [(n, int(lv), int(mv), int(t)) for n, lv, mv, t in leaderboard_data]

def add_to_leaderboard(name, level, moves, t):
    leaderboard_data.append((name, level, moves, t))
    leaderboard_data.sort(key=lambda x: (x[1], x[2], x[3]))
    leaderboard_data[:] = leaderboard_data[:8]
    save_leaderboard()

def draw_stacks():
    y_base = CONTENT_RECT.bottom - 40
    width_each = CONTENT_RECT.width // STACK_COUNT
    for i in range(STACK_COUNT):
        x = CONTENT_RECT.left + i * width_each + width_each // 2
        rc = GREEN if is_win() and len(stacks[i]) == total_plates else GRAY
        pygame.draw.rect(screen, rc, (x - STACK_WIDTH // 2, y_base - 300, STACK_WIDTH, 300), 5 if rc == GREEN else 3)
        y = y_base
        for p in reversed(stacks[i]):
            w = 40 + p * 8
            rect = pygame.Rect(x - w // 2, y - PLATE_HEIGHT, w, PLATE_HEIGHT)
            clr = YELLOW if i == selected_stack else BLUE
            pygame.draw.rect(screen, clr, rect)
            pygame.draw.rect(screen, BLACK, rect, 2)
            t = FONT.render(str(p), True, BLACK)
            screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))
            y -= PLATE_HEIGHT + 2

def draw_screens():
    global elapsed_time, current_screen
    bg_colors = {
        "home": ((10, 100, 150), (60, 180, 200)),
        "levels": ((40, 20, 60), (130, 50, 150)),
        "help": ((60, 60, 60), (180, 180, 180)),
        "game": ((30, 30, 60), (80, 120, 180)),
        "win": ((0, 70, 0), (80, 180, 80)),
        "timeout": ((100, 0, 0), (180, 50, 50)),
        "name_prompt": ((40, 40, 80), (100, 100, 180)),
        "leaderboard": ((30, 30, 30), (90, 90, 90))
    }
    draw_gradient(screen, *bg_colors[current_screen])
    draw_box()

    if current_screen == "name_prompt":
        draw_text_center("Enter Your Name", BIG_FONT, BLACK, CONTENT_RECT.top + 40)
        pygame.draw.rect(screen, WHITE, name_input_box, 0, border_radius=10)
        pygame.draw.rect(screen, BLACK, name_input_box, 2, border_radius=10)
        name_surface = FONT.render(input_text, True, BLACK)
        screen.blit(name_surface, (name_input_box.x + 10, name_input_box.y + 10))
        if input_error:
            err_surface = SMALL_FONT.render(input_error, True, RED)
            screen.blit(err_surface, (CONTENT_RECT.centerx - err_surface.get_width()//2, name_input_box.bottom + 10))
        draw_text_center("Press Enter(only alphabets) to Continue", SMALL_FONT, BLACK, CONTENT_RECT.bottom - 60)

    elif current_screen == "home":
        draw_text_center(" STACKING PLATES ", pygame.font.SysFont("Segoe UI Emoji", 70), BLACK, CONTENT_RECT.top + 20)
        #draw_text_center_splash(" STACKING PLATES ", BIG_FONT, (50, 10, 10), HEIGHT // 2 + 100)

        for b in home_buttons: b.draw(screen)

    elif current_screen == "levels":
        draw_text_center("Select Level", pygame.font.SysFont("Segoe UI Emoji", 70), BLUE, CONTENT_RECT.top + 30)


        for i, b in enumerate(level_buttons):
            b.enabled = completed_levels[i]
            b.draw(screen)
            if not b.enabled:
                l = FONT.render("\U0001F512", True, RED)
                screen.blit(l, (b.rect.right - 30, b.rect.top + 10))
        back_button.draw(screen)

    elif current_screen == "help":
        draw_text_center("Help", BIG_FONT, BLACK, CONTENT_RECT.top + 20)
        lines = [
            "- Move ALL plates (in increasing order) onto any stack.",
            "- visually which means larger at bottom smaller at top",
            "- Move only one top plate at a time.",
            "- Can't place larger over smaller.",
            "- Each level adds 2 new plates.",
            "- Every 2 levels add another stack.",
            "- Click stacks to move.",
            "- Use ← Back to go back.",
            "- Press Z to undo last move.",
            "- starts at 45 secs and increment of 45 secs for every level"
        ]
        for i, ln in enumerate(lines):
            screen.blit(FONT.render(ln, True, BLACK), (CONTENT_RECT.left + 20, CONTENT_RECT.top + 80 + i * 30))
        back_button.draw(screen)

    elif current_screen == "game":
        draw_stacks()
        if not paused:
            elapsed_time = int(time.time() - start_time)
        tleft = max(0, max_time_per_level - elapsed_time)
        screen.blit(FONT.render(f"Time Left: {tleft}s", True, BLACK), (CONTENT_RECT.left + 10, CONTENT_RECT.top + 10))
        sb = pygame.Rect(CONTENT_RECT.right - 160, CONTENT_RECT.top + 5, 140, 40)
        pygame.draw.rect(screen, (255, 255, 200), sb, border_radius=6)
        pygame.draw.rect(screen, BLACK, sb, 2, border_radius=6)
        screen.blit(FONT.render(f"Moves: {score}", True, BLACK), (sb.left + 10, sb.centery - 10))
        screen.blit(FONT.render(f"Level: {selected_level + 1}", True, BLACK), (CONTENT_RECT.left + 10, CONTENT_RECT.top + 40))
        back_button.draw(screen)
        
        # Draw Pause/Resume button with Unicode characters
        pause_button.text = "▶️" if paused else "⏸️"
        pause_button.draw(screen)

        if paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))
            draw_text_center("PAUSED", BIG_FONT, BLACK, HEIGHT // 2 - 50)
            draw_text_center("Click ▶️ to Continue", FONT, BLACK, HEIGHT // 2 + 20)


    elif current_screen == "win":
        draw_text_center("\U0001F389 CONGRATULATIONS!", BIG_FONT, BLACK, CONTENT_RECT.top + 50)
        draw_text_center(f"Level {selected_level+1} Completed", FONT, BLACK, CONTENT_RECT.top + 140)
        draw_text_center(f"Moves: {score} | Time: {elapsed_time}s", FONT, BLACK, CONTENT_RECT.top + 200)
        win_back_button.draw(screen)
        win_next_button.enabled = (selected_level+1 < MAX_LEVELS and completed_levels[selected_level+1])
        win_next_button.draw(screen)

    elif current_screen == "timeout":
        draw_text_center("⏰ TIME'S UP!", BIG_FONT, BLACK, CONTENT_RECT.top + 80)
        draw_text_center(f"Level {selected_level+1} failed", FONT, BLACK, CONTENT_RECT.top + 160)
        draw_text_center(f"Moves: {score} | Time: {elapsed_time}s", FONT, BLACK, CONTENT_RECT.top + 220)
        timeout_retry_button.draw(screen)
        timeout_exit_button.draw(screen)

    elif current_screen == "leaderboard":
        draw_text_center("Leaderboard", BIG_FONT, BLACK, CONTENT_RECT.top + 30)
        headers = ["Name", "Level", "Moves", "Time"]
        for i, h in enumerate(headers):
            screen.blit(FONT.render(h, True, BLACK), (CONTENT_RECT.left + 80 + i * 180, CONTENT_RECT.top + 80))
        for i, (n, lv, mv, t) in enumerate(leaderboard_data[:10]):
            for j, val in enumerate([n, str(lv), str(mv), str(t)]):
                screen.blit(SMALL_FONT.render(val, True, RED), (CONTENT_RECT.left + 80 + j*180, CONTENT_RECT.top + 120 + i*30))
        back_button.draw(screen)
        clear_lb_button.draw(screen)
    

# --- Main loop ---
running = True
selected_stack = None

while running:
    clock.tick(30)
    pos = pygame.mouse.get_pos()

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        if current_screen == "name_prompt":
            if e.type == pygame.KEYDOWN:
                if input_active:
                    if e.key == pygame.K_RETURN:
                        if len(input_text.strip()) >= 2:
                            player_name = input_text.strip()
                            load_leaderboard()
                            current_screen = "home"
                        else:
                            input_error = "Name must be at least 2 characters(alphabets only)"
                    elif e.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        if len(input_text) < 20 and e.unicode.isalpha():
                            input_text += e.unicode

        elif e.type == pygame.MOUSEBUTTONDOWN:
            if current_screen == "home":
                for b in home_buttons:
                    if b.is_clicked(pos):
                        if b.text == "Play":
                            selected_level = 0
                            init_game(0)
                            current_screen = "game"
                        elif b.text == "Levels":
                            current_screen = "levels"
                        elif b.text == "Help":
                            current_screen = "help"
                        elif b.text == "Quit":
                            running = False
                        elif b.text == "Leaderboard":
                            current_screen = "leaderboard"

            elif current_screen == "levels":
                if back_button.is_clicked(pos):
                    current_screen = "home"
                else:
                    for i, b in enumerate(level_buttons):
                        if b.is_clicked(pos) and b.enabled:
                            selected_level = i
                            init_game(i)
                            current_screen = "game"

            elif current_screen == "help" and back_button.is_clicked(pos):
                current_screen = "home"

            elif current_screen == "game":
                if pause_button.is_clicked(pos):
                    if not paused:
                        paused = True
                        pause_start_time = time.time()
                        pygame.mixer.music.pause()
                    else:
                        paused = False
                        start_time += (time.time() - pause_start_time)
                        pygame.mixer.music.unpause()
                elif not paused:
                    if back_button.is_clicked(pos):
                        current_screen = "home"
                    else:
                        cs = get_clicked_stack(pos)
                        if cs is not None:
                            if selected_stack is None and stacks[cs]:
                                selected_stack = cs
                            elif selected_stack is not None:
                                move_plate(selected_stack, cs)
                                selected_stack = None
                
                if not paused and is_win():
                    completed_levels[selected_level] = True
                    if selected_level + 1 < MAX_LEVELS:
                        completed_levels[selected_level + 1] = True
                    if sound_win: sound_win.play()
                    if not any(n == player_name and lv == selected_level+1 and mv == score for n, lv, mv, t in leaderboard_data):
                        add_to_leaderboard(player_name, selected_level + 1, score, elapsed_time)
                    current_screen = "win"
                    pygame.mixer.music.play(-1)

            elif current_screen == "win":
                if win_back_button.is_clicked(pos):
                    current_screen = "home"
                elif win_next_button.is_clicked(pos) and win_next_button.enabled:
                    selected_level += 1
                    init_game(selected_level)
                    current_screen = "game"

            elif current_screen == "timeout":
                if timeout_retry_button.is_clicked(pos):
                    init_game(selected_level)
                    current_screen = "game"
                    pygame.mixer.music.play(-1)
                elif timeout_exit_button.is_clicked(pos):
                    current_screen = "home"

            elif current_screen == "leaderboard":
                if back_button.is_clicked(pos):
                    current_screen = "home"
                elif clear_lb_button.is_clicked(pos):
                    leaderboard_data.clear()
                    save_leaderboard()

        elif e.type == pygame.KEYDOWN and current_screen == "game" and e.key == pygame.K_z:
            if not paused:
                undo_move()

    if current_screen == "game" and not paused:
        elapsed_time = int(time.time() - start_time)
        if elapsed_time >= max_time_per_level:
            current_screen = "timeout"
            pygame.mixer.music.stop()
            if sound_timeout: sound_timeout.play()


    draw_screens()
    pygame.display.flip()

pygame.quit()
sys.exit()