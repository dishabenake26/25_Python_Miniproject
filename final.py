import pygame
import sys
import math
import random
import json
import os
from array import array

# ================= INITIALIZATION =================
current_score = 0
level_scores = {
    1: 0,
    2: 0,
    3: 0,
    4: 0
}
high_scores = {
    1: 0,
    2: 0,
    3: 0,
    4: 0
}
SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscores.json")
def load_high_scores():
    global high_scores

    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as file:
                saved_scores = json.load(file)

            for level in range(1, 5):
                high_scores[level] = saved_scores.get(
                    str(level), 0
                )

        except (json.JSONDecodeError, OSError):
            pass
load_high_scores()

def save_high_scores():
    with open(SCORE_FILE, "w") as file:
        json.dump(high_scores, file, indent=4)

def record_level_high_score(level_number, score):
    """Keep the best score achieved in each level across game sessions."""
    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 0
    high_scores[level_number] = max(int(high_scores.get(level_number, 0)), score)
    save_high_scores()
 

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

W, H = 1000, 650
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Escape Room: The Mystery Game")
clock = pygame.time.Clock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE = os.path.join(BASE_DIR, "savegame.json")

# ================= COLORS =================
BLACK = (7, 10, 19)
WHITE = (239, 243, 250)
GOLD = (238, 184, 75)
GL = (255, 220, 132)
CYAN = (85, 225, 220)
DIM = (42, 115, 125)
RED = (255, 88, 103)
PURPLE = (127, 100, 200)
PANEL = (18, 27, 44)
MUTED = (156, 171, 193)
GREEN = (91, 224, 167)

title = pygame.font.SysFont("georgia", 48, bold=True)
large = pygame.font.SysFont("georgia", 32, bold=True)
medium = pygame.font.SysFont("georgia", 24, bold=True)
font = pygame.font.SysFont("arial", 21)
btnfont = pygame.font.SysFont("arial", 18, bold=True)
small = pygame.font.SysFont("arial", 15)
tiny = pygame.font.SysFont("arial", 12)

# ================= BACKGROUND IMAGES =================
def load_background(filename):
    path = os.path.join(BASE_DIR, filename)

    try:
        image = pygame.image.load(path).convert()
        image = pygame.transform.scale(image, (W, H))
        print("BACKGROUND LOADED:", filename)
        return image
    except (pygame.error, FileNotFoundError) as error:
        print("BACKGROUND FAILED:", filename, error)
        return None


# Keep both image files in the same folder as main.py.
room_bg = load_background("room.png")
room2_bg = load_background("room2.png")
room3_bg = load_background("room3.png")


# ================= SOUND EFFECTS =================
def tone(freq, dur=0.1, vol=0.18):
    sr = 44100
    samples = array("h")

    for i in range(int(sr * dur)):
        fade = min(1, i / 400, (sr * dur - i) / 1200)
        wave = math.sin(2 * math.pi * freq * i / sr)
        samples.append(
            int(32767 * vol * max(0, fade) * wave)
        )

    return pygame.mixer.Sound(buffer=samples.tobytes())


try:
    S_CLICK = tone(650, 0.055, 0.14)
    S_CLUE = tone(880)
    S_UNLOCK = tone(1100)
    S_KEY = tone(1320)
    S_ERR = tone(180, 0.16)
    S_WIN = tone(1047, 0.2)
except pygame.error:
    S_CLICK = S_CLUE = S_UNLOCK = S_KEY = S_ERR = S_WIN = None

sound_on = True


def play(sound):
    if sound_on and sound:
        try:
            sound.play()
        except pygame.error:
            pass


# ================= LEVELS =================
LEVELS = [
    "THE MYSTERY ROOM",
    "THE LOST ENERGY CORE",
    "THe MAZE OF SHADOWS",
    "THE CURSED ALTAR",
    "THE FORGOTTEN DUNGEON"
]

DIFF = [
    "EASY", "EASY+", "MEDIUM", "MEDIUM+",
    "HARD", "EXPERT", "FINAL"
]

TIMES = [300, 270, 240, 210, 180, 180, 180]


def load_save():
    try:
        with open(SAVE, encoding="utf-8") as f:
            data = json.load(f)

        return (
            max(1, min(5, int(data.get("unlocked", 1)))),
            max(0, int(data.get("score", 0))),
            set(data.get("completed", []))
        )
    except (OSError, ValueError, TypeError):
        return 1, 0, set()


unlocked, total_score, completed = load_save()

# ================= GAME STATE =================
level = 1
level_score = 0
page = "menu"
game_start = 0

painting = False
clock_found = False
note = False
unlocked_cupboard = False
key_found = False

code = ""
message = ""
message_until = 0

particles = [
    {
        "x": random.randrange(W),
        "y": random.randrange(H),
        "speed": random.uniform(0.25, 0.9),
        "radius": random.choice([1, 1, 2]),
        "phase": random.random() * math.tau
    }
    for _ in range(85)
]


# ================= BUTTONS =================
play_rect = pygame.Rect(70, 270, 310, 50)
levels_rect = pygame.Rect(70, 330, 310, 46)
settings_rect = pygame.Rect(70, 386, 310, 46)
board_rect = pygame.Rect(70, 442, 310, 46)
exit_rect = pygame.Rect(70, 498, 310, 46)

back = pygame.Rect(30, 25, 125, 42)

replay = pygame.Rect(100, 535, 220, 50)
next_btn = pygame.Rect(390, 535, 220, 50)
menu_btn = pygame.Rect(680, 535, 220, 50)

# Level 1 clickable objects
door = pygame.Rect(0, 80, 245, 430)
painting_rect = pygame.Rect(625, 65, 130, 190)
clock_rect = pygame.Rect(770, 145, 70, 75)
note_rect = pygame.Rect(720, 405, 65, 65)
cupboard = pygame.Rect(440, 165, 190, 270)
desk = pygame.Rect(280, 355, 700, 205)
key_rect = pygame.Rect(480, 285, 75, 75)

code_panel = pygame.Rect(300, 180, 400, 290)
code_box = pygame.Rect(385, 280, 230, 55)
submit = pygame.Rect(400, 360, 200, 48)


# ================= HELPER FUNCTIONS =================
def text(s, f, color, x, y, center=True):
    image = f.render(str(s), True, color)
    rect = image.get_rect()

    if center:
        rect.center = (int(x), int(y))
    else:
        rect.topleft = (int(x), int(y))

    screen.blit(image, rect)


def msg(s, duration=3):
    global message, message_until
    message = s
    message_until = pygame.time.get_ticks() + duration * 1000


def save():
    try:
        with open(SAVE, "w", encoding="utf-8") as f:
            json.dump({
                "unlocked": unlocked,
                "score": total_score,
                "completed": sorted(completed)
            }, f, indent=2)
    except OSError:
        pass


def bg():
    screen.fill(BLACK)

    for y in range(0, H, 3):
        t = y / H
        color = (
            int(8 + 7 * t),
            int(13 + 8 * t),
            int(25 + 15 * t)
        )
        pygame.draw.rect(screen, color, (0, y, W, 3))

    for p in particles:
        p["y"] -= p["speed"]
        p["x"] += math.sin(
            p["y"] * 0.012 + p["phase"]
        ) * 0.35

        if p["y"] < -5:
            p["y"] = H + random.randrange(50)
            p["x"] = random.randrange(W)

        color = (
            CYAN if int(p["phase"] * 10) % 3 == 0
            else GOLD
        )
        pygame.draw.circle(
            screen, color,
            (int(p["x"]), int(p["y"])),
            p["radius"]
        )


def panel(rect, fill=(8, 14, 27), border=DIM, rad=12, width=1):
    pygame.draw.rect(screen, fill, rect, border_radius=rad)
    pygame.draw.rect(
        screen, border, rect, width, border_radius=rad
    )


def glow(rect, color):
    for extra, alpha in [(10, 18), (5, 30)]:
        surface = pygame.Surface(
            (rect.w + extra * 2, rect.h + extra * 2),
            pygame.SRCALPHA
        )
        pygame.draw.rect(
            surface, (*color, alpha),
            surface.get_rect(), 3, border_radius=14
        )
        screen.blit(surface, (rect.x - extra, rect.y - extra))

    pygame.draw.rect(screen, color, rect, 2, border_radius=12)


def button(rect, label, mouse, color=CYAN, icon=None, highlight=False):
    hovered = rect.collidepoint(mouse) or highlight
    fill = (35, 43, 58) if hovered else (10, 19, 34)
    pygame.draw.rect(screen, fill, rect, border_radius=11)

    if hovered:
        glow(rect, GL if rect.collidepoint(mouse) else color)
    else:
        pygame.draw.rect(screen, color, rect, 1, border_radius=11)

    if icon:
        text(icon, btnfont, color, rect.x + 25, rect.centery)
        text(label, btnfont, WHITE, rect.centerx + 12, rect.centery)
    else:
        text(label, btnfont, WHITE, rect.centerx, rect.centery)


def target_code():
    return "258" if level == 1 else "314"


def clue_details():
    if level == 1:
        return ("PAINTING", "CLOCK", "NOTE"), ("2", "5", "8")
    return ("BOOKSHELF", "CANDLE", "SCROLL"), ("3", "1", "4")


def set_reset(number=1):
    global level, level_score, painting, clock_found, note
    global unlocked_cupboard, key_found, code, game_start

    level = number
    level_score = 0
    painting = False
    clock_found = False
    note = False
    unlocked_cupboard = False
    key_found = False
    code = ""
    game_start = pygame.time.get_ticks()

    if number == 2:
        reset_level2()
    elif number == 3:
        reset_level3()

    if number == 1:
        msg("Find the painting, clock and note. Code: 258")
    elif number == 2:
        msg("Collect energy orbs, activate switches, and secure the core.")
    elif number == 3:
        msg("Find the access card. Keep your flashlight charged and avoid the shadow!")
        # ================= MAIN MENU =================
