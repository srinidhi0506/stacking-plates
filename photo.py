import pygame
import random
import sys
import time
import os

pygame.init()
pygame.mixer.init()

# --- Constants ---
infoObject = pygame.display.Info()
WIDTH, HEIGHT = infoObject.current_w, infoObject.current_h

# Dynamic scaling factor based on screen height for overall neatness
SCALE_FACTOR = HEIGHT / 900 # Base this on a comfortable reference height (e.g., 900p)

WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (180,180,180)
BLUE = (70,130,255)
YELLOW = (255,215,0)
GREEN = (0,200,0)
RED = (255,0,0)

# Adjust font sizes using the scaling factor
FONT = pygame.font.SysFont("Segoe UI Emoji", int(28 * SCALE_FACTOR))
BIG_FONT = pygame.font.SysFont("Segoe UI Emoji", int(50 * SCALE_FACTOR))
SMALL_FONT = pygame.font.SysFont("Segoe UI Emoji", int(20 * SCALE_FACTOR))
# New, larger font for win/timeout messages
HUGE_FONT = pygame.font.SysFont("Segoe UI Emoji", int(70 * SCALE_FACTOR)) # Increased font size

screen = pygame.display.set_mode((WIDTH,HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Stacking Plates Game")
clock = pygame.time.Clock()

# --- Game States ---
current_screen = "start_screen" # Changed initial screen
selected_level = 0
start_time = elapsed_time = score = 0
max_time_per_level = 300

# Base CONTENT_RECT - this will be modified for specific screens if needed
base_content_rect_padding_x = WIDTH * 0.05
base_content_rect_padding_y = HEIGHT * 0.08
BASE_CONTENT_RECT = pygame.Rect(base_content_rect_padding_x, base_content_rect_padding_y,
                                 WIDTH - (2 * base_content_rect_padding_x), HEIGHT - (2 * base_content_rect_padding_y))

STACK_COUNT = 3
PLATE_HEIGHT, STACK_WIDTH = 0, 0 # Initialized to 0, set in init_game()

move_history = []
paused = False
pause_start_time = 0

# --- Name Prompt Input State ---
input_box_width = int(WIDTH * 0.3)
input_box_height = int(55 * SCALE_FACTOR)
name_input_box = pygame.Rect(BASE_CONTENT_RECT.centerx - input_box_width // 2,
                             BASE_CONTENT_RECT.centery - input_box_height // 2,
                             input_box_width, input_box_height)
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
    print("Warning: Audio files not found or mixer error. Game will run without sound.")
    sound_move = sound_win = sound_timeout = None

# --- Images ---
try:
    start_screen_image = pygame.image.load('Screenshot 2025-06-19 212608.png').convert_alpha()
    start_screen_image = pygame.transform.scale(start_screen_image, (WIDTH, HEIGHT))
except pygame.error as e:
    print(f"Warning: Could not load start screen image: {e}. Falling back to solid color.")
    start_screen_image = None


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
        self.border_radius = int(8 * SCALE_FACTOR)
        self.border_thickness = int(2 * SCALE_FACTOR)

    def draw(self, s):
        clr = BLUE if self.enabled else GRAY
        pygame.draw.rect(s, clr, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(s, BLACK, self.rect, self.border_thickness, border_radius=self.border_radius)
        # We handle text drawing for level buttons and some others outside this method for centering
        # For other buttons, draw text normally
        if self.text not in [f"Level {i+1}" for i in range(MAX_LEVELS)]: # Exclude level buttons
            t = FONT.render(self.text, True, BLACK)
            s.blit(t, (self.rect.centerx - t.get_width()//2, self.rect.centery - t.get_height()//2))

    def is_clicked(self, pos):
        return self.enabled and self.rect.collidepoint(pos)

# --- Buttons (initialization based on BASE_CONTENT_RECT, will adjust for home screen later) ---
# Button dimensions and spacing scaled for home screen
# These will be dynamically adjusted within draw_screens for the home menu
button_width_main = int(BASE_CONTENT_RECT.width * 0.35)
button_height_main = int(60 * SCALE_FACTOR)
button_spacing_main = int(25 * SCALE_FACTOR)

home_buttons = [] # Will be populated dynamically in draw_screens for precise positioning

level_button_width = int(180 * SCALE_FACTOR)
level_button_height = int(60 * SCALE_FACTOR)
level_button_x_spacing = int(20 * SCALE_FACTOR)
level_button_y_spacing = int(20 * SCALE_FACTOR)

level_buttons = [] # Will be populated dynamically in draw_screens for precise positioning

# Back button (top-left)
back_button = Button((int(WIDTH * 0.02), int(HEIGHT * 0.02), int(140 * SCALE_FACTOR), int(40 * SCALE_FACTOR)), "← Back")

# Win/Timeout screen buttons (bottom of CONTENT_RECT)
win_timeout_btn_width = int(180 * SCALE_FACTOR)
win_timeout_btn_height = int(50 * SCALE_FACTOR)
win_timeout_btn_spacing = int(40 * SCALE_FACTOR)

win_back_button = Button((BASE_CONTENT_RECT.centerx - win_timeout_btn_width - win_timeout_btn_spacing // 2,
                          BASE_CONTENT_RECT.bottom - win_timeout_btn_height - int(20 * SCALE_FACTOR),
                          win_timeout_btn_width, win_timeout_btn_height), "Back to Home")
win_next_button = Button((BASE_CONTENT_RECT.centerx + win_timeout_btn_spacing // 2,
                          BASE_CONTENT_RECT.bottom - win_timeout_btn_height - int(20 * SCALE_FACTOR),
                          win_timeout_btn_width, win_timeout_btn_height), "Next Level")

timeout_retry_button = Button((BASE_CONTENT_RECT.centerx - win_timeout_btn_width - win_timeout_btn_spacing // 2,
                                BASE_CONTENT_RECT.bottom - win_timeout_btn_height - int(20 * SCALE_FACTOR),
                                win_timeout_btn_width, win_timeout_btn_height), "Retry")
timeout_exit_button = Button((BASE_CONTENT_RECT.centerx + win_timeout_btn_spacing // 2,
                              BASE_CONTENT_RECT.bottom - win_timeout_btn_height - int(20 * SCALE_FACTOR),
                              win_timeout_btn_width, win_timeout_btn_height), "Exit")

# Clear Leaderboard button
clear_lb_button = Button((BASE_CONTENT_RECT.centerx - int(240 * SCALE_FACTOR) // 2,
                          BASE_CONTENT_RECT.bottom - int(60 * SCALE_FACTOR) - int(20 * SCALE_FACTOR),
                          int(240 * SCALE_FACTOR), int(60 * SCALE_FACTOR)), "Clear Leaderboard")

# Pause button (top-right)
pause_button = Button((WIDTH - int(150 * SCALE_FACTOR), int(HEIGHT * 0.02),
                        int(140 * SCALE_FACTOR), int(40 * SCALE_FACTOR)), "⏸️")

# --- Start Screen Button ---
start_game_button_width = int(300 * SCALE_FACTOR)
start_game_button_height = int(70 * SCALE_FACTOR)
start_game_button = Button((WIDTH // 2 - start_game_button_width // 2,
                            HEIGHT - int(150 * SCALE_FACTOR), # Position it lower on the screen
                            start_game_button_width, start_game_button_height), "Start Game")


# --- Utility Functions ---
def draw_text_center(txt, font, color, y):
    t = font.render(txt, True, color)
    screen.blit(t, (WIDTH // 2 - t.get_width() // 2, y))

def draw_box(rect_to_draw):
    pygame.draw.rect(screen, (230,230,250), rect_to_draw, border_radius=int(12 * SCALE_FACTOR))
    pygame.draw.rect(screen, BLACK, rect_to_draw, int(3 * SCALE_FACTOR), border_radius=int(12 * SCALE_FACTOR))

def draw_gradient(s, top, bottom):
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(top[0]*(1-t)+bottom[0]*t)
        g = int(top[1]*(1-t)+bottom[1]*t)
        b = int(top[2]*(1-t)+bottom[2]*t)
        pygame.draw.line(s, (r,g,b), (0,y), (WIDTH,y))

def init_game(level):
    global stacks, total_plates, STACK_COUNT, plates, selected_stack
    global start_time, elapsed_time, score, move_history, max_time_per_level, paused, pause_start_time
    global PLATE_HEIGHT, STACK_WIDTH

    total_plates = base_total_plates + plates_increment * level
    STACK_COUNT = base_stacks + (level // 2)
    
    min_plate_visual_width = int(30 * SCALE_FACTOR)
    spacing_between_poles = int(10 * SCALE_FACTOR)
    max_possible_stacks = int(BASE_CONTENT_RECT.width / (min_plate_visual_width + spacing_between_poles))
    if STACK_COUNT > max_possible_stacks and max_possible_stacks >= base_stacks:
        STACK_COUNT = max_possible_stacks
    elif STACK_COUNT > max_possible_stacks and max_possible_stacks < base_stacks:
        STACK_COUNT = base_stacks

    plates = list(range(1, total_plates + 1))
    random.shuffle(plates)
    stacks = [[] for _ in range(STACK_COUNT)]
    
    sel = 0
    for plate in plates:
        stacks[sel].append(plate)
        sel = (sel + 1) % (STACK_COUNT - 1 if STACK_COUNT > 1 else STACK_COUNT)

    selected_stack = None
    start_time = time.time()
    elapsed_time = score = 0
    move_history = []
    paused = False
    pause_start_time = 0

    max_time_per_level = 45 * (level + 1)

    pole_area_height = BASE_CONTENT_RECT.height * 0.7
    PLATE_HEIGHT = min(int(30 * SCALE_FACTOR), int(pole_area_height / (total_plates + 2)))
    PLATE_HEIGHT = max(PLATE_HEIGHT, int(15 * SCALE_FACTOR))

    width_per_stack_column = BASE_CONTENT_RECT.width / STACK_COUNT
    STACK_WIDTH = int(width_per_stack_column * 0.6)
    STACK_WIDTH = max(STACK_WIDTH, int(30 * SCALE_FACTOR))

def is_valid_move(f, t):
    if not (0 <= f < STACK_COUNT and 0 <= t < STACK_COUNT): return False
    if f == t: return False
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
        else:
            print("Warning: Undo operation attempted on a mismatched plate. Game state might be inconsistent.")
            stacks[f].append(plate)

def is_win():
    for s in stacks:
        if len(s) == total_plates:
            if all(s[i] < s[i+1] for i in range(len(s)-1)):
                return True
    return False

def get_clicked_stack(pos):
    x, y = pos
    # Use BASE_CONTENT_RECT for general game area, even if a modified rect is used for drawing
    if not BASE_CONTENT_RECT.collidepoint(pos): return None
    
    width_each_column = BASE_CONTENT_RECT.width / STACK_COUNT
    
    y_base_draw = BASE_CONTENT_RECT.bottom - int(20 * SCALE_FACTOR)
    pole_area_height = BASE_CONTENT_RECT.height * 0.7
    pole_height_draw = max(pole_area_height, (total_plates + 2) * PLATE_HEIGHT)
    
    clickable_y_start = y_base_draw - pole_height_draw
    clickable_y_end = y_base_draw + int(10 * SCALE_FACTOR)

    if not (clickable_y_start <= y <= clickable_y_end):
        return None

    for i in range(STACK_COUNT):
        column_left = BASE_CONTENT_RECT.left + i * width_each_column
        column_right = column_left + width_each_column
        
        if column_left <= x < column_right:
            return i
    return None

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
    else:
        leaderboard_data = []

def add_to_leaderboard(name, level, moves, t):
    leaderboard_data.append((name, level, moves, t))
    leaderboard_data.sort(key=lambda x: (x[1], x[2], x[3]))
    leaderboard_data[:] = leaderboard_data[:8]
    save_leaderboard()

def draw_stacks():
    y_base = BASE_CONTENT_RECT.bottom - int(20 * SCALE_FACTOR)
    
    pole_area_height = BASE_CONTENT_RECT.height * 0.7
    pole_height = max(pole_area_height, (total_plates + 2) * PLATE_HEIGHT)
    
    width_each_column = BASE_CONTENT_RECT.width / STACK_COUNT

    for i in range(STACK_COUNT):
        x_center = BASE_CONTENT_RECT.left + i * width_each_column + width_each_column // 2
        
        rc = GREEN if is_win() and len(stacks[i]) == total_plates else GRAY
        pygame.draw.rect(screen, rc, (x_center - STACK_WIDTH // 2, y_base - pole_height, STACK_WIDTH, pole_height),
                         int(5 * SCALE_FACTOR) if rc == GREEN else int(3 * SCALE_FACTOR))
        
        current_y = y_base
        for p in reversed(stacks[i]):
            plate_width_dynamic = int(STACK_WIDTH * 0.5 + p * (STACK_WIDTH * 0.4 / total_plates))
            plate_width = min(plate_width_dynamic, int(width_each_column * 0.9))
            plate_width = max(plate_width, int(30 * SCALE_FACTOR))
            
            rect = pygame.Rect(x_center - plate_width // 2, current_y - PLATE_HEIGHT, plate_width, PLATE_HEIGHT)
            clr = YELLOW if i == selected_stack else BLUE
            pygame.draw.rect(screen, clr, rect)
            pygame.draw.rect(screen, BLACK, rect, int(2 * SCALE_FACTOR))
            
            t = FONT.render(str(p), True, BLACK)
            text_rect = t.get_rect(center=rect.center)
            screen.blit(t, text_rect)
            current_y -= (PLATE_HEIGHT + int(2 * SCALE_FACTOR))

def draw_screens():
    global elapsed_time, current_screen, home_buttons, level_buttons
    bg_colors = {
        "start_screen": ((0, 0, 0), (0, 0, 0)), # Dark background for image
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

    if current_screen == "start_screen":
        if start_screen_image:
            screen.blit(start_screen_image, (0, 0))
        else:
            # Fallback if image not loaded
            draw_text_center("Stacking Plates Game", BIG_FONT, WHITE, HEIGHT // 2 - BIG_FONT.get_height() // 2)
        start_game_button.draw(screen) # Draw the "Start Game" button

    else: # All other screens, draw the content box
        # Determine which CONTENT_RECT to use based on the current screen
        if current_screen == "home":
            # Make CONTENT_RECT slightly smaller for home screen
            home_rect_padding_y = HEIGHT * 0.12 # More vertical padding
            current_content_rect = pygame.Rect(BASE_CONTENT_RECT.left, home_rect_padding_y,
                                                BASE_CONTENT_RECT.width, HEIGHT - (2 * home_rect_padding_y))
        else:
            current_content_rect = BASE_CONTENT_RECT
        
        draw_box(current_content_rect) # Draw the box using the determined rect

        if current_screen == "name_prompt":
            draw_text_center("Enter Your Name", BIG_FONT, BLACK, current_content_rect.top + current_content_rect.height * 0.1)
            # Name input box also needs to be centered relative to BASE_CONTENT_RECT
            name_input_box.centerx = BASE_CONTENT_RECT.centerx
            name_input_box.centery = BASE_CONTENT_RECT.centery - int(40 * SCALE_FACTOR) # Adjust for title
            pygame.draw.rect(screen, WHITE, name_input_box, 0, border_radius=int(10 * SCALE_FACTOR))
            pygame.draw.rect(screen, BLACK, name_input_box, int(2 * SCALE_FACTOR), border_radius=int(10 * SCALE_FACTOR))
            name_surface = FONT.render(input_text, True, BLACK)
            screen.blit(name_surface, (name_input_box.x + int(10 * SCALE_FACTOR),
                                        name_input_box.y + name_input_box.height // 2 - name_surface.get_height() // 2))
            if input_error:
                err_surface = SMALL_FONT.render(input_error, True, RED)
                screen.blit(err_surface, (current_content_rect.centerx - err_surface.get_width()//2, name_input_box.bottom + int(10 * SCALE_FACTOR)))
            draw_text_center("Press Enter (alphabets only, min 2 chars) to Continue", SMALL_FONT, BLACK, current_content_rect.bottom - current_content_rect.height * 0.1)

        elif current_screen == "home":
            draw_text_center("Stacking Plates Game", BIG_FONT, BLACK, current_content_rect.top + current_content_rect.height * 0.05)
            
            # Recalculate home button positions and sizes for the adjusted content_rect
            button_names = ["Play", "Levels", "Help", "Quit", "Leaderboard"]
            
            # Calculate total required height for buttons and spacing
            num_buttons = len(button_names)
            # Use available height for buttons, leaving some margin at top/bottom
            available_height_for_buttons = current_content_rect.height * 0.7 # Approx 70% of box height
            
            # Calculate optimal button height and spacing to fill the space
            # This will distribute buttons evenly
            total_spacing_height = available_height_for_buttons * 0.2 # 20% of available height for spacing
            button_height_calculated = (available_height_for_buttons - total_spacing_height) / num_buttons
            
            # Ensure button height is within reasonable bounds
            button_height_calculated = max(int(50 * SCALE_FACTOR), min(int(80 * SCALE_FACTOR), button_height_calculated))
            button_spacing_calculated = (available_height_for_buttons - (button_height_calculated * num_buttons)) / (num_buttons - 1) if num_buttons > 1 else 0
            button_spacing_calculated = max(int(10 * SCALE_FACTOR), button_spacing_calculated) # Min spacing

            # Recreate home buttons with dynamic dimensions for the current_content_rect
            home_buttons = []
            for i, text in enumerate(button_names):
                btn_y = current_content_rect.top + current_content_rect.height * 0.15 + i * (button_height_calculated + button_spacing_calculated)
                home_buttons.append(Button((current_content_rect.centerx - button_width_main // 2,
                                            btn_y,
                                            button_width_main, button_height_calculated), text))

            for b in home_buttons: b.draw(screen)

        elif current_screen == "levels":
            draw_text_center("Select Level", BIG_FONT, WHITE, current_content_rect.top + current_content_rect.height * 0.05)
            
            # Calculate dynamic start X for level buttons to center them within CONTENT_RECT
            total_levels_row_width = (3 * level_button_width) + (2 * level_button_x_spacing)
            start_x_levels = current_content_rect.centerx - total_levels_row_width // 2

            level_buttons = []
            for i in range(MAX_LEVELS):
                row = i // 3
                col = i % 3
                btn_x = start_x_levels + col * (level_button_width + level_button_x_spacing)
                btn_y = current_content_rect.top + current_content_rect.height * 0.15 + row * (level_button_height + level_button_y_spacing)
                level_buttons.append(Button((btn_x, btn_y, level_button_width, level_button_height),
                                             f"Level {i+1}", enabled=completed_levels[i]))


            for i, b in enumerate(level_buttons):
                b.draw(screen)
                
                level_text_surface = FONT.render(f"{i+1}", True, BLACK) # Just the number
                level_text_rect = level_text_surface.get_rect(center=b.rect.center)
                screen.blit(level_text_surface, level_text_rect)

                if not b.enabled:
                    l_icon = FONT.render("\U0001F512", True, RED)
                    screen.blit(l_icon, (b.rect.right - int(b.rect.width * 0.2) + int(5 * SCALE_FACTOR),
                                         b.rect.top + int(b.rect.height * 0.15)))
            back_button.draw(screen)

        elif current_screen == "help":
            draw_text_center("Help", BIG_FONT, BLACK, current_content_rect.top + current_content_rect.height * 0.05)
            lines = [
                "- Move ALL plates (in increasing order) onto any stack.",
                "- Visually, larger at bottom, smaller at top.",
                "- Move only one top plate at a time.",
                "- Can't place larger over smaller.",
                "- Each level adds 2 new plates.",
                "- Every 2 levels add another stack.",
                "- Click stacks to move.",
                "- Use ← Back to go back.",
                "- Press Z to undo last move.",
                "- Starts at 45 secs and increments 45 secs for every level."
            ]
            line_height = FONT.get_height() + int(8 * SCALE_FACTOR)
            start_y_help = current_content_rect.top + current_content_rect.height * 0.15
            for i, ln in enumerate(lines):
                screen.blit(FONT.render(ln, True, BLACK), (current_content_rect.left + current_content_rect.width * 0.03, start_y_help + i * line_height))
            back_button.draw(screen)

        elif current_screen == "game":
            draw_stacks()
            if not paused:
                elapsed_time = int(time.time() - start_time)
            tleft = max(0, max_time_per_level - elapsed_time)
            
            # Level number in the middle top of the game area
            level_num_text = FONT.render(f"Level: {selected_level + 1}", True, BLACK)
            level_num_rect = level_num_text.get_rect(centerx=current_content_rect.centerx,
                                                     top=current_content_rect.top + int(20 * SCALE_FACTOR))
            screen.blit(level_num_text, level_num_rect)

            # Info box for Time, Moves (top-right of CONTENT_RECT)
            info_box_width = int(200 * SCALE_FACTOR)
            info_box_height = int(70 * SCALE_FACTOR) # Adjusted height for 2 lines
            info_box_x = current_content_rect.right - info_box_width - int(10 * SCALE_FACTOR)
            info_box_y = current_content_rect.top + int(10 * SCALE_FACTOR)
            
            sb = pygame.Rect(info_box_x, info_box_y, info_box_width, info_box_height)
            pygame.draw.rect(screen, (255, 255, 200), sb, border_radius=int(6 * SCALE_FACTOR))
            pygame.draw.rect(screen, BLACK, sb, int(2 * SCALE_FACTOR), border_radius=int(6 * SCALE_FACTOR))
            
            text_padding_x = int(10 * SCALE_FACTOR)
            text_line_height = SMALL_FONT.get_height() + int(2 * SCALE_FACTOR)

            screen.blit(SMALL_FONT.render(f"Time Left: {tleft}s", True, BLACK), (sb.left + text_padding_x, sb.top + text_line_height * 0.5))
            screen.blit(SMALL_FONT.render(f"Moves: {score}", True, BLACK), (sb.left + text_padding_x, sb.top + text_line_height * 1.5))
            
            back_button.draw(screen)
            
            pause_button.text = "▶️" if paused else "⏸️"
            pause_button.draw(screen)

            if paused:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 128))
                screen.blit(overlay, (0, 0))
                draw_text_center("PAUSED", HUGE_FONT, BLACK, HEIGHT // 2 - HUGE_FONT.get_height()) # Use HUGE_FONT
                draw_text_center("Click ▶️ to Continue", FONT, BLACK, HEIGHT // 2 + FONT.get_height() // 2)


        elif current_screen == "win":
            draw_text_center("\U0001F389 CONGRATULATIONS!", HUGE_FONT, BLACK, current_content_rect.top + current_content_rect.height * 0.1)
            draw_text_center(f"Level {selected_level+1} Completed", FONT, BLACK, current_content_rect.top + current_content_rect.height * 0.25)
            draw_text_center(f"Moves: {score} | Time: {elapsed_time}s", FONT, BLACK, current_content_rect.top + current_content_rect.height * 0.35)
            win_back_button.draw(screen)
            win_next_button.enabled = (selected_level + 1 < MAX_LEVELS)
            win_next_button.draw(screen)

        elif current_screen == "timeout":
            draw_text_center("⏰ TIME'S UP!", HUGE_FONT, BLACK, current_content_rect.top + current_content_rect.height * 0.1)
            draw_text_center(f"Level {selected_level+1} failed", FONT, BLACK, current_content_rect.top + current_content_rect.height * 0.25)
            draw_text_center(f"Moves: {score} | Time: {elapsed_time}s", FONT, BLACK, current_content_rect.top + current_content_rect.height * 0.35)
            timeout_retry_button.draw(screen)
            timeout_exit_button.draw(screen)

        elif current_screen == "leaderboard":
            draw_text_center("Leaderboard", BIG_FONT, BLACK, current_content_rect.top + current_content_rect.height * 0.05)
            headers = ["Name", "Level", "Moves", "Time"]
            header_y = current_content_rect.top + current_content_rect.height * 0.15
            row_start_y = current_content_rect.top + current_content_rect.height * 0.22
            
            col_widths = [0.25, 0.15, 0.15, 0.15]
            
            current_x_offset = current_content_rect.left + current_content_rect.width * 0.05

            for i, h in enumerate(headers):
                screen.blit(FONT.render(h, True, BLACK), (current_x_offset, header_y))
                if i < len(col_widths):
                    current_x_offset += current_content_rect.width * col_widths[i]
                else:
                    current_x_offset += current_content_rect.width * (0.75 / len(headers))

            current_x_offset_data_row = current_content_rect.left + current_content_rect.width * 0.05
            
            for i, (n, lv, mv, t) in enumerate(leaderboard_data[:10]):
                temp_x_offset = current_x_offset_data_row
                for j, val in enumerate([n, str(lv), str(mv), str(t)]):
                    screen.blit(SMALL_FONT.render(val, True, RED), (temp_x_offset, row_start_y + i * (SMALL_FONT.get_height() + int(5 * SCALE_FACTOR))))
                    if j < len(col_widths):
                        temp_x_offset += current_content_rect.width * col_widths[j]
                    else:
                        temp_x_offset += current_content_rect.width * (0.75 / len(headers))
            
            back_button.draw(screen)
            clear_lb_button.draw(screen)

# --- Main loop ---
running = True
selected_stack = None
load_leaderboard()

while running:
    clock.tick(30)
    pos = pygame.mouse.get_pos()

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            running = False

        if current_screen == "start_screen":
            if e.type == pygame.MOUSEBUTTONDOWN:
                if start_game_button.is_clicked(pos):
                    current_screen = "name_prompt" # Transition to name prompt after start screen
        
        elif current_screen == "name_prompt":
            if e.type == pygame.KEYDOWN:
                if input_active:
                    if e.key == pygame.K_RETURN:
                        if len(input_text.strip()) >= 2 and input_text.strip().isalpha():
                            player_name = input_text.strip()
                            current_screen = "home"
                            input_error = ""
                        else:
                            input_error = "Name must be at least 2 alphabetic characters."
                    elif e.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                        input_error = ""
                    else:
                        if len(input_text) < 20 and e.unicode.isalpha():
                            input_text += e.unicode
                            input_error = ""
                        elif e.unicode.strip() and not e.unicode.isalpha():
                             input_error = "Only alphabetic characters allowed."

        elif e.type == pygame.MOUSEBUTTONDOWN:
            if current_screen == "home":
                for b in home_buttons: # Use the dynamically populated home_buttons
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
                                move_success = move_plate(selected_stack, cs)
                                selected_stack = None
                                
            if current_screen == "game" and not paused and is_win():
                completed_levels[selected_level] = True 
                if selected_level + 1 < MAX_LEVELS:
                    completed_levels[selected_level + 1] = True
                
                if sound_win: sound_win.play()
                
                entry_exists = False
                for idx, (name, level_lb, moves_lb, time_lb) in enumerate(leaderboard_data):
                    if name == player_name and level_lb == selected_level + 1:
                        entry_exists = True
                        if moves_lb > score or (moves_lb == score and time_lb > elapsed_time):
                            leaderboard_data[idx] = (player_name, selected_level + 1, score, elapsed_time)
                            save_leaderboard()
                        break
                
                if not entry_exists:
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