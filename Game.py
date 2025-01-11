import random
import time
import math

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Window dimensions
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

# Game element dimensions and speeds
CIRCLE_RADIUS = 20
CIRCLE_SPEED = 30  # Reduced from 60

SHIP_WIDTH = 90
SHIP_HEIGHT = 40
SHIP_SPEED = 25

BULLET_SPEED = 300

SPECIAL_CIRCLE_POINTS = 5
MAX_HEALTH = 100
HEALTH_BAR_HEIGHT = 5
HEALTH_BAR_PADDING = 20  # Increased padding
BULLET_DAMAGE = 15
OBSTACLE_DAMAGE = 10
SPECIAL_OBSTACLE_DAMAGE = 30  # New constant for special circle damage

MIDDLE_PADDING = 30  # Space between player areas
TOP_PADDING = 110  # Space from top for health bars
SIDE_PADDING = 10  # Space from sides of screen

# Add these constants after other constants
CHAR_WIDTH = 15
CHAR_HEIGHT = 20
CHAR_SPACING = 5

# Add this dictionary for basic point-based character definitions
CHAR_POINTS = {
    'A': [(0,0), (0,20), (15,20), (15,0), (0,10), (15,10)],
    'B': [(0,0), (0,20), (15,20), (15,10), (0,10), (15,0), (0,0)],
    'C': [(15,0), (0,0), (0,20), (15,20)],
    'D': [(0,0), (0,20), (10,15), (10,5), (0,0)],
    'E': [(15,0), (0,0), (0,20), (15,20), (0,10)],
    'G': [(15,0), (0,0), (0,20), (15,20), (15,10), (8,10)],
    'I': [(0,0), (15,0), (7,0), (7,20), (0,20), (15,20)],
    'L': [(0,20), (0,0), (15,0)],
    'M': [(0,0), (0,20), (7,10), (15,20), (15,0)],
    'N': [(0,0), (0,20), (15,0), (15,20)],
    'O': [(0,0), (0,20), (15,20), (15,0), (0,0)],
    'P': [(0,0), (0,20), (15,20), (15,10), (0,10)],
    'R': [(0,0), (0,20), (15,20), (15,10), (0,10), (15,0)],
    'S': [(15,0), (0,0), (0,10), (15,10), (15,20), (0,20)],
    'T': [(0,20), (15,20), (7,20), (7,0)],
    'V': [(0,20), (7,0), (15,20)],
    'W': [(0,20), (3,0), (7,10), (12,0), (15,20)],
    'Y': [(0,20), (7,10), (15,20), (7,10), (7,0)],
    '0': [(0,0), (0,20), (15,20), (15,0), (0,0)],
    '1': [(7,0), (7,20)],
    '2': [(0,20), (15,20), (15,10), (0,10), (0,0), (15,0)],
    '3': [(0,0), (15,0), (15,20), (0,20), (15,10)],
    '4': [(0,20), (0,10), (15,10), (15,20), (15,0)],
    '5': [(15,20), (0,20), (0,10), (15,10), (15,0), (0,0)],
    '!': [(7,0), (7,15), (7,20)],
    ' ': []
}

# Game state variables
current_score = 0
game_is_over = False
is_paused = True
first_start = True
last_circle_spawn_time = time.time()

# Game state variables for two players
player1_position_y = WINDOW_HEIGHT // 2
player1_position_x = SIDE_PADDING + SHIP_WIDTH  # Start farther from left edge

player2_position_y = WINDOW_HEIGHT // 2
player2_position_x = WINDOW_WIDTH - (
    SIDE_PADDING + SHIP_WIDTH
)  # Start farther from right edge

player1_score = 0
player1_health = MAX_HEALTH

player2_score = 0
player2_health = MAX_HEALTH

# Lists to store game objects
bullets_p1 = []
bullets_p2 = []
circles = []  # Single list for all circles