def draw_menu(mouse):
    bg()

    art = pygame.Rect(445, 45, 510, 555)
    panel(art, (9, 17, 31), (58, 103, 124), 20, 2)

    for x in [510, 600, 690, 780, 870]:
        pygame.draw.line(
            screen, (20, 57, 76),
            (x, 70), (x, 410), 2
        )

    for y in [150, 235, 320]:
        pygame.draw.line(
            screen, (20, 57, 76),
            (475, y), (925, y), 2
        )

    door_shape = pygame.Rect(620, 135, 200, 315)
    glow(door_shape, GOLD)
    pygame.draw.rect(screen, (31, 23, 26), door_shape)
    pygame.draw.rect(screen, GL, door_shape, 3)

    inner = pygame.Rect(642, 157, 156, 270)
    pygame.draw.rect(screen, (12, 26, 40), inner)

    for i in range(5):
        pygame.draw.line(
            screen, (25, 50, 68),
            (655 + i * 30, 165), (655 + i * 30, 420), 2
        )

    pygame.draw.circle(screen, GOLD, (780, 300), 6)

    text("THE", small, CYAN, 225, 63)
    text("ESCAPE", title, GL, 225, 117)
    text("ROOM", title, GL, 225, 168)

    pygame.draw.line(screen, GOLD, (75, 205), (375, 205), 2)
    text("A MYSTERY WAITING TO BE SOLVED", tiny, MUTED, 225, 228)

    button(play_rect, "PLAY / CONTINUE", mouse, GOLD, "▶", True)
    button(levels_rect, "LEVEL SELECT", mouse, CYAN, "▦")
    button(settings_rect, "SETTINGS", mouse, CYAN, "⚙")
    button(board_rect, "LEADERBOARD", mouse, GOLD, "★")
    button(exit_rect, "EXIT GAME", mouse, PURPLE, "↪")

    text(f"UNLOCKED {unlocked}/5", tiny, CYAN, 225, 580)
    text("SEARCH  •  DISCOVER  •  ESCAPE", tiny, MUTED, 700, 555)


# ================= LEVEL SELECT =================
def draw_levels(mouse):
    bg()
    text("SELECT LEVEL", title, GL, 500, 62)
    text("Complete each mystery to unlock the next",
         small, MUTED, 500, 102)

    button(back, "← BACK", mouse, CYAN)

    panel(pygame.Rect(817, 22, 150, 48), (8, 14, 27), DIM)
    text(f"SCORE: {total_score}", small, GOLD, 892, 46)

    card_w, gap = 122, 14
    start_x = (W - (5 * card_w + 4 * gap)) // 2

    for i in range(5):
        number = i + 1
        rect = pygame.Rect(
            start_x + i * (card_w + gap), 170, card_w, 300
        )

        is_unlocked = number <= unlocked
        is_completed = number in completed

        border_color = (
            GREEN if is_completed
            else GOLD if is_unlocked
            else DIM
        )

        panel(
            rect,
            (13, 25, 39) if is_unlocked else (8, 12, 22),
            border_color, 14, 2
        )

        if is_unlocked:
            text(f"{number:02}", large, GL, rect.centerx, rect.y + 48)
            text(LEVELS[i], tiny, WHITE, rect.centerx, rect.y + 112)
            text(DIFF[i], small, CYAN, rect.centerx, rect.y + 157)

            text(
                "COMPLETED" if is_completed else "UNLOCKED",
                tiny, GREEN if is_completed else GOLD,
                rect.centerx, rect.y + 205
            )
        else:
            text("LOCKED", large, MUTED, rect.centerx, rect.y + 80)
            text("Complete previous", tiny, MUTED, rect.centerx, rect.y + 190)
            text("level", tiny, MUTED, rect.centerx, rect.y + 208)

    text("Choose an unlocked level to begin your investigation.",
         small, MUTED, 500, 530)
    text("Find clues  •  Solve puzzles  •  Escape",
         tiny, CYAN, 500, 570)


# ================= SETTINGS AND LEADERBOARD =================
def draw_simple(heading, mouse):
    bg()
    text(heading, title, GL, 500, 120)

    if heading == "SETTINGS":
        text("Control your game preferences", font, MUTED, 500, 220)
        sound_label = "SOUND: ON" if sound_on else "SOUND: OFF"
        button(
            pygame.Rect(350, 315, 300, 48),
            sound_label, mouse, GOLD
        )

    elif heading == "LEADERBOARD":
        text("YOUR ADVENTURE RECORD", medium, CYAN, 500, 220)
        text(f"Total Score: {total_score}", font, WHITE, 500, 280)
        text(f"Levels Unlocked: {unlocked}/5", font, WHITE, 500, 325)
        text(f"Levels Completed: {len(completed)}", font, WHITE, 500, 370)
        text("BEST LEVEL SCORES", medium, CYAN, 500, 430)
        text(f"L1: {high_scores[1]}     L2: {high_scores[2]}", font, GOLD, 500, 470)
        text(f"L3: {high_scores[3]}     L4: {high_scores[4]}", font, GOLD, 500, 510)

    button(back, "← BACK", mouse, CYAN)


# ================= LEVEL 1 GAME SCREEN =================
def draw_level1():
    if room_bg is not None:
        screen.blit(room_bg, (0, 0))
    else:
        bg()

    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 55))
    screen.blit(overlay, (0, 0))

    pygame.draw.rect(screen, (7, 13, 24), (0, 0, W, 58))
    pygame.draw.line(screen, GOLD, (0, 58), (W, 58), 2)

    text(LEVELS[0], medium, GL, 240, 29)

    elapsed = (pygame.time.get_ticks() - game_start) // 1000
    remaining = max(0, TIMES[0] - elapsed)
    timer_color = RED if remaining <= 30 else CYAN

    text(
        f"TIME: {remaining // 60:02}:{remaining % 60:02}",
        font, timer_color, 720, 29
    )
    text(f"SCORE: {total_score + level_score}", small, GOLD, 900, 29)

    objects = [
        (painting_rect, painting),
        (clock_rect, clock_found),
        (note_rect, note)
    ]

    for rect, found in objects:
        if found:
            pygame.draw.rect(screen, GREEN, rect, 2, border_radius=6)
        elif rect.collidepoint(pygame.mouse.get_pos()):
            glow(rect, GOLD)

    panel(
        pygame.Rect(20, 495, 330, 125),
        (7, 15, 28), DIM, 12, 2
    )
    text("CLUES DISCOVERED", small, GOLD, 185, 518)

    statuses = [
        ("PAINTING", painting),
        ("CLOCK", clock_found),
        ("NOTE", note)
    ]

    for i, (name, found) in enumerate(statuses):
        text(
            f"{name}: {'FOUND' if found else 'SEARCH'}",
            tiny, GREEN if found else MUTED,
            185, 544 + i * 22
        )

    panel(
        pygame.Rect(690, 495, 290, 125),
        (7, 15, 28), DIM, 12, 2
    )
    text("ESCAPE OBJECTIVE", small, GOLD, 835, 518)

    if not unlocked_cupboard:
        text("Find 3 clues and unlock cupboard", tiny, WHITE, 835, 548)
    elif not key_found:
        text("Cupboard unlocked!", tiny, GREEN, 835, 548)
        text("Collect the golden key", tiny, CYAN, 835, 570)
    else:
        text("KEY COLLECTED!", small, GREEN, 835, 548)
        text("Click the exit door", tiny, CYAN, 835, 572)

    if message and pygame.time.get_ticks() < message_until:
        panel(
            pygame.Rect(250, 70, 500, 55),
            (7, 15, 28), GOLD, 12, 2
        )
        text(message, small, WHITE, 500, 97)

    if unlocked_cupboard and not key_found:
        pygame.draw.circle(screen, GOLD, key_rect.center, 18, 3)
        pygame.draw.circle(screen, GL, key_rect.center, 7)
        pygame.draw.line(
            screen, GOLD,
            (key_rect.centerx + 8, key_rect.centery),
            (key_rect.centerx + 26, key_rect.centery), 4
        )
        pygame.draw.line(
            screen, GOLD,
            (key_rect.centerx + 20, key_rect.centery),
            (key_rect.centerx + 20, key_rect.centery + 8), 3
        )

    text("Click objects to investigate", tiny, WHITE, 500, 635)


# ================= GAME SCREEN ROUTER =================
def draw_game():
    if level == 2:
        draw_level2()
    else:
        draw_level1()


# ================= CODE LOCK SCREEN =================
def draw_code_screen(mouse):
    draw_game()

    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    panel(code_panel, PANEL, GOLD, 18, 2)
    text("CUPBOARD LOCK", large, GOLD, 500, 220)
    text("Enter the secret 3-digit code", font, WHITE, 500, 260)

    pygame.draw.rect(screen, BLACK, code_box, border_radius=8)
    pygame.draw.rect(screen, CYAN, code_box, 2, border_radius=8)
    text(code if code else "_ _ _", large, WHITE, 500, 307)

    button(submit, "UNLOCK", mouse, GOLD)
    text("ENTER = Submit   |   ESC = Return", small, MUTED, 500, 425)

    if painting and clock_found and note:
        text("All three clues discovered!", small, GREEN, 500, 455)


# ================= WIN / TIME-UP SCREEN =================
def draw_end_screen(won, mouse):
    bg()

    panel(
        pygame.Rect(180, 110, 640, 440),
        PANEL, GREEN if won else RED, 22, 2
    )

    if won:
        text("YOU ESCAPED!", title, GOLD, 500, 200)
        text("The mystery is solved!", font, WHITE, 500, 270)
        text("Congratulations, detective!", font, CYAN, 500, 315)
        text(f"Score earned: {level_score}", medium, GREEN, 500, 365)
    else:
        text("TIME'S UP!", title, RED, 500, 200)
        text("The mystery remains unsolved.", font, WHITE, 500, 270)
        text("Try again!", font, GOLD, 500, 315)

    button(replay, "PLAY AGAIN", mouse, GREEN)
    button(menu_btn, "MAIN MENU", mouse, CYAN)

    if level < 5:
        button(next_btn, "NEXT LEVEL", mouse, GOLD)


# ================= GAME RESET =================
def reset_game(number=1):
    global level_score, game_start, page

    set_reset(number)
    level_score = 0
    game_start = pygame.time.get_ticks()
    page = "game"
    # ================= LEVEL 2: THE LOST ENERGY CORE =================

player_speed = 4
player = pygame.Rect(70, 440, 30, 38)

energy_orbs = []
level2_switches = []
level2_lasers = []

level2_crystal = pygame.Rect(820, 150, 28, 28)
level2_portal = pygame.Rect(875, 440, 65, 85)

level2_orbs_collected = 0
level2_switch_progress = 0
level2_power_restored = False
level2_crystal_collected = False


def reset_level2():
    global player, energy_orbs, level2_switches, level2_lasers
    global level2_crystal, level2_portal
    global level2_orbs_collected, level2_switch_progress
    global level2_power_restored, level2_crystal_collected

    player = pygame.Rect(70, 440, 30, 38)

    energy_orbs = [
        pygame.Rect(185, 170, 24, 24),
        pygame.Rect(475, 395, 24, 24),
        pygame.Rect(700, 205, 24, 24)
    ]

    # Activate switches in the order 1 -> 2 -> 3.
    level2_switches = [
        pygame.Rect(300, 160, 42, 42),
        pygame.Rect(565, 275, 42, 42),
        pygame.Rect(760, 360, 42, 42)
    ]

    # Moving laser obstacles: 7 beams with different paths and speeds.
    # Horizontal lasers move left/right; vertical lasers move up/down.
    level2_lasers = [
        {
            "rect": pygame.Rect(355, 225, 125, 12),
            "axis": "x", "speed": 2.4,
            "low": 300, "high": 500
        },
        {
            "rect": pygame.Rect(610, 430, 12, 75),
            "axis": "y", "speed": 2.0,
            "low": 360, "high": 500
        },
        {
            "rect": pygame.Rect(690, 115, 115, 12),
            "axis": "x", "speed": -2.1,
            "low": 620, "high": 830
        },
        {
            # New laser 4: patrols the lower-left corridor.
            "rect": pygame.Rect(95, 315, 145, 10),
            "axis": "x", "speed": 2.7,
            "low": 75, "high": 250
        },
        {
            # New laser 5: vertical beam near the middle of the room.
            "rect": pygame.Rect(390, 345, 10, 90),
            "axis": "y", "speed": -2.3,
            "low": 300, "high": 455
        },
        {
            # New laser 6: patrols the upper-middle corridor.
            "rect": pygame.Rect(465, 95, 115, 10),
            "axis": "x", "speed": 2.0,
            "low": 400, "high": 590
        },
        {
            # New laser 7: guards the approach to the exit side.
            "rect": pygame.Rect(845, 275, 10, 90),
            "axis": "y", "speed": 2.5,
            "low": 235, "high": 375
        }
    ]

    level2_crystal = pygame.Rect(820, 150, 28, 28)
    level2_portal = pygame.Rect(875, 440, 65, 85)

    level2_orbs_collected = 0
    level2_switch_progress = 0
    level2_power_restored = False
    level2_crystal_collected = False


def level2_message(message_text):
    msg(message_text, 3)


def handle_level2_interaction():
    global level2_orbs_collected, level2_switch_progress
    global level2_power_restored, level2_crystal_collected
    global level_score, page, total_score, unlocked

    # Create a small interaction area around the player.
    interaction_area = player.inflate(30, 30)
    targets = []

    # Find nearby energy orbs.
    for orb in energy_orbs:
        if interaction_area.colliderect(orb):
            targets.append(("orb", orb))

    # Find nearby switches.
    for i, switch in enumerate(level2_switches):
        if interaction_area.colliderect(switch):
            targets.append(("switch", i))

    # Find the crystal if it is nearby and not collected.
    if (
        not level2_crystal_collected
        and interaction_area.colliderect(level2_crystal)
    ):
        targets.append(("crystal", level2_crystal))

    # Find the exit portal.
    if interaction_area.colliderect(level2_portal):
        targets.append(("portal", level2_portal))

    # No nearby object to interact with.
    if not targets:
        level2_message(
            "Move closer to an object and press E."
        )
        return

    # Calculate the distance to each target.
    def target_distance(target):
        target_type, target_obj = target

        if target_type == "switch":
            target_obj = level2_switches[target_obj]

        return math.hypot(
            player.centerx - target_obj.centerx,
            player.centery - target_obj.centery
        )

    # Interact with the nearest object only.
    target_type, target_obj = min(
        targets,
        key=target_distance
    )

    # ================= COLLECT ENERGY ORB =================
    if target_type == "orb":
        energy_orbs.remove(target_obj)
        level2_orbs_collected += 1
        level_score += 25

        play(S_CLUE)

        level2_message(
            f"Energy orb collected: "
            f"{level2_orbs_collected}/3"
        )
        return

    # ================= ACTIVATE SWITCH =================
    if target_type == "switch":
        switch_number = target_obj

        if level2_orbs_collected < 3:
            level2_message(
                "Collect all 3 energy orbs first!"
            )
            return

        # Switches must be activated in order: 1, 2, 3.
        if switch_number == level2_switch_progress:
            level2_switch_progress += 1
            level_score += 30

            play(S_UNLOCK)

            if level2_switch_progress == 3:
                level2_power_restored = True

                level2_message(
                    "Power restored! Collect the energy crystal."
                )
            else:
                next_switch = level2_switch_progress + 1

                level2_message(
                    f"Switch {switch_number + 1} activated! "
                    f"Find switch {next_switch}."
                )

        else:
            level2_switch_progress = 0

            play(S_ERR)

            level2_message(
                "Wrong switch! Start again from switch 1."
            )

        return

    # ================= COLLECT ENERGY CRYSTAL =================
    if target_type == "crystal":
        if not level2_power_restored:
            level2_message(
                "Crystal shielded! Activate all 3 switches first."
            )

        else:
            level2_crystal_collected = True
            level_score += 75

            play(S_KEY)

            level2_message(
                "Energy crystal secured! Reach the exit portal."
            )

        return

    # ================= ESCAPE THROUGH PORTAL =================
    if target_type == "portal":
        if not level2_crystal_collected:
            level2_message(
                "The portal needs the energy crystal. Find it first!"
            )
            return

        completed.add(2)
        record_level_high_score(2, level_score)

        total_score += level_score
        unlocked = max(unlocked, 3)

        save()
        play(S_WIN)

        page = "win"
        return

def update_level2():
    keys = pygame.key.get_pressed()
    dx = 0
    dy = 0

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        dx -= player_speed
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        dx += player_speed
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        dy -= player_speed
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        dy += player_speed

    if dx and dy:
        dx = int(dx * 0.7071)
        dy = int(dy * 0.7071)

    player.x += dx
    player.y += dy
    player.clamp_ip(pygame.Rect(12, 70, W - 24, H - 90))

    # Move lasers and reverse direction at their boundaries.
    for laser in level2_lasers:
        r = laser["rect"]

        if laser["axis"] == "x":
            r.x += laser["speed"]

            if r.x < laser["low"] or r.x > laser["high"]:
                laser["speed"] *= -1
                r.x = max(laser["low"], min(laser["high"], r.x))
        else:
            r.y += laser["speed"]

            if r.y < laser["low"] or r.y > laser["high"]:
                laser["speed"] *= -1
                r.y = max(laser["low"], min(laser["high"], r.y))

        if player.colliderect(r):
            player.topleft = (70, 440)
            play(S_ERR)
            level2_message("Laser hit! You were returned to the start.")