# Button positions
BUTTONS = {
    "start": {
        "x": WINDOW_WIDTH // 2 - 20,
        "y": WINDOW_HEIGHT - 50,
        "width": 40,
        "height": 40,
    },
    "restart": {"x": 15, "y": WINDOW_HEIGHT - 50, "width": 40, "height": 40},
    "quit": {
        "x": WINDOW_WIDTH - 65,
        "y": WINDOW_HEIGHT - 50,
        "width": 40,
        "height": 40,
    },
}

# Add game message variables
game_message = ""
score_message = ""

# Helper functions for midpoint algorithms
def draw_circle_points(cx, cy, x, y):
    glVertex2f(cx + x, cy + y)
    glVertex2f(cx - x, cy + y)
    glVertex2f(cx + x, cy - y)
    glVertex2f(cx - x, cy - y)
    glVertex2f(cx + y, cy + x)
    glVertex2f(cx - y, cy + x)
    glVertex2f(cx + y, cy - x)
    glVertex2f(cx - y, cy - x)


def draw_circle(cx, cy, radius):
    x, y = 0, radius
    decision = 1 - radius
    glBegin(GL_POINTS)
    while x <= y:
        draw_circle_points(cx, cy, x, y)
        if decision < 0:
            decision += 2 * x + 3
        else:
            decision += 2 * (x - y) + 5
            y -= 1
        x += 1
    glEnd()