def draw_level2():
    # This explicitly uses room2.png, not the Level 1 background.
    if room2_bg is not None:
        screen.blit(room2_bg, (0, 0))
    else:
        # Clearly different fallback background if room2.png is missing.
        screen.fill((5, 12, 30))

        for x in range(25, W, 50):
            pygame.draw.line(
                screen, (14, 48, 76),
                (x, 65), (x, H), 1
            )

        for y in range(80, H, 50):
            pygame.draw.line(
                screen, (14, 48, 76),
                (0, y), (W, y), 1
            )

        pygame.draw.rect(
            screen, (9, 25, 48),
            (30, 80, 940, 520), 3, border_radius=12
        )

    # Cool blue tint makes Level 2's presentation distinctive.
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((3, 12, 38, 65))
    screen.blit(overlay, (0, 0))

    pygame.draw.rect(screen, (5, 13, 27), (0, 0, W, 58))
    pygame.draw.line(screen, CYAN, (0, 58), (W, 58), 2)

    text("THE LOST ENERGY CORE", medium, CYAN, 250, 29)

    elapsed = (pygame.time.get_ticks() - game_start) // 1000
    remaining = max(0, TIMES[1] - elapsed)

    text(
        f"TIME: {remaining // 60:02}:{remaining % 60:02}",
        font, RED if remaining <= 30 else WHITE, 700, 29
    )
    text(
        f"SCORE: {total_score + level_score}",
        small, GOLD, 900, 29
    )

    # Decorative glowing energy lines.
    for x in range(70, 950, 110):
        pygame.draw.circle(screen, (25, 90, 125), (x, 590), 4)
        pygame.draw.line(
            screen, (18, 55, 86),
            (x, 590), (x, 615), 2
        )

    # Energy orbs.
    for orb in energy_orbs:
        pulse = 2 + int((pygame.time.get_ticks() // 120) % 4)

        pygame.draw.circle(
            screen, (27, 115, 150), orb.center, 17 + pulse, 2
        )
        pygame.draw.circle(screen, CYAN, orb.center, 10)
        pygame.draw.circle(
            screen, WHITE,
            (orb.centerx - 3, orb.centery - 3), 3
        )

    # Switches.
    for i, switch in enumerate(level2_switches):
        active = i < level2_switch_progress

        color = (
            GREEN if active
            else PURPLE if level2_orbs_collected == 3
            else MUTED
        )

        pygame.draw.rect(
            screen, (15, 28, 46), switch, border_radius=8
        )
        pygame.draw.rect(
            screen, color, switch, 3, border_radius=8
        )
        pygame.draw.circle(screen, color, switch.center, 8)
        text(str(i + 1), tiny, WHITE, switch.centerx, switch.bottom + 10)

    # Moving laser beams.
    for laser in level2_lasers:
        r = laser["rect"]

        pygame.draw.rect(
            screen, (100, 18, 42),
            r.inflate(12, 12), border_radius=5
        )
        pygame.draw.rect(screen, RED, r, border_radius=4)

        if r.w > r.h:
            pygame.draw.line(
                screen, (255, 205, 210),
                (r.left + 5, r.centery),
                (r.right - 5, r.centery), 2
            )
        else:
            pygame.draw.line(
                screen, (255, 205, 210),
                (r.centerx, r.top + 5),
                (r.centerx, r.bottom - 5), 2
            )

    # Energy crystal.
    if not level2_crystal_collected:
        cx, cy = level2_crystal.center
        crystal_color = GOLD if level2_power_restored else PURPLE

        points = [
            (cx, cy - 18),
            (cx + 13, cy - 4),
            (cx + 9, cy + 14),
            (cx - 9, cy + 14),
            (cx - 13, cy - 4)
        ]

        pygame.draw.polygon(screen, crystal_color, points)
        pygame.draw.polygon(screen, WHITE, points, 2)
        pygame.draw.circle(screen, crystal_color, (cx, cy), 25, 2)

    # Exit portal.
    portal_color = GREEN if level2_crystal_collected else PURPLE

    pygame.draw.ellipse(screen, (15, 22, 42), level2_portal)
    pygame.draw.ellipse(screen, portal_color, level2_portal, 4)
    pygame.draw.ellipse(
        screen, CYAN, level2_portal.inflate(-18, -12), 2
    )
    text(
        "EXIT", tiny, WHITE,
        level2_portal.centerx, level2_portal.bottom + 10
    )

    # Player character.
    pygame.draw.circle(screen, (20, 85, 110), player.center, 26, 2)
    pygame.draw.rect(screen, CYAN, player, border_radius=8)
    pygame.draw.rect(
        screen, WHITE,
        (player.x + 6, player.y + 7, player.w - 12, 8),
        border_radius=3
    )
    pygame.draw.circle(
        screen, GOLD,
        (player.centerx, player.bottom - 5), 4
    )

    # Mission panel.
    panel(
        pygame.Rect(20, 485, 320, 130),
        (5, 13, 27), CYAN, 12, 2
    )

    text("ENERGY CORE MISSION", small, GOLD, 180, 507)
    text(
        f"Energy orbs: {level2_orbs_collected}/3",
        tiny, GREEN if level2_orbs_collected == 3 else WHITE,
        180, 533
    )
    text(
        f"Switches: {level2_switch_progress}/3",
        tiny, GREEN if level2_power_restored else WHITE,
        180, 555
    )

    crystal_status = (
        "CRYSTAL SECURED" if level2_crystal_collected
        else "CRYSTAL EXPOSED" if level2_power_restored
        else "CRYSTAL SHIELDED"
    )

    text(
        crystal_status, tiny,
        GOLD if level2_crystal_collected else MUTED,
        180, 577
    )

    if message and pygame.time.get_ticks() < message_until:
        panel(
            pygame.Rect(350, 68, 440, 42),
            (5, 13, 27), GOLD, 10, 2
        )
        text(message, small, WHITE, 570, 89)

    text(
        "MOVE: WASD / ARROWS     INTERACT: E     ESC: MENU",
        tiny, WHITE, 690, 630
    )
    # ================= LEVEL 3: THE SHADOW LABYRINTH =================
# Level 3 is a true top-down maze-survival game. The characters are drawn
# as detailed layered sprites (not simple rectangles) and can later be swapped
# for PNG sprite sheets without changing the gameplay logic.
L3_TILE = 40
l3_walls = []
l3_player = pygame.Rect(52, 102, 24, 30)
l3_monster = pygame.Rect(820, 500, 30, 34)
l3_batteries = []
l3_card = pygame.Rect(860, 90, 20, 28)
l3_exit = pygame.Rect(900, 560, 48, 58)
l3_hides = []
l3_battery = 100
l3_card_found = False
l3_monster_alert = 0
l3_last_battery = 0
l3_invulnerable_until = 0
# The maze is generated as a winding labyrinth each time Level 3 resets.
# Odd-numbered cells form corridors; randomized DFS carves connecting turns,
# leaving dead ends while guaranteeing a route from start to exit.

def generate_level3_maze():
    rows, cols = 14, 25
    grid = [['#' for _ in range(cols)] for _ in range(rows)]

    start = (1, 1)
    grid[1][1] = 'S'

    stack = [start]
    visited = {start}

    while stack:
        r, c = stack[-1]
        choices = []

        directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        random.shuffle(directions)

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if (1 <= nr < rows - 1
                    and 1 <= nc < cols - 1
                    and (nr, nc) not in visited):
                choices.append((nr, nc, dr, dc))

        if choices:
            nr, nc, dr, dc = choices[0]

            grid[r + dr // 2][c + dc // 2] = '.'
            grid[nr][nc] = '.'

            visited.add((nr, nc))
            stack.append((nr, nc))
        else:
            stack.pop()

    # Keep the starting point.
    grid[1][1] = 'S'

    # Connect the exit area to the maze.
    grid[11][23] = '.'
    grid[12][23] = '.'
    grid[11][22] = '.'

    return [''.join(row) for row in grid]
def reset_level3():
    global l3_walls, l3_player, l3_monster, l3_batteries, l3_card, l3_exit
    global l3_hides, l3_battery, l3_card_found, l3_monster_alert
    global l3_last_battery, l3_invulnerable_until
    l3_walls = []
    l3_maze = generate_level3_maze()
    for row, line in enumerate(l3_maze):
        for col, char in enumerate(line):
            if char == '#':
                l3_walls.append(pygame.Rect(col * L3_TILE, row * L3_TILE + 60, L3_TILE, L3_TILE))
    l3_player = pygame.Rect(52, 102, 24, 30)
    l3_monster = pygame.Rect(820, 500, 28, 34)
    # Place collectibles and hiding spots inside carved corridor cells.
    l3_batteries = [pygame.Rect(3 * L3_TILE + 10, 3 * L3_TILE + 70, 18, 22),
                    pygame.Rect(13 * L3_TILE + 10, 7 * L3_TILE + 70, 18, 22),
                    pygame.Rect(19 * L3_TILE + 10, 9 * L3_TILE + 70, 18, 22)]
    l3_card = pygame.Rect(23 * L3_TILE + 7, 11 * L3_TILE + 66, 24, 30)
    l3_exit = pygame.Rect(23 * L3_TILE + 1, 11 * L3_TILE + 82, 38, 38)
    l3_hides = [pygame.Rect(5 * L3_TILE + 3, 5 * L3_TILE + 64, 34, 34),
                pygame.Rect(15 * L3_TILE + 3, 3 * L3_TILE + 64, 34, 34),
                pygame.Rect(17 * L3_TILE + 3, 9 * L3_TILE + 64, 34, 34)]
    l3_battery = 100
    l3_card_found = False
    l3_monster_alert = 0
    l3_last_battery = pygame.time.get_ticks()
    l3_invulnerable_until = 0

def l3_move(rect, dx, dy):
    rect.x += int(dx)
    for wall in l3_walls:
        if rect.colliderect(wall):
            if dx > 0: rect.right = wall.left
            elif dx < 0: rect.left = wall.right
    rect.y += int(dy)
    for wall in l3_walls:
        if rect.colliderect(wall):
            if dy > 0: rect.bottom = wall.top
            elif dy < 0: rect.top = wall.bottom
    rect.clamp_ip(pygame.Rect(0, 60, W, H-60))

def draw_human_sprite(rect, monster=False):
    x, y = rect.centerx, rect.centery
    if monster:
        # Layered shadow body, claw-like limbs and luminous eyes.
        pygame.draw.ellipse(screen, (38, 18, 48), (x-18, y-16, 36, 38))
        pygame.draw.ellipse(screen, (12, 10, 22), (x-13, y-20, 26, 25))
        pygame.draw.polygon(screen, (25, 13, 35), [(x-12,y+5),(x-25,y+18),(x-15,y+13),(x-7,y+20)])
        pygame.draw.polygon(screen, (25, 13, 35), [(x+12,y+5),(x+25,y+18),(x+15,y+13),(x+7,y+20)])
        pygame.draw.circle(screen, (255, 48, 72), (x-6,y-11), 3)
        pygame.draw.circle(screen, (255, 48, 72), (x+6,y-11), 3)
        pygame.draw.circle(screen, (255, 160, 170), (x-6,y-11), 1)
        pygame.draw.circle(screen, (255, 160, 170), (x+6,y-11), 1)
    else:
        # Explorer: boots, legs, jacket, backpack, head, hair and flashlight.
        pygame.draw.ellipse(screen, (2, 5, 12), (x-13,y+8,26,10))
        pygame.draw.line(screen, (33, 49, 69), (x-5,y+4),(x-7,y+13), 5)
        pygame.draw.line(screen, (33, 49, 69), (x+5,y+4),(x+7,y+13), 5)
        pygame.draw.ellipse(screen, (10, 17, 29), (x-11,y+10,9,5))
        pygame.draw.ellipse(screen, (10, 17, 29), (x+3,y+10,9,5))
        pygame.draw.ellipse(screen, (147, 93, 57), (x-12,y-8,24,24))
        pygame.draw.ellipse(screen, (40, 78, 105), (x-10,y-7,20,22))
        pygame.draw.rect(screen, (120, 77, 46), (x-15,y-5,6,14), border_radius=3)
        pygame.draw.circle(screen, (220, 174, 133), (x,y-13), 8)
        pygame.draw.arc(screen, (35, 25, 24), (x-8,y-21,16,13), 0, math.pi, 3)
        pygame.draw.circle(screen, (28, 34, 45), (x-3,y-13), 1)
        pygame.draw.circle(screen, (28, 34, 45), (x+3,y-13), 1)
        pygame.draw.line(screen, (205, 213, 221), (x+8,y-2),(x+15,y-5), 3)
        pygame.draw.circle(screen, GOLD, (x+16,y-5), 3)

def update_level3():
    global l3_battery, l3_card_found, l3_monster_alert, l3_last_battery
    global l3_invulnerable_until, level_score, page, total_score, unlocked
    keys = pygame.key.get_pressed()
    dx = (int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])) * 3
    dy = (int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP])) * 3
    # hiding zone stops the creature noticing the player
    hiding = any(l3_player.colliderect(h) for h in l3_hides) and (keys[pygame.K_SPACE])
    l3_move(l3_player, dx, dy)
    now = pygame.time.get_ticks()
    if now - l3_last_battery > 500:
        l3_battery = max(0, l3_battery - 1)
        l3_last_battery = now
    for b in l3_batteries[:]:
        if l3_player.colliderect(b):
            l3_batteries.remove(b); l3_battery = min(100, l3_battery + 35); level_score += 15; play(S_CLUE); msg("Flashlight battery collected!")
    if not l3_card_found and l3_player.colliderect(l3_card):
        l3_card_found = True; level_score += 75; play(S_KEY); msg("Access card acquired! Reach the exit!")
    if not hiding:
        mx, my = l3_player.centerx-l3_monster.centerx, l3_player.centery-l3_monster.centery
        dist = max(1, math.hypot(mx,my))
        if dist < 310:
            l3_monster_alert = min(100, int(100 - dist/3.1))
            l3_move(l3_monster, mx/dist*1.35, my/dist*1.35)
        else:
            l3_monster_alert = max(0,l3_monster_alert-1)
    if l3_player.colliderect(l3_monster) and now > l3_invulnerable_until:
        l3_player.topleft = (62,86); l3_battery = max(15,l3_battery-20); l3_invulnerable_until = now+1800; play(S_ERR); msg("The shadow caught you! Run and hide!")
    if l3_player.colliderect(l3_exit):
        if l3_card_found:
            completed.add(3); record_level_high_score(3, level_score); total_score += level_score; unlocked = max(unlocked,4); save(); play(S_WIN); page="win"
        else: msg("Exit locked! Find the blue access card first.")

def draw_level3():
    screen.fill((5,8,18))
    # dark lab floor and tile grid
    for y in range(60,H,40):
        for x in range(0,W,40):
            pygame.draw.rect(screen, (10,18,31), (x,y,40,40))
            pygame.draw.rect(screen, (17,34,48), (x,y,40,40), 1)
    if room3_bg:
        screen.blit(room3_bg,(0,60))
    # Always draw the actual collision walls on top of the background.
    # This prevents invisible walls when room3.png is present.
    for wall in l3_walls:
        pygame.draw.rect(screen,(20,34,52),wall,border_radius=4)
        pygame.draw.rect(screen,(66,125,153),wall,2,border_radius=4)
        pygame.draw.line(screen,(35,66,84),(wall.x+5,wall.y+6),(wall.right-5,wall.y+6),1)
    # Safe hiding alcoves
    for h in l3_hides:
        pygame.draw.rect(screen,(12,48,45),h,border_radius=7); pygame.draw.rect(screen,GREEN,h,2,border_radius=7)
        pygame.draw.circle(screen,GREEN,h.center,4)
    for b in l3_batteries:
        pygame.draw.rect(screen,(255,205,70),(b.x,b.y,b.width,b.height),border_radius=4)
        pygame.draw.rect(screen,(255,245,175),(b.x+5,b.y+5,8,12),border_radius=2)
        pygame.draw.circle(screen,GOLD,b.center,13,1)
    if not l3_card_found:
        pygame.draw.rect(screen,(40,170,255),l3_card,border_radius=4); pygame.draw.rect(screen,(180,235,255),l3_card,2,border_radius=4)
        pygame.draw.line(screen,WHITE,(l3_card.x+4,l3_card.y+8),(l3_card.right-4,l3_card.y+8),2)
    pygame.draw.rect(screen,(13,63,57) if l3_card_found else (38,26,51),l3_exit,border_radius=6)
    pygame.draw.rect(screen,GREEN if l3_card_found else PURPLE,l3_exit,3,border_radius=6)
    text("EXIT",tiny,WHITE,l3_exit.centerx,l3_exit.centery)
    # Flashlight cone and darkness overlay. The cone follows the explorer.
    px,py=l3_player.center
    darkness=pygame.Surface((W,H),pygame.SRCALPHA)
    darkness.fill((0,0,8,218 if l3_battery>0 else 242))
    # The transparent inner circle creates the flashlight's visible area.
    pygame.draw.circle(darkness,(0,0,8,35 if l3_battery>0 else 175),(px,py),105)
    pygame.draw.circle(darkness,(0,0,8,100 if l3_battery>0 else 220),(px,py),145,35)
    screen.blit(darkness,(0,0))
    # Keep the characters visible over the darkness layer.
    draw_human_sprite(l3_monster,True)
    draw_human_sprite(l3_player,False)
    # Red warning glow around the monster when it is close.
    dist=math.hypot(l3_player.centerx-l3_monster.centerx,l3_player.centery-l3_monster.centery)
    if dist<220:
        pygame.draw.circle(screen,(255,50,75),l3_monster.center,35,2)
    # HUD drawn above the darkness
    pygame.draw.rect(screen,(6,12,25),(0,0,W,60)); pygame.draw.line(screen,CYAN,(0,59),(W,59),2)
    text("LEVEL 3: THE SHADOW LABYRINTH",medium,CYAN,280,27)
    elapsed=(pygame.time.get_ticks()-game_start)//1000; remaining=max(0,TIMES[2]-elapsed)
    text(f"TIME {remaining//60:02}:{remaining%60:02}",font,RED if remaining<30 else WHITE,535,27)
    text(f"SCORE {level_score}",small,GOLD,665,27)
    text("FLASHLIGHT",tiny,WHITE,770,16)
    pygame.draw.rect(screen,(50,58,72),(720,28,150,12),border_radius=5)
    pygame.draw.rect(screen,GOLD if l3_battery>25 else RED,(720,28,int(150*l3_battery/100),12),border_radius=5)
    text("CARD FOUND" if l3_card_found else "FIND ACCESS CARD",tiny,GREEN if l3_card_found else CYAN,885,27)
    if l3_monster_alert>30:
        text("SHADOW NEARBY!",small,RED,500,83)
    text("WASD/ARROWS MOVE  •  SPACE HIDE IN GREEN ZONES  •  ESC MENU",tiny,WHITE,500,635)