def find_zone(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1

    if abs(dx) >= abs(dy):
        if dx >= 0 and dy >= 0:
            return 0
        elif dx >= 0 and dy <= 0:
            return 7
        elif dx <= 0 and dy >= 0:
            return 3
        else:
            return 4
    else:
        if dx >= 0 and dy >= 0:
            return 1
        elif dx >= 0 and dy <= 0:
            return 6
        elif dx <= 0 and dy >= 0:
            return 2
        else:
            return 5


def convert_to_zone0(x, y, zone):
    if zone == 0:
        return x, y
    elif zone == 1:
        return y, x
    elif zone == 2:
        return y, -x
    elif zone == 3:
        return -x, y
    elif zone == 4:
        return -x, -y
    elif zone == 5:
        return -y, -x
    elif zone == 6:
        return -y, x
    elif zone == 7:
        return x, -y


def convert_from_zone0(x, y, zone):
    if zone == 0:
        return x, y
    elif zone == 1:
        return y, x
    elif zone == 2:
        return -y, x
    elif zone == 3:
        return -x, y
    elif zone == 4:
        return -x, -y
    elif zone == 5:
        return -y, -x
    elif zone == 6:
        return y, -x
    elif zone == 7:
        return x, -y


def draw_line(x1, y1, x2, y2):
    # Find the zone
    zone = find_zone(x1, y1, x2, y2)

    # Convert endpoints to zone 0
    x1_prime, y1_prime = convert_to_zone0(x1, y1, zone)
    x2_prime, y2_prime = convert_to_zone0(x2, y2, zone)

    # Midpoint Line Algorithm for Zone 0
    dx = x2_prime - x1_prime
    dy = y2_prime - y1_prime
    d = 2 * dy - dx
    inc_E = 2 * dy
    inc_NE = 2 * (dy - dx)

    x = x1_prime
    y = y1_prime

    # Convert and draw initial point
    real_x, real_y = convert_from_zone0(x, y, zone)
    glVertex2f(real_x, real_y)

    while x < x2_prime:
        x += 1
        if d > 0:
            y += 1
            d += inc_NE
        else:
            d += inc_E

        # Convert point back to original zone and draw
        real_x, real_y = convert_from_zone0(x, y, zone)
        glVertex2f(real_x, real_y)


# Render spaceship as a rocket using draw_line
def render_ship(x, y, is_player_one):
    glColor3f(0, 1, 0) if is_player_one else glColor3f(1, 0.5, 0)
    glBegin(GL_POINTS)

    half_height = SHIP_HEIGHT // 2
    main_body_width = int(SHIP_WIDTH * 0.75)

    if is_player_one:
        # Player 1 (facing right)
        # Main body
        draw_line(x, y - half_height, x + main_body_width, y - half_height)
        draw_line(x, y + half_height, x + main_body_width, y + half_height)
        draw_line(x, y - half_height, x, y + half_height)
        draw_line(
            x + main_body_width, y - half_height, x + main_body_width, y + half_height
        )
        # Nose
        draw_line(x + main_body_width, y - half_height, x + SHIP_WIDTH, y)
        draw_line(x + main_body_width, y + half_height, x + SHIP_WIDTH, y)
    else:
        # Player 2 (facing left)
        # Main body
        draw_line(x, y - half_height, x - main_body_width, y - half_height)
        draw_line(x, y + half_height, x - main_body_width, y + half_height)
        draw_line(x, y - half_height, x, y + half_height)
        draw_line(
            x - main_body_width, y - half_height, x - main_body_width, y + half_height
        )
        # Nose
        draw_line(x - main_body_width, y - half_height, x - SHIP_WIDTH, y)
        draw_line(x - main_body_width, y + half_height, x - SHIP_WIDTH, y)

    glEnd()


def render_circle(x, y, radius, is_special):
    if is_special:
        radius += int(5 * math.sin(time.time() * 5))  # Animate radius
        glColor3f(1, 0.65, 0.65)  # Light red for special circles
    else:
        glColor3f(0.65, 0.65, 1)  # Light blue for regular circles
    draw_circle(x, y, radius)


def draw_play_symbol(x, y, size):
    # Triangle pointing right
    glBegin(GL_POINTS)
    draw_line(x, y, x + size, y + size // 2)
    draw_line(x + size, y + size // 2, x, y + size)
    draw_line(x, y, x, y + size)
    glEnd()


def draw_pause_symbol(x, y, size):
    # Two vertical lines
    glBegin(GL_POINTS)
    draw_line(x + size // 3, y, x + size // 3, y + size)
    draw_line(x + 2 * size // 3, y, x + 2 * size // 3, y + size)
    glEnd()


def draw_restart_symbol(x, y, size):
    # Draw 3/4 of a circle
    radius = size // 2
    center_x = x + radius
    center_y = y + radius

    glBegin(GL_POINTS)
    # Draw arc (not complete circle)
    for angle in range(-45, 270, 5):
        radian = math.radians(angle)
        px = center_x + radius * math.cos(radian)
        py = center_y + radius * math.sin(radian)
        glVertex2f(px, py)

    # Draw arrow at the end
    arrow_x = center_x + radius * math.cos(math.radians(-45))
    arrow_y = center_y + radius * math.sin(math.radians(-45))
    draw_line(
        int(arrow_x), int(arrow_y), int(arrow_x - size // 4), int(arrow_y - size // 4)
    )
    draw_line(
        int(arrow_x), int(arrow_y), int(arrow_x - size // 4), int(arrow_y + size // 4)
    )
    glEnd()


def draw_quit_symbol(x, y, size):
    # X mark
    glBegin(GL_POINTS)
    draw_line(x, y, x + size, y + size)
    draw_line(x, y + size, x + size, y)
    glEnd()


def render_buttons():
    for button, params in BUTTONS.items():
        glColor3f(1, 1, 1)
        x, y = params["x"], params["y"]
        size = params["width"]

        # Draw button outline
        glBegin(GL_POINTS)
        draw_line(x, y, x + size, y)
        draw_line(x + size, y, x + size, y + size)
        draw_line(x + size, y + size, x, y + size)
        draw_line(x, y + size, x, y)
        glEnd()

        # Draw button symbol
        if button == "start":
            if is_paused:
                draw_play_symbol(x + size // 4, y + size // 4, size // 2)
            else:
                draw_pause_symbol(x + size // 4, y + size // 4, size // 2)
        elif button == "restart":
            draw_restart_symbol(x + size // 4, y + size // 4, size // 2)
        elif button == "quit":
            draw_quit_symbol(x + size // 4, y + size // 4, size // 2)


# Update game state
def ship_collision_with_circle(ship_x, ship_y, circle_x, circle_y, circle_radius):
    # Determine if it's player 1 (facing right) or player 2 (facing left)
    is_player_one = ship_x < WINDOW_WIDTH // 2
    half_height = SHIP_HEIGHT // 2
    main_body_width = int(SHIP_WIDTH * 0.75)

    if is_player_one:
        # Player 1 (facing right) hitbox
        body_box = {
            "x": ship_x,  # Start from the left edge
            "y": ship_y - half_height,  # Center vertically
            "width": main_body_width,  # Main body width
            "height": SHIP_HEIGHT,  # Full height
        }

        # Nose hitbox for player 1
        nose_box = {
            "x": ship_x + main_body_width,  # Start from where main body ends
            "y": ship_y - half_height // 2,  # Slightly smaller height for nose
            "width": SHIP_WIDTH - main_body_width,  # Remaining width for nose
            "height": SHIP_HEIGHT // 2,  # Reduced height for nose
        }
    else:
        # Player 2 (facing left) hitbox
        body_box = {
            "x": ship_x - main_body_width,  # Start from the right edge minus body width
            "y": ship_y - half_height,  # Center vertically
            "width": main_body_width,  # Main body width
            "height": SHIP_HEIGHT,  # Full height
        }

        # Nose hitbox for player 2
        nose_box = {
            "x": ship_x - SHIP_WIDTH,  # Start from the leftmost point
            "y": ship_y - half_height // 2,  # Slightly smaller height for nose
            "width": SHIP_WIDTH - main_body_width,  # Remaining width for nose
            "height": SHIP_HEIGHT // 2,  # Reduced height for nose
        }

    # Circle hitbox
    circle_box = {
        "x": circle_x - circle_radius,
        "y": circle_y - circle_radius,
        "width": 2 * circle_radius,
        "height": 2 * circle_radius,
    }

    # Check collision with body and nose
    for box in [body_box, nose_box]:
        if (
            circle_box["x"] < box["x"] + box["width"]
            and circle_box["x"] + circle_box["width"] > box["x"]
            and circle_box["y"] < box["y"] + box["height"]
            and circle_box["y"] + circle_box["height"] > box["y"]
        ):
            return True

    return False


def update_game_state():
    global bullets_p1, bullets_p2, circles, player1_score, player2_score
    global game_is_over, last_circle_spawn_time, player1_health, player2_health
    global game_message, score_message

    if is_paused or game_is_over:
        current_time = time.time()
        for bullet in bullets_p1 + bullets_p2:
            bullet["last_update"] = current_time
        for circle in circles:
            circle["last_update"] = current_time
        return

    current_time = time.time()

    # Check bullet-bullet collisions first
    for bullet1 in bullets_p1[:]:
        for bullet2 in bullets_p2[:]:
            if (
                abs(bullet1["x"] - bullet2["x"]) < 5
                and abs(bullet1["y"] - bullet2["y"]) < 5
            ):
                if bullet1 in bullets_p1 and bullet2 in bullets_p2:
                    bullets_p1.remove(bullet1)
                    bullets_p2.remove(bullet2)
                break

    # Update bullets for both players
    for bullet in bullets_p1[:]:
        bullet["x"] += BULLET_SPEED * (current_time - bullet["last_update"])
        bullet["last_update"] = current_time
        if bullet["x"] > WINDOW_WIDTH:
            bullets_p1.remove(bullet)
            continue

        # Check if bullet hits player 2
        if (
            abs(bullet["x"] - player2_position_x) < SHIP_WIDTH / 2
            and abs(bullet["y"] - player2_position_y) < SHIP_HEIGHT / 2
        ):
            player2_health -= BULLET_DAMAGE
            bullets_p1.remove(bullet)
            if player2_health <= 0:
                game_is_over = True
                game_message = "PLAYER 1 WINS!"
                score_message = f"SCORE P1 {player1_score} P2 {player2_score}"
                print("Player 1 wins! Player 2's ship was destroyed!")
            continue

    for bullet in bullets_p2[:]:
        bullet["x"] -= BULLET_SPEED * (current_time - bullet["last_update"])
        bullet["last_update"] = current_time
        if bullet["x"] < 0:
            bullets_p2.remove(bullet)
            continue

        # Check if bullet hits player 1
        if (
            abs(bullet["x"] - player1_position_x) < SHIP_WIDTH / 2
            and abs(bullet["y"] - player1_position_y) < SHIP_HEIGHT / 2
        ):
            player1_health -= BULLET_DAMAGE
            bullets_p2.remove(bullet)
            if player1_health <= 0:
                game_is_over = True
                game_message = "PLAYER 2 WINS!"
                score_message = f"SCORE P1 {player1_score} P2 {player2_score}"
                print("Player 2 wins! Player 1's ship was destroyed!")
            continue

    # Update all circles
    for circle in circles[:]:
        circle["y"] -= CIRCLE_SPEED * (current_time - circle["last_update"])
        circle["last_update"] = current_time

        if circle["y"] < 0:
            circles.remove(circle)

    # Spawn new circles
    if current_time - last_circle_spawn_time > 3:
        # Spawn a single circle at random x position
        circles.append(
            {
                "x": random.randint(0, WINDOW_WIDTH),
                "y": WINDOW_HEIGHT,
                "radius": CIRCLE_RADIUS,
                "is_special": random.random() < 0.2,
                "last_update": current_time,
            }
        )
        last_circle_spawn_time = current_time

    # Detect collisions
    for circle in circles[:]:
        circle_box = {
            "x": circle["x"] - circle["radius"],
            "y": circle["y"] - circle["radius"],
            "width": 2 * circle["radius"],
            "height": 2 * circle["radius"],
        }
        # Check collisions with player 1's bullets
        for bullet in bullets_p1[:]:
            bullet_box = {"x": bullet["x"], "y": bullet["y"], "width": 1, "height": 1}
            if (
                circle_box["x"] < bullet_box["x"] + bullet_box["width"]
                and circle_box["x"] + circle_box["width"] > bullet_box["x"]
                and circle_box["y"] < bullet_box["y"] + bullet_box["height"]
                and circle_box["y"] + circle_box["height"] > bullet_box["y"]
            ):
                player1_score += SPECIAL_CIRCLE_POINTS if circle["is_special"] else 1
                print(f"Player 1 Score updated! Current Score: {player1_score}")
                circles.remove(circle)
                bullets_p1.remove(bullet)
                break

        # Check collisions with player 2's bullets
        if circle in circles:  # Only check if circle wasn't already removed
            for bullet in bullets_p2[:]:
                bullet_box = {
                    "x": bullet["x"],
                    "y": bullet["y"],
                    "width": 1,
                    "height": 1,
                }
                if (
                    circle_box["x"] < bullet_box["x"] + bullet_box["width"]
                    and circle_box["x"] + circle_box["width"] > bullet_box["x"]
                    and circle_box["y"] < bullet_box["y"] + bullet_box["height"]
                    and circle_box["y"] + circle_box["height"] > bullet_box["y"]
                ):
                    player2_score += (
                        SPECIAL_CIRCLE_POINTS if circle["is_special"] else 1
                    )
                    print(f"Player 2 Score updated! Current Score: {player2_score}")
                    circles.remove(circle)
                    bullets_p2.remove(bullet)
                    break

        # Check collision with player 1
        if ship_collision_with_circle(
            player1_position_x,
            player1_position_y,
            circle["x"],
            circle["y"],
            circle["radius"],
        ):
            # Apply different damage based on circle type
            damage = (
                SPECIAL_OBSTACLE_DAMAGE if circle["is_special"] else OBSTACLE_DAMAGE
            )
            player1_health -= damage
            circles.remove(circle)
            if player1_health <= 0:
                game_is_over = True
                game_message = "PLAYER 2 WINS!"
                score_message = f"SCORE P1 {player1_score} P2 {player2_score}"
                print("Player 2 wins! Player 1 crashed!")
            continue

        # Check collision with player 2
        if ship_collision_with_circle(
            player2_position_x,
            player2_position_y,
            circle["x"],
            circle["y"],
            circle["radius"],
        ):
            # Apply different damage based on circle type
            damage = (
                SPECIAL_OBSTACLE_DAMAGE if circle["is_special"] else OBSTACLE_DAMAGE
            )
            player2_health -= damage
            circles.remove(circle)
            if player2_health <= 0:
                game_is_over = True
                game_message = "PLAYER 1 WINS!"
                score_message = f"SCORE P1 {player1_score} P2 {player2_score}"
                print("Player 1 wins! Player 2 crashed!")
            continue

    glutPostRedisplay()


# Mouse interaction for buttons
def handle_mouse(button, state, x, y):
    global is_paused, game_is_over, circles, bullets_p1, bullets_p2
    global player1_score, player2_score, first_start, last_circle_spawn_time, current_score
    global player1_health, player2_health  # Add this
    global game_message, score_message

    if state == GLUT_DOWN:
        y = WINDOW_HEIGHT - y  # Adjust y for OpenGL's coordinate system
        for name, params in BUTTONS.items():
            if (
                params["x"] <= x <= params["x"] + params["width"]
                and params["y"] <= y <= params["y"] + params["height"]
            ):
                if name == "start":
                    if first_start:
                        first_start = False
                        is_paused = False
                    else:
                        is_paused = not is_paused  # Toggle pause state
                elif name == "restart":
                    player1_health = MAX_HEALTH  # Reset health
                    player2_health = MAX_HEALTH
                    player1_score = 0
                    player2_score = 0
                    current_score = 0
                    circles = []
                    bullets_p1 = []
                    bullets_p2 = []
                    game_is_over = False
                    is_paused = False  # Don't pause on restart
                    last_circle_spawn_time = time.time()  # Reset spawn timer on restart
                    game_message = ""
                    score_message = ""
                elif name == "quit":
                    print(
                        f"Final Scores - Player 1: {player1_score}, Player 2: {player2_score}. Goodbye!"
                    )
                    glutLeaveMainLoop()
                break


# Handle keyboard input
def handle_keyboard(key, x, y):
    global player1_position_y, player1_position_x, player2_position_y, player2_position_x, bullets_p1, bullets_p2, is_paused

    # Handle escape key for pause/unpause
    if key == b"\x1b":  # ASCII code for escape key
        is_paused = not is_paused
        return

    if not game_is_over and not is_paused:
        # Player 1 controls (WASD for movement, SPACE for shooting)
        if key == b"w" and player1_position_y < WINDOW_HEIGHT - TOP_PADDING:
            player1_position_y += SHIP_SPEED
        elif key == b"s" and player1_position_y > SHIP_HEIGHT + SIDE_PADDING:
            player1_position_y -= SHIP_SPEED
        elif key == b"a" and player1_position_x > SIDE_PADDING + 20:
            player1_position_x -= SHIP_SPEED
        elif (
            key == b"d"
            and player1_position_x < (WINDOW_WIDTH / 2) - SHIP_WIDTH - MIDDLE_PADDING
        ):
            player1_position_x += SHIP_SPEED
        elif key == b" ":
            bullets_p1.append(
                {
                    "x": player1_position_x + SHIP_WIDTH,
                    "y": player1_position_y,
                    "last_update": time.time(),
                }
            )

        # Player 2 controls (IJKL for movement, P for shooting)
        if key == b"i" and player2_position_y < WINDOW_HEIGHT - TOP_PADDING:
            player2_position_y += SHIP_SPEED
        elif key == b"k" and player2_position_y > SHIP_HEIGHT + SIDE_PADDING:
            player2_position_y -= SHIP_SPEED
        elif (
            key == b"j"
            and player2_position_x > (WINDOW_WIDTH / 2) + SHIP_WIDTH + MIDDLE_PADDING
        ):
            player2_position_x -= SHIP_SPEED
        elif key == b"l" and player2_position_x < WINDOW_WIDTH - SIDE_PADDING - 20:
            player2_position_x += SHIP_SPEED
        elif key == b"p":
            bullets_p2.append(
                {
                    "x": player2_position_x - SHIP_WIDTH,
                    "y": player2_position_y,
                    "last_update": time.time(),
                }
            )


# Main render function
def render_game():
    glClear(GL_COLOR_BUFFER_BIT)

    if game_is_over:
        # Render game over messages
        glColor3f(1, 1, 1)
        draw_text(WINDOW_WIDTH//4, WINDOW_HEIGHT//2, game_message, 1.5)
        draw_text(WINDOW_WIDTH//4, WINDOW_HEIGHT//2 - 40, score_message, 1)
    else:
        render_health_bars()
        render_ship(player1_position_x, player1_position_y, True)
        render_ship(player2_position_x, player2_position_y, False)

        # Render bullets
        for bullet in bullets_p1:
            draw_circle(bullet["x"], bullet["y"], 5)
        for bullet in bullets_p2:
            draw_circle(bullet["x"], bullet["y"], 5)

        # Render all circles
        for circle in circles:
            render_circle(
                circle["x"], circle["y"], circle["radius"], circle["is_special"]
            )

    render_buttons()
    glutSwapBuffers()


# health bar rendering function
def render_health_bars():
    bar_y = WINDOW_HEIGHT - (TOP_PADDING - 10)  # Position health bars with padding

    # Player 1 health bar (left side)
    # Red background
    glColor3f(1, 0, 0)
    glBegin(GL_POINTS)
    for h in range(HEALTH_BAR_HEIGHT):
        draw_line(HEALTH_BAR_PADDING, bar_y + h, WINDOW_WIDTH // 4, bar_y + h)
    glEnd()

    # Green health
    glColor3f(0, 1, 0)
    health_width = (WINDOW_WIDTH // 4 - HEALTH_BAR_PADDING) * (
        player1_health / MAX_HEALTH
    )
    glBegin(GL_POINTS)
    for h in range(HEALTH_BAR_HEIGHT):
        draw_line(
            HEALTH_BAR_PADDING, bar_y + h, HEALTH_BAR_PADDING + health_width, bar_y + h
        )
    glEnd()

    # Player 2 health bar (right side)
    # Red background
    glColor3f(1, 0, 0)
    glBegin(GL_POINTS)
    for h in range(HEALTH_BAR_HEIGHT):
        draw_line(
            WINDOW_WIDTH - WINDOW_WIDTH // 4,
            bar_y + h,
            WINDOW_WIDTH - HEALTH_BAR_PADDING,
            bar_y + h,
        )
    glEnd()

    # Green health
    glColor3f(0, 1, 0)
    health_width = (WINDOW_WIDTH // 4 - HEALTH_BAR_PADDING) * (
        player2_health / MAX_HEALTH
    )
    glBegin(GL_POINTS)
    for h in range(HEALTH_BAR_HEIGHT):
        draw_line(
            WINDOW_WIDTH - HEALTH_BAR_PADDING - health_width,
            bar_y + h,
            WINDOW_WIDTH - HEALTH_BAR_PADDING,
            bar_y + h,
        )
    glEnd()


# Add new functions for text rendering
def draw_char(x, y, char, scale=1):
    if char not in CHAR_POINTS:
        return
    
    glBegin(GL_POINTS)
    for px, py in CHAR_POINTS[char]:
        # Draw multiple points to make characters thicker
        for dx in range(2):
            for dy in range(2):
                glVertex2f(x + (px + dx) * scale, y + (py + dy) * scale)
    glEnd()

def draw_text(x, y, text, scale=1):
    current_x = x
    for char in text.upper():  # Convert to uppercase as we only defined uppercase letters
        draw_char(current_x, y, char, scale)
        current_x += (CHAR_WIDTH + CHAR_SPACING) * scale


# Initialize OpenGL
def init():
    glClearColor(0, 0, 0, 0)
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glPointSize(2.0)  # Makes all points thicker


glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
glutInitWindowPosition(500, 100)
glutCreateWindow(b"Rocket Shootout!")
init()
glutDisplayFunc(render_game)
glutIdleFunc(update_game_state)
glutKeyboardFunc(handle_keyboard)
glutMouseFunc(handle_mouse)
glutMainLoop()