# ================= LEVEL 4: JUNGLE RUINS =================
LEVEL4_SOURCE = 'def _run_level4():\n\n    import pygame\n    import sys\n    import math\n    import random\n\n    pygame.init()\n\n    # =====================================================\n    # JUNGLE RUINS - ESCAPE ROOM ADVENTURE\n    # Level 1: Artifact Altar\n    # Level 2: Treasure Maze\n    # Level 3: Crystal Memory Challenge\n    # =====================================================\n\n    WIDTH, HEIGHT = 1000, 650\n    FPS = 60\n\n    screen = pygame.display.set_mode((WIDTH, HEIGHT))\n    pygame.display.set_caption("Jungle Ruins - Escape Room Adventure")\n    clock = pygame.time.Clock()\n\n    # COLORS\n    BG = (10, 19, 17)\n    PANEL = (22, 39, 31)\n    GREEN = (44, 91, 57)\n    LIGHT_GREEN = (106, 177, 111)\n    GOLD = (255, 199, 69)\n    WHITE = (240, 241, 224)\n    GREY = (103, 116, 104)\n    STONE = (65, 75, 63)\n    RED = (226, 75, 66)\n    CYAN = (95, 231, 211)\n    PURPLE = (170, 131, 228)\n    BLUE = (80, 155, 255)\n    BLACK = (5, 10, 9)\n\n    # PREMIUM GAME UI COLORS\n    DEEP_BG = (5, 12, 11)\n    JUNGLE_DARK = (9, 27, 20)\n    NEON_GREEN = (85, 255, 165)\n    DARK_PANEL = (12, 26, 23)\n    GOLD_GLOW = (255, 180, 55)\n    MUTED_GOLD = (150, 112, 43)\n\n    # Floating particles for cinematic atmosphere\n    particles = []\n\n    for i in range(65):\n        particles.append({\n            "x": random.randint(0, WIDTH),\n            "y": random.randint(0, HEIGHT),\n            "speed": random.uniform(12, 38),\n            "size": random.choice([1, 2, 2, 3]),\n            "alpha": random.randint(70, 180)\n        })\n\n\n    def update_particles(dt):\n        for p in particles:\n            p["y"] -= p["speed"] * dt\n            p["x"] += math.sin(p["y"] * 0.025) * 8 * dt\n\n            if p["y"] < -5:\n                p["y"] = HEIGHT + 5\n                p["x"] = random.randint(0, WIDTH)\n\n\n    def draw_particles():\n        for p in particles:\n            pygame.draw.circle(\n                screen,\n                GOLD_GLOW if p["size"] == 3 else NEON_GREEN,\n                (int(p["x"]), int(p["y"])),\n                p["size"]\n            )\n\n\n    def glow_circle(color, position, radius):\n        # Soft layered glow around magical objects\n        for extra, alpha in [(22, 18), (14, 28), (7, 45)]:\n            glow = pygame.Surface(\n                (radius * 2 + extra * 2, radius * 2 + extra * 2),\n                pygame.SRCALPHA\n            )\n\n            pygame.draw.circle(\n                glow,\n                (*color, alpha),\n                (glow.get_width() // 2, glow.get_height() // 2),\n                radius + extra\n            )\n\n            screen.blit(\n                glow,\n                (\n                    position[0] - glow.get_width() // 2,\n                    position[1] - glow.get_height() // 2\n                )\n            )\n\n\n    # FONTS\n    font = pygame.font.SysFont("arial", 21)\n    small = pygame.font.SysFont("arial", 16)\n    medium = pygame.font.SysFont("georgia", 29, bold=True)\n    large = pygame.font.SysFont("georgia", 49, bold=True)\n\n    # GAME VARIABLES\n    state = "ALTAR"\n    message = ""\n    message_time = 0\n    start_ticks = 0\n    TIME_LIMIT = 360\n\n    coins = 0\n    lives = 3\n    has_key = False\n    altar_solved = False\n    maze_solved = False\n\n    # -----------------------------------------------------\n    # COMMON FUNCTIONS\n    # -----------------------------------------------------\n\n    def text(msg, fnt, color, x, y, center=True):\n        image = fnt.render(str(msg), True, color)\n        rect = image.get_rect()\n\n        if center:\n            rect.center = (int(x), int(y))\n        else:\n            rect.topleft = (int(x), int(y))\n\n        screen.blit(image, rect)\n\n\n    def say(msg, seconds=2):\n        nonlocal message, message_time\n        message = msg\n        message_time = seconds\n\n\n    def panel(rect, color=PANEL, border=GOLD):\n        pygame.draw.rect(screen, color, rect, border_radius=12)\n        pygame.draw.rect(screen, border, rect, 2, border_radius=12)\n\n\n    def button(rect, label):\n        hover = rect.collidepoint(pygame.mouse.get_pos())\n\n        pygame.draw.rect(\n            screen, GREEN if hover else PANEL,\n            rect, border_radius=12\n        )\n\n        pygame.draw.rect(screen, GOLD, rect, 2, border_radius=12)\n        text(label, font, WHITE, rect.centerx, rect.centery)\n\n\n    def background():\n        screen.fill(BG)\n\n        for x in range(0, WIDTH, 70):\n            pygame.draw.rect(\n                screen, (13, 29, 22),\n                (x, 0, 34, HEIGHT)\n            )\n\n        for x in [25, 130, 850, 965]:\n            pygame.draw.line(\n                screen, GREEN, (x, 0), (x + 12, 125), 4\n            )\n\n            pygame.draw.ellipse(\n                screen, LIGHT_GREEN, (x - 9, 45, 19, 9)\n            )\n\n            pygame.draw.ellipse(\n                screen, GREEN, (x + 5, 78, 18, 9)\n            )\n\n        for y in range(100, HEIGHT, 75):\n            pygame.draw.line(\n                screen, (29, 46, 34),\n                (0, y), (WIDTH, y), 2\n            )\n\n\n    def header(title, subtitle):\n        text(title, medium, GOLD, WIDTH // 2, 37)\n        text(subtitle, small, WHITE, WIDTH // 2, 72)\n\n\n    def draw_hud():\n        pygame.draw.rect(\n            screen, BLACK, (12, 10, 255, 77), border_radius=10\n        )\n\n        pygame.draw.rect(\n            screen, GREEN, (12, 10, 255, 77), 2, border_radius=10\n        )\n\n        text("COINS: " + str(coins), font, GOLD, 27, 17, False)\n        text("LIVES: " + ("♥ " * lives), small, RED, 27, 47, False)\n\n        elapsed = (pygame.time.get_ticks() - start_ticks) / 1000\n        remaining = max(0, int(TIME_LIMIT - elapsed))\n\n        pygame.draw.rect(\n            screen, BLACK, (805, 12, 180, 38), border_radius=9\n        )\n\n        pygame.draw.rect(\n            screen, GOLD, (805, 12, 180, 38), 2, border_radius=9\n        )\n\n        text(\n            f"TIME {remaining // 60:02d}:{remaining % 60:02d}",\n            small, WHITE, 895, 31\n        )\n\n\n    def draw_message():\n        if message_time > 0 and message:\n            pygame.draw.rect(\n                screen, BLACK, (245, 87, 510, 39),\n                border_radius=9\n            )\n\n            pygame.draw.rect(\n                screen, GOLD, (245, 87, 510, 39),\n                1, border_radius=9\n            )\n\n            text(message, small, WHITE, 500, 106)\n\n\n    # =====================================================\n    # LEVEL 1: ARTIFACT ALTAR\n    # =====================================================\n\n    class Artifact(pygame.sprite.Sprite):\n\n        def __init__(self, name, aid, symbol, home, color):\n            super().__init__()\n\n            self.name = name\n            self.aid = aid\n            self.home = home\n            self.dragging = False\n            self.offset = (0, 0)\n\n            self.image = pygame.Surface((76, 76), pygame.SRCALPHA)\n\n            pygame.draw.circle(\n                self.image, STONE, (38, 38), 36\n            )\n\n            pygame.draw.circle(\n                self.image, color, (38, 38), 32, 3\n            )\n\n            symbol_img = medium.render(symbol, True, GOLD)\n\n            self.image.blit(\n                symbol_img,\n                symbol_img.get_rect(center=(38, 38))\n            )\n\n            self.rect = self.image.get_rect(topleft=home)\n\n\n    class Slot:\n\n        def __init__(self, x, y, expected, label):\n            self.rect = pygame.Rect(x, y, 90, 90)\n            self.expected = expected\n            self.label = label\n            self.item = None\n\n        def draw(self):\n            pygame.draw.rect(\n                screen, STONE, self.rect, border_radius=12\n            )\n\n            pygame.draw.rect(\n                screen,\n                GOLD if self.item else GREY,\n                self.rect, 3, border_radius=12\n            )\n\n            text(\n                self.label, small, WHITE,\n                self.rect.centerx, self.rect.bottom + 15\n            )\n\n\n    artifacts = pygame.sprite.Group()\n\n    snake = Artifact("Snake", 1, "S", (100, 465), LIGHT_GREEN)\n    jaguar = Artifact("Jaguar", 2, "J", (210, 465), GOLD)\n    monkey = Artifact("Monkey", 3, "M", (320, 465), PURPLE)\n\n    artifacts.add(snake, jaguar, monkey)\n\n    slots = [\n        Slot(665, 150, 3, "CANOPY"),\n        Slot(665, 275, 1, "CRAWL"),\n        Slot(665, 400, 2, "FLOOR"),\n    ]\n\n\n    def reset_altar():\n        nonlocal altar_solved\n\n        altar_solved = False\n\n        for slot in slots:\n            slot.item = None\n\n        for artifact in artifacts:\n            artifact.dragging = False\n            artifact.rect.topleft = artifact.home\n\n\n    def altar_event(event):\n        nonlocal altar_solved\n\n        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:\n\n            for artifact in reversed(list(artifacts)):\n\n                if artifact.rect.collidepoint(event.pos):\n\n                    artifact.dragging = True\n\n                    artifact.offset = (\n                        artifact.rect.x - event.pos[0],\n                        artifact.rect.y - event.pos[1]\n                    )\n\n                    for slot in slots:\n                        if slot.item == artifact:\n                            slot.item = None\n\n                    artifacts.remove(artifact)\n                    artifacts.add(artifact)\n                    break\n\n        elif event.type == pygame.MOUSEMOTION:\n\n            for artifact in artifacts:\n\n                if artifact.dragging:\n                    artifact.rect.x = event.pos[0] + artifact.offset[0]\n                    artifact.rect.y = event.pos[1] + artifact.offset[1]\n\n        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:\n\n            for artifact in artifacts:\n\n                if not artifact.dragging:\n                    continue\n\n                artifact.dragging = False\n                placed = False\n\n                for slot in slots:\n\n                    if artifact.rect.colliderect(slot.rect):\n                        if slot.item is None:\n\n                            slot.item = artifact\n                            artifact.rect.center = slot.rect.center\n                            placed = True\n\n                            say(artifact.name + " placed!", 1.2)\n                            break\n\n                if not placed:\n\n                    still_placed = any(\n                        slot.item == artifact for slot in slots\n                    )\n\n                    if not still_placed:\n                        artifact.rect.topleft = artifact.home\n\n            altar_solved = all(\n                slot.item is not None\n                and slot.item.aid == slot.expected\n                for slot in slots\n            )\n\n            if altar_solved:\n                say("ALTAR ACTIVATED! Press ENTER.", 3)\n\n\n    def draw_altar():\n        background()\n\n        header(\n            "THE ARTIFACT ALTAR",\n            "TRIAL 1 OF 3 | Restore the ancient mechanism"\n        )\n\n        panel(pygame.Rect(35, 120, 515, 310))\n        panel(pygame.Rect(590, 120, 335, 425))\n\n        text("ANCIENT ARTIFACTS", font, GOLD, 290, 150)\n        text("TEMPLE POSITIONS", font, GOLD, 755, 150)\n\n        text("S  Snake", small, LIGHT_GREEN, 105, 205, False)\n        text("J  Jaguar", small, GOLD, 105, 240, False)\n        text("M  Monkey", small, PURPLE, 105, 275, False)\n\n        for slot in slots:\n            slot.draw()\n\n        artifacts.draw(screen)\n\n        text(\n            "Drag each artifact into a slot.",\n            small, WHITE, 290, 370\n        )\n\n        text(\n            "Order: Monkey -> Snake -> Jaguar",\n            small, CYAN, 290, 400\n        )\n\n        if altar_solved:\n            next_rect = pygame.Rect(650, 565, 290, 54)\n            button(next_rect, "CONTINUE TO TREASURE MAZE  >")\n            text("Or press ENTER / SPACE", small, WHITE, 480, 585)\n\n        draw_hud()\n\n\n    # =====================================================\n    # LEVEL 2: TREASURE MAZE\n    # =====================================================\n\n    maze = [\n        "##########",\n        "#S..C....#",\n        "#.#.##.#.#",\n        "#.#....#.#",\n        "#...##...#",\n        "###....#.#",\n        "#C##.##..#",\n        "#....C.KE#",\n        "##########",\n    ]\n\n    TILE = 52\n    MX = 240\n    MY = 135\n\n    player_r = 1\n    player_c = 1\n    maze_coins = set()\n    key_tile = None\n    exit_tile = None\n    collected_coins = set()\n\n    trap_tiles = {(3, 3), (5, 4), (6, 7)}\n    trap_cooldown = 0\n\n\n    def setup_maze():\n        nonlocal player_r, player_c, maze_coins\n        nonlocal key_tile, exit_tile, collected_coins\n        nonlocal maze_solved, has_key, coins, lives, trap_cooldown\n\n        player_r, player_c = 1, 1\n\n        maze_coins = set()\n        collected_coins = set()\n        key_tile = None\n        exit_tile = None\n\n        trap_cooldown = 0\n        maze_solved = False\n        has_key = False\n        coins = 0\n        lives = 3\n\n        for r, row in enumerate(maze):\n\n            for c, cell in enumerate(row):\n\n                if cell == "C":\n                    maze_coins.add((r, c))\n\n                elif cell == "K":\n                    key_tile = (r, c)\n\n                elif cell == "E":\n                    exit_tile = (r, c)\n\n\n    def draw_maze():\n        background()\n\n        header(\n            "THE LOST TREASURE MAZE",\n            "TRIAL 2 OF 3 | Collect coins and find the key"\n        )\n\n        for r, row in enumerate(maze):\n\n            for c, cell in enumerate(row):\n\n                x = MX + c * TILE\n                y = MY + r * TILE\n\n                rect = pygame.Rect(\n                    x, y, TILE - 3, TILE - 3\n                )\n\n                if cell == "#":\n\n                    pygame.draw.rect(\n                        screen, STONE, rect, border_radius=6\n                    )\n\n                    pygame.draw.line(\n                        screen, (91, 101, 84),\n                        (x + 8, y + 8),\n                        (x + 39, y + 8), 2\n                    )\n\n                else:\n\n                    pygame.draw.rect(\n                        screen, (34, 64, 44),\n                        rect, border_radius=6\n                    )\n\n                pos = (r, c)\n\n                if pos in maze_coins and pos not in collected_coins:\n\n                    cx = x + TILE // 2\n                    cy = y + TILE // 2\n\n                    pulse = int(\n                        2 * math.sin(pygame.time.get_ticks() / 150)\n                    )\n\n                    pygame.draw.circle(\n                        screen, GOLD, (cx, cy), 12 + pulse\n                    )\n\n                    pygame.draw.circle(\n                        screen, WHITE, (cx, cy), 7, 2\n                    )\n\n                if pos in trap_tiles:\n                    text("!", font, RED, x + TILE // 2, y + TILE // 2)\n\n                if pos == key_tile and not has_key:\n                    text("K", medium, GOLD, x + TILE // 2, y + TILE // 2)\n\n                if pos == exit_tile:\n                    pygame.draw.rect(\n                        screen, GOLD, rect, border_radius=6\n                    )\n\n                    text(\n                        "EXIT", small, BLACK,\n                        x + TILE // 2, y + TILE // 2\n                    )\n\n        px = MX + player_c * TILE + TILE // 2\n        py = MY + player_r * TILE + TILE // 2\n\n        pygame.draw.circle(screen, CYAN, (px, py), 18)\n        pygame.draw.circle(screen, WHITE, (px, py), 18, 2)\n\n        pygame.draw.circle(screen, BLACK, (px - 6, py - 3), 2)\n        pygame.draw.circle(screen, BLACK, (px + 6, py - 3), 2)\n\n        text(\n            "Arrow keys / WASD = Move",\n            small, WHITE, 500, 620\n        )\n\n        text(\n            "KEY: " + ("FOUND" if has_key else "MISSING"),\n            small, GOLD, 100, 130\n        )\n\n        draw_hud()\n\n\n    def move_player(dr, dc):\n        nonlocal player_r, player_c, coins, has_key\n        nonlocal maze_solved, lives, state, trap_cooldown\n\n        nr = player_r + dr\n        nc = player_c + dc\n\n        if not (0 <= nr < len(maze) and 0 <= nc < len(maze[0])):\n            return\n\n        if maze[nr][nc] == "#":\n            say("Blocked by a stone wall!", 0.8)\n            return\n\n        player_r, player_c = nr, nc\n        pos = (nr, nc)\n\n        if pos in maze_coins and pos not in collected_coins:\n\n            collected_coins.add(pos)\n            coins += 10\n\n            say("+10 COINS!", 1.2)\n\n        if pos in trap_tiles and trap_cooldown <= 0:\n\n            lives -= 1\n            trap_cooldown = 1.5\n\n            say("TRAP! You lost one life.", 1.5)\n\n            if lives <= 0:\n                state = "LOSE"\n                return\n\n        if pos == key_tile and not has_key:\n\n            has_key = True\n            say("GOLDEN KEY FOUND!", 2)\n\n        if pos == exit_tile:\n\n            if has_key:\n\n                maze_solved = True\n                reset_crystals()\n                state = "CRYSTALS"\n\n                say("Gate unlocked! Enter the Crystal Chamber.", 2)\n\n            else:\n                say("Find the golden key first!", 2)\n\n\n    # =====================================================\n    # LEVEL 3: CRYSTAL MEMORY CHALLENGE\n    # =====================================================\n\n    crystal_colors = [\n        (235, 75, 83),\n        (65, 160, 255),\n        (75, 220, 135),\n        (190, 100, 245),\n    ]\n\n    crystal_names = [\n        "RUBY", "SAPPHIRE", "EMERALD", "AMETHYST"\n    ]\n\n    crystal_rects = [\n        pygame.Rect(170, 250, 150, 145),\n        pygame.Rect(365, 250, 150, 145),\n        pygame.Rect(560, 250, 150, 145),\n        pygame.Rect(755, 250, 150, 145),\n    ]\n\n    crystal_sequence = []\n    crystal_input = []\n    crystal_round = 1\n    crystal_phase = "INTRO"\n    sequence_index = 0\n    phase_timer = 0\n    lit_crystal = -1\n    crystal_flash_time = 0\n\n    CRYSTAL_ROUNDS = 3\n\n\n    def reset_crystals():\n        nonlocal crystal_sequence, crystal_input, crystal_round\n        nonlocal crystal_phase, sequence_index, phase_timer\n        nonlocal lit_crystal, crystal_flash_time\n\n        crystal_sequence = []\n        crystal_input = []\n        crystal_round = 1\n        crystal_phase = "INTRO"\n        sequence_index = 0\n        phase_timer = 0\n        lit_crystal = -1\n        crystal_flash_time = 0\n\n\n    def begin_crystal_round():\n        nonlocal crystal_sequence, crystal_input, crystal_phase\n        nonlocal sequence_index, phase_timer, lit_crystal\n\n        # Each round is longer than the previous round.\n        crystal_sequence = [\n            random.randrange(4)\n            for _ in range(crystal_round + 2)\n        ]\n\n        crystal_input = []\n        sequence_index = 0\n        phase_timer = 0.7\n        lit_crystal = -1\n        crystal_phase = "SHOW"\n\n\n    def crystal_click(index):\n        nonlocal crystal_input, crystal_phase\n        nonlocal crystal_flash_time, lit_crystal\n\n        if crystal_phase != "INPUT":\n            return\n\n        crystal_input.append(index)\n        lit_crystal = index\n        crystal_flash_time = 0.25\n\n        expected = crystal_sequence[len(crystal_input) - 1]\n\n        if index != expected:\n\n            crystal_phase = "WRONG"\n            return\n\n        if len(crystal_input) == len(crystal_sequence):\n\n            if crystal_round >= CRYSTAL_ROUNDS:\n                crystal_phase = "WIN"\n            else:\n                crystal_phase = "ROUND_COMPLETE"\n\n\n    def draw_crystal_shape(rect, color, lit=False):\n        cx, cy = rect.center\n\n        points = [\n            (cx, rect.top + 8),\n            (rect.right - 12, cy - 10),\n            (cx + 22, rect.bottom - 10),\n            (cx - 22, rect.bottom - 10),\n            (rect.left + 12, cy - 10),\n        ]\n\n        if lit:\n            pygame.draw.circle(\n                screen, color, (cx, cy), 70\n            )\n\n        pygame.draw.polygon(screen, color, points)\n\n        pygame.draw.polygon(\n            screen, WHITE if lit else GOLD, points, 3\n        )\n\n        pygame.draw.line(\n            screen, WHITE,\n            (cx, rect.top + 12),\n            (cx - 8, cy + 5), 2\n        )\n\n        pygame.draw.line(\n            screen, WHITE,\n            (cx, cy + 4),\n            (cx + 15, rect.bottom - 15), 2\n        )\n\n\n    def draw_crystals():\n        background()\n\n        header(\n            "THE CRYSTAL CHAMBER",\n            "TRIAL 3 OF 3 | Memorize the glowing sequence"\n        )\n\n        panel(pygame.Rect(75, 115, 850, 455))\n\n        text(\n            f"ROUND {min(crystal_round, CRYSTAL_ROUNDS)} / {CRYSTAL_ROUNDS}",\n            medium, GOLD, 500, 150\n        )\n\n        text(\n            "Watch the crystals light up, then repeat the sequence!",\n            small, WHITE, 500, 190\n        )\n\n        for i, rect in enumerate(crystal_rects):\n\n            lit = (\n                lit_crystal == i\n                and (\n                    crystal_phase == "SHOW"\n                    or crystal_flash_time > 0\n                )\n            )\n\n            draw_crystal_shape(\n                rect, crystal_colors[i], lit\n            )\n\n            text(\n                crystal_names[i], small, WHITE,\n                rect.centerx, rect.bottom + 20\n            )\n\n        if crystal_phase == "INTRO":\n\n            text(\n                "The temple\'s final gate is powered by four crystals.",\n                font, CYAN, 500, 475\n            )\n\n            text(\n                "Press ENTER to begin.",\n                small, WHITE, 500, 600\n            )\n\n        elif crystal_phase == "SHOW":\n\n            text(\n                "WATCH CAREFULLY!",\n                font, GOLD, 500, 475\n            )\n\n        elif crystal_phase == "INPUT":\n\n            text(\n                "YOUR TURN! Repeat the sequence.",\n                font, CYAN, 500, 475\n            )\n\n            text(\n                f"Correct presses: {len(crystal_input)} / {len(crystal_sequence)}",\n                small, WHITE, 500, 510\n            )\n\n        elif crystal_phase == "ROUND_COMPLETE":\n\n            text(\n                "ROUND COMPLETE!",\n                font, LIGHT_GREEN, 500, 475\n            )\n\n            text(\n                "Press ENTER for the next round.",\n                small, WHITE, 500, 600\n            )\n\n        elif crystal_phase == "WRONG":\n\n            text(\n                "WRONG CRYSTAL!",\n                font, RED, 500, 475\n            )\n\n            text(\n                "Press ENTER to retry this round.",\n                small, WHITE, 500, 600\n            )\n\n        elif crystal_phase == "WIN":\n\n            text(\n                "ALL CRYSTALS ACTIVATED!",\n                font, GOLD, 500, 475\n            )\n\n            text(\n                "Press ENTER to open the final gate.",\n                small, WHITE, 500, 600\n            )\n\n        draw_hud()\n\n\n    def update_crystals(dt):\n        nonlocal phase_timer, sequence_index, lit_crystal\n        nonlocal crystal_phase, crystal_flash_time\n\n        if crystal_flash_time > 0:\n\n            crystal_flash_time -= dt\n\n            if crystal_flash_time <= 0 and crystal_phase == "INPUT":\n                lit_crystal = -1\n\n        if crystal_phase == "SHOW":\n\n            phase_timer -= dt\n\n            if phase_timer <= 0:\n\n                if lit_crystal != -1:\n\n                    lit_crystal = -1\n                    phase_timer = 0.25\n\n                elif sequence_index < len(crystal_sequence):\n\n                    lit_crystal = crystal_sequence[sequence_index]\n                    sequence_index += 1\n                    phase_timer = 0.65\n\n                else:\n\n                    lit_crystal = -1\n                    crystal_phase = "INPUT"\n\n\n    # =====================================================\n    # MENU AND END SCREENS\n    # =====================================================\n\n    def draw_menu():\n        background()\n\n        text("JUNGLE RUINS", large, GOLD, 500, 160)\n        text("ESCAPE ROOM ADVENTURE", font, WHITE, 500, 215)\n\n        text(\n            "Three trials. One ancient secret. Find your way out.",\n            small, LIGHT_GREEN, 500, 258\n        )\n\n        button(pygame.Rect(350, 330, 300, 58), "START ADVENTURE")\n        button(pygame.Rect(350, 410, 300, 58), "HOW TO PLAY")\n        button(pygame.Rect(350, 490, 300, 58), "QUIT GAME")\n\n\n    def draw_instructions():\n        background()\n\n        header(\n            "YOUR MISSION",\n            "Three trials stand between you and freedom"\n        )\n\n        panel(pygame.Rect(110, 135, 780, 380))\n\n        lines = [\n            "TRIAL 1: Drag Monkey, Snake and Jaguar into the correct slots.",\n            "TRIAL 2: Explore the maze, collect coins and find the key.",\n            "Avoid red traps! You have three lives.",\n            "TRIAL 3: Watch the crystals glow, then repeat the sequence.",\n            "Each round adds one more crystal to remember.",\n            "Mouse for puzzles; arrow keys or WASD in the maze."\n        ]\n\n        for i, line in enumerate(lines):\n            text(line, small, WHITE, 150, 180 + i * 48, False)\n\n        text("Click anywhere to return", font, GOLD, 500, 560)\n\n\n    def draw_win():\n        background()\n\n        text("YOU ESCAPED!", large, GOLD, 500, 210)\n\n        text(\n            "The ancient temple has revealed its treasure.",\n            font, WHITE, 500, 280\n        )\n\n        text(\n            f"FINAL COINS: {coins}",\n            medium, GOLD, 500, 340\n        )\n\n        text(\n            "Champion of the Jungle Ruins!",\n            font, LIGHT_GREEN, 500, 390\n        )\n\n        text(\n            "ENTER = Play again     ESC = Menu",\n            small, WHITE, 500, 470\n        )\n\n\n    def draw_lose():\n        background()\n\n        text("ADVENTURE OVER", large, RED, 500, 220)\n\n        text(\n            "You ran out of time or lost all your lives.",\n            font, WHITE, 500, 300\n        )\n\n        text(\n            "ENTER = Try again     ESC = Menu",\n            small, GOLD, 500, 390\n        )\n\n\n    def reset_game():\n        nonlocal state, start_ticks, coins, lives, has_key\n        nonlocal altar_solved, maze_solved\n\n        coins = 0\n        lives = 3\n        has_key = False\n        altar_solved = False\n        maze_solved = False\n\n        reset_altar()\n        setup_maze()\n        reset_crystals()\n\n        start_ticks = pygame.time.get_ticks()\n        state = "ALTAR"\n\n\n    # =====================================================\n    # MAIN LOOP\n    # =====================================================\n\n    setup_maze()\n    reset_crystals()\n\n    running = True\n\n    while running:\n\n        dt = clock.tick(FPS) / 1000.0\n\n        if message_time > 0:\n            message_time -= dt\n\n        if state in ("ALTAR", "MAZE", "CRYSTALS") and start_ticks:\n\n            elapsed = (pygame.time.get_ticks() - start_ticks) / 1000\n\n            if elapsed >= TIME_LIMIT:\n                state = "LOSE"\n\n        if trap_cooldown > 0:\n            trap_cooldown -= dt\n\n        if state == "CRYSTALS":\n            update_crystals(dt)\n\n        for event in pygame.event.get():\n\n            if event.type == pygame.QUIT:\n                running = False\n\n            if event.type == pygame.KEYDOWN:\n\n                if event.key == pygame.K_ESCAPE:\n                    if state == "MENU":\n                        running = False\n                    else:\n                        state = "MENU"\n\n                elif state == "ALTAR" and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):\n\n                    if altar_solved:\n                        state = "MAZE"\n                        say("TRIAL 1 COMPLETE! Find the key and reach the exit.", 4)\n                    else:\n                        say("Place Monkey, Snake and Jaguar correctly first.", 3)\n\n                elif state == "MAZE":\n\n                    if event.key in (pygame.K_UP, pygame.K_w):\n                        move_player(-1, 0)\n\n                    elif event.key in (pygame.K_DOWN, pygame.K_s):\n                        move_player(1, 0)\n\n                    elif event.key in (pygame.K_LEFT, pygame.K_a):\n                        move_player(0, -1)\n\n                    elif event.key in (pygame.K_RIGHT, pygame.K_d):\n                        move_player(0, 1)\n\n                elif state == "CRYSTALS":\n\n                    if event.key == pygame.K_RETURN:\n\n                        if crystal_phase == "INTRO":\n\n                            begin_crystal_round()\n\n                        elif crystal_phase == "ROUND_COMPLETE":\n\n                            crystal_round += 1\n                            begin_crystal_round()\n\n                        elif crystal_phase == "WRONG":\n\n                            lives -= 1\n\n                            if lives <= 0:\n                                state = "LOSE"\n                            else:\n                                begin_crystal_round()\n\n                        elif crystal_phase == "WIN":\n\n                            state = "WIN"\n\n                elif state == "WIN" and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):\n                    running = False\n                elif state == "LOSE" and event.key == pygame.K_RETURN:\n                    reset_game()\n\n            if state == "MENU" and event.type == pygame.MOUSEBUTTONDOWN:\n\n                if event.button == 1 and pygame.Rect(350, 330, 300, 58).collidepoint(event.pos):\n                    reset_game()\n                    say("Trial 1: Place the artifacts in the correct order.", 3)\n\n                elif pygame.Rect(350, 410, 300, 58).collidepoint(event.pos):\n                    state = "INSTRUCTIONS"\n\n                elif pygame.Rect(350, 490, 300, 58).collidepoint(event.pos):\n                    running = False\n\n            elif state == "INSTRUCTIONS" and event.type == pygame.MOUSEBUTTONDOWN:\n                state = "MENU"\n\n            elif state == "ALTAR":\n                if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1\n                        and altar_solved\n                        and pygame.Rect(650, 565, 290, 54).collidepoint(event.pos)):\n                    state = "MAZE"\n                    say("TRIAL 1 COMPLETE! Find the key and reach the exit.", 4)\n                else:\n                    altar_event(event)\n\n            elif state == "CRYSTALS" and event.type == pygame.MOUSEBUTTONDOWN:\n\n                if event.button == 1:\n\n                    for i, rect in enumerate(crystal_rects):\n\n                        if rect.collidepoint(event.pos):\n                            crystal_click(i)\n                            break\n\n        if state == "MENU":\n            draw_menu()\n\n        elif state == "INSTRUCTIONS":\n            draw_instructions()\n\n        elif state == "ALTAR":\n            artifacts.update(pygame.mouse.get_pos())\n            draw_altar()\n\n        elif state == "MAZE":\n            draw_maze()\n\n        elif state == "CRYSTALS":\n            draw_crystals()\n\n        elif state == "WIN":\n            draw_win()\n\n        elif state == "LOSE":\n            draw_lose()\n\n        draw_message()\n        pygame.display.flip()\n\n    _level4_result = (state == "WIN")\n    return _level4_result\n'


def run_level4():
    """Play the Jungle Ruins level and return to the main level selector."""
    namespace = {
        "__name__": "__level4__", "pygame": pygame, "sys": sys,
        "math": math, "random": random
    }
    exec(compile(LEVEL4_SOURCE, "<Level 4>", "exec"), namespace)
    return bool(namespace["_run_level4"]())

# ================= MAIN LOOP =================
running = True

while running:
    clock.tick(60)
    mouse = pygame.mouse.get_pos()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False


        # ================= KEYBOARD INPUT =================
        if event.type == pygame.KEYDOWN:

            # Level 2 interaction
            if (
                page == "game"
                and level == 2
                and event.key == pygame.K_e
            ):
                handle_level2_interaction()

            # Escape key
            if event.key == pygame.K_ESCAPE:
                if page == "code":
                    page = "game"
                elif page != "menu":
                    page = "menu"

            # Code entry
            elif page == "code":

                if event.key == pygame.K_BACKSPACE:
                    code = code[:-1]

                elif event.key == pygame.K_RETURN:
                    if code == target_code():
                        unlocked_cupboard = True
                        level_score += 100
                        play(S_UNLOCK)
                        page = "game"
                        msg("Cupboard unlocked! Find the golden key.")
                    else:
                        play(S_ERR)
                        msg("Incorrect code. Try again.")
                        code = ""

                elif event.unicode.isdigit() and len(code) < 3:
                    code += event.unicode

        # ================= MOUSE INPUT =================
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            # ---------- MAIN MENU ----------
            if page == "menu":

                if play_rect.collidepoint(event.pos):
                    reset_game(min(level, unlocked))

                elif levels_rect.collidepoint(event.pos):
                    page = "levels"

                elif settings_rect.collidepoint(event.pos):
                    page = "settings"

                elif board_rect.collidepoint(event.pos):
                    page = "leaderboard"

                elif exit_rect.collidepoint(event.pos):
                    running = False

            # ---------- LEVEL SELECTION ----------
            elif page == "levels":

                if back.collidepoint(event.pos):
                    page = "menu"

                else:
                    card_w, gap = 122, 14
                    start_x = (W - (5 * card_w + 4 * gap)) // 2

                    for i in range(5):
                        rect = pygame.Rect(
                            start_x + i * (card_w + gap),
                            170, card_w, 300
                        )

                        if rect.collidepoint(event.pos):
                            chosen = i + 1

                            if chosen <= unlocked:
                                if chosen in (1, 2, 3):
                                    reset_game(chosen)
                                elif chosen == 4:
                                    try:
                                        level4_won = run_level4()
                                        if level4_won:
                                            record_level_high_score(4, level_score)
                                            completed.add(4)
                                            unlocked = max(unlocked, 5)
                                            save()
                                            msg("JUNGLE RUINS COMPLETED!")
                                        page = "levels"
                                    except Exception as exc:
                                        page = "levels"
                                        msg("Level 4 error: " + str(exc)[:45])
                                else:
                                    msg("Level 5 is not built yet.")
                            break

            # ---------- SETTINGS ----------
            elif page == "settings":

                if back.collidepoint(event.pos):
                    page = "menu"

                elif pygame.Rect(
                    350, 315, 300, 48
                ).collidepoint(event.pos):
                    sound_on = not sound_on

            # ---------- LEADERBOARD ----------
            elif page == "leaderboard":

                if back.collidepoint(event.pos):
                    page = "menu"

            # ---------- LEVEL 1 GAMEPLAY ----------
            elif page == "game" and level == 1:

                # Check the key first, then always allow the door to be clicked.
                # Previously, all object handling was skipped once key_found became True,
                # so the door click could never reach its success branch.
                if unlocked_cupboard and not key_found and key_rect.collidepoint(event.pos):
                    key_found = True
                    level_score += 50
                    play(S_KEY)
                    msg("Golden key collected! Click the exit door.")

                elif door.collidepoint(event.pos):
                    if key_found:
                        page = "win"
                        completed.add(1)
                        record_level_high_score(1, level_score)
                        total_score += level_score
                        unlocked = max(unlocked, 2)
                        save()
                        play(S_WIN)
                    else:
                        msg("The exit is locked. Find the golden key!")

                elif not key_found:
                    clue_names, clue_digits = clue_details()

                    if painting_rect.collidepoint(event.pos):
                        if not painting:
                            painting = True
                            level_score += 20
                            play(S_CLUE)

                        msg(
                            f"Painting clue: first digit is "
                            f"{clue_digits[0]}."
                        )

                    elif clock_rect.collidepoint(event.pos):
                        if not clock_found:
                            clock_found = True
                            level_score += 20
                            play(S_CLUE)

                        msg(
                            f"Clock clue: second digit is "
                            f"{clue_digits[1]}."
                        )

                    elif note_rect.collidepoint(event.pos):
                        if not note:
                            note = True
                            level_score += 20
                            play(S_CLUE)

                        msg(
                            f"Note clue: final digit is "
                            f"{clue_digits[2]}."
                        )

                    elif cupboard.collidepoint(event.pos):
                        if unlocked_cupboard:
                            msg("The cupboard is open. Collect the key!")

                        elif painting and clock_found and note:
                            page = "code"
                            code = ""

                        else:
                            msg("Find all three clues first!")

                    elif desk.collidepoint(event.pos):
                        msg("Investigate the objects around the room.")

            # ---------- CODE SUBMIT ----------
            elif page == "code":

                if submit.collidepoint(event.pos):
                    if code == target_code():
                        unlocked_cupboard = True
                        level_score += 100
                        play(S_UNLOCK)
                        page = "game"
                        msg("Cupboard unlocked! Find the golden key.")
                    else:
                        play(S_ERR)
                        msg("Incorrect code. Try again.")
                        code = ""

            # ---------- END SCREENS ----------
            elif page in ("win", "timeup"):

                if replay.collidepoint(event.pos):
                    reset_game(level)

                elif menu_btn.collidepoint(event.pos):
                    page = "menu"

                elif next_btn.collidepoint(event.pos):
                    if level < 5 and level + 1 <= unlocked:
                        if level + 1 in (1, 2, 3):
                            reset_game(level + 1)
                        elif level+1==4:
                            page='levels'
                            msg("LEVEL 4 UNLOCKED! Select Level 4 to begin.")
                        else:
                            msg("This room has not been built yet.")
                

    # ================= TIMER AND UPDATES =================
    if page == "game":

        if level == 2:
            update_level2()
        elif level == 3:
            update_level3()

        elapsed = (
            pygame.time.get_ticks() - game_start
        ) // 1000

        if elapsed >= TIMES[level - 1]:
            page = "timeup"

    # ================= DRAW SCREEN =================
    if page == "menu":
        draw_menu(mouse)

    elif page == "levels":
        draw_levels(mouse)

    elif page == "settings":
        draw_simple("SETTINGS", mouse)

    elif page == "leaderboard":
        draw_simple("LEADERBOARD", mouse)

    elif page == "game":
        if level == 3:
            draw_level3()
        else:
            draw_game()

    elif page == "code":
        draw_code_screen(mouse)

    elif page == "win":
        draw_end_screen(True, mouse)

    elif page == "timeup":
        draw_end_screen(False, mouse)


    pygame.display.flip()


# ================= CLOSE GAME =================
save()
pygame.quit()
sys.exit()