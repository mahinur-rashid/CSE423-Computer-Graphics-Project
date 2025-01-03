import random
import time
import math

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Window dimensions
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600

# Game element dimensions and speeds
CIRCLE_RADIUS = 20
CIRCLE_SPEED = 60

SHIP_WIDTH = 90
SHIP_HEIGHT = 40
SHIP_SPEED = 20

BULLET_SPEED = 300

SPECIAL_CIRCLE_POINTS = 5
MAX_MISSED_CIRCLES = 3

# Game state variables
current_score = 0
player1_missed_circles = 0  # Separate counter for player 1
player2_missed_circles = 0  # Separate counter for player 2
game_is_over = False
is_paused = True
first_start = True
last_circle_spawn_time = time.time()

# Game state variables for two players
player1_position_y = WINDOW_HEIGHT // 2
player1_position_x = 50
player1_score = 0

player2_position_y = WINDOW_HEIGHT // 2
player2_position_x = WINDOW_WIDTH - 50
player2_score = 0

# Lists to store game objects
bullets_p1 = []
bullets_p2 = []
circles_p1 = []  # Circles moving towards player 1
circles_p2 = []  # Circles moving towards player 2

# Button positions
BUTTONS = {
    "start": {"x": WINDOW_WIDTH // 2, "y": WINDOW_HEIGHT - 50, "width": 40, "height": 40},
    "restart": {"x": 15, "y": WINDOW_HEIGHT - 50, "width": 40, "height": 40},
    "quit": {"x": WINDOW_WIDTH - 65, "y": WINDOW_HEIGHT - 50, "width": 40, "height": 40},
}
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
        if dx >= 0 and dy >= 0: return 0
        elif dx >= 0 and dy <= 0: return 7
        elif dx <= 0 and dy >= 0: return 3
        else: return 4
    else:
        if dx >= 0 and dy >= 0: return 1
        elif dx >= 0 and dy <= 0: return 6
        elif dx <= 0 and dy >= 0: return 2
        else: return 5

def convert_to_zone0(x, y, zone):
    if zone == 0: return x, y
    elif zone == 1: return y, x
    elif zone == 2: return y, -x
    elif zone == 3: return -x, y
    elif zone == 4: return -x, -y
    elif zone == 5: return -y, -x
    elif zone == 6: return -y, x
    elif zone == 7: return x, -y

def convert_from_zone0(x, y, zone):
    if zone == 0: return x, y
    elif zone == 1: return y, x
    elif zone == 2: return -y, x
    elif zone == 3: return -x, y
    elif zone == 4: return -x, -y
    elif zone == 5: return -y, -x
    elif zone == 6: return y, -x
    elif zone == 7: return x, -y

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
    nose_width = SHIP_WIDTH - main_body_width

    # Main body
    draw_line(x, y - half_height, x + main_body_width, y - half_height)
    draw_line(x, y + half_height, x + main_body_width, y + half_height)
    draw_line(x, y - half_height, x, y + half_height)
    
    if is_player_one:
        # Player 1 (facing right)
        draw_line(x + main_body_width, y - half_height, x + main_body_width, y + half_height)
        # Nose
        draw_line(x + main_body_width, y - half_height, x + SHIP_WIDTH, y)
        draw_line(x + main_body_width, y + half_height, x + SHIP_WIDTH, y)
    else:
        # Player 2 (facing left)
        draw_line(x - main_body_width, y - half_height, x - main_body_width, y + half_height)
        # Nose
        draw_line(x - main_body_width, y - half_height, x - SHIP_WIDTH, y)
        draw_line(x - main_body_width, y + half_height, x - SHIP_WIDTH, y)

    glEnd()

def render_circle(x, y, radius, is_special):
    if is_special:
        radius += int(5 * math.sin(time.time() * 5))  # Animate radius
    glColor3f(1, 0, 0) if is_special else glColor3f(0, 0, 1)
    draw_circle(x, y, radius)

def draw_play_symbol(x, y, size):
    # Triangle pointing right
    glBegin(GL_POINTS)
    draw_line(x, y, x + size, y + size//2)
    draw_line(x + size, y + size//2, x, y + size)
    draw_line(x, y, x, y + size)
    glEnd()

def draw_pause_symbol(x, y, size):
    # Two vertical lines
    glBegin(GL_POINTS)
    draw_line(x + size//3, y, x + size//3, y + size)
    draw_line(x + 2*size//3, y, x + 2*size//3, y + size)
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
    draw_line(int(arrow_x), int(arrow_y), int(arrow_x - size//4), int(arrow_y - size//4))
    draw_line(int(arrow_x), int(arrow_y), int(arrow_x - size//4), int(arrow_y + size//4))
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
        x, y = params['x'], params['y']
        size = params['width']
        
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
                draw_play_symbol(x + size//4, y + size//4, size//2)
            else:
                draw_pause_symbol(x + size//4, y + size//4, size//2)
        elif button == "restart":
            draw_restart_symbol(x + size//4, y + size//4, size//2)
        elif button == "quit":
            draw_quit_symbol(x + size//4, y + size//4, size//2)

# Update game state
def check_ship_collision(ship_x, ship_y, circle_x, circle_y, circle_radius):
    # Ship hitbox components
    half_width = SHIP_WIDTH // 2
    main_body_height = int(SHIP_HEIGHT * 0.75)
    
    # Main body hitbox
    body_box = {
        'x': ship_x - half_width,
        'y': ship_y,
        'width': SHIP_WIDTH,
        'height': main_body_height
    }
    
    # Wings hitbox (wider at the bottom)
    wing_box = {
        'x': ship_x - SHIP_WIDTH,
        'y': ship_y,
        'width': SHIP_WIDTH * 2,
        'height': main_body_height // 3
    }
    
    # Nose hitbox (triangle approximated as rectangle)
    nose_box = {
        'x': ship_x - half_width,
        'y': ship_y + main_body_height,
        'width': SHIP_WIDTH,
        'height': SHIP_HEIGHT - main_body_height
    }
    
    # Circle hitbox
    circle_box = {
        'x': circle_x - circle_radius,
        'y': circle_y - circle_radius,
        'width': 2 * circle_radius,
        'height': 2 * circle_radius
    }
    
    # Check collision with each ship component
    for box in [body_box, wing_box, nose_box]:
        if (circle_box['x'] < box['x'] + box['width'] and
            circle_box['x'] + circle_box['width'] > box['x'] and
            circle_box['y'] < box['y'] + box['height'] and
            circle_box['y'] + circle_box['height'] > box['y']):
            return True
            
    return False

def update_game_state():
    global bullets_p1, bullets_p2, circles_p1, circles_p2, player1_score, player2_score
    global game_is_over, last_circle_spawn_time, player1_missed_circles, player2_missed_circles

    if is_paused or game_is_over:
        current_time = time.time()
        for bullet in bullets_p1 + bullets_p2:
            bullet['last_update'] = current_time
        for circle in circles_p1 + circles_p2:
            circle['last_update'] = current_time
        return

    current_time = time.time()

    # Update bullets for both players
    for bullet in bullets_p1[:]:
        bullet['x'] += BULLET_SPEED * (current_time - bullet['last_update'])
        bullet['last_update'] = current_time
        if bullet['x'] > WINDOW_WIDTH:
            bullets_p1.remove(bullet)
            continue
        
        # Check if bullet hits player 2
        if (abs(bullet['x'] - player2_position_x) < SHIP_WIDTH/2 and
            abs(bullet['y'] - player2_position_y) < SHIP_HEIGHT/2):
            game_is_over = True
            print("Player 1 wins! Player 2's ship was destroyed!")
            return

    for bullet in bullets_p2[:]:
        bullet['x'] -= BULLET_SPEED * (current_time - bullet['last_update'])
        bullet['last_update'] = current_time
        if bullet['x'] < 0:
            bullets_p2.remove(bullet)
            continue
        
        # Check if bullet hits player 1
        if (abs(bullet['x'] - player1_position_x) < SHIP_WIDTH/2 and
            abs(bullet['y'] - player1_position_y) < SHIP_HEIGHT/2):
            game_is_over = True
            print("Player 2 wins! Player 1's ship was destroyed!")
            return

    # Update circles for player 1
    for circle in circles_p1[:]:
        circle['x'] -= CIRCLE_SPEED * (current_time - circle['last_update'])
        circle['last_update'] = current_time

        if circle['x'] < 0:
            circles_p1.remove(circle)
            player1_missed_circles += 1
            print(f"Player 1 Missed Circles: {player1_missed_circles}")
            if player1_missed_circles >= MAX_MISSED_CIRCLES:
                game_is_over = True
                print("Player 2 wins! Player 1 missed too many circles!")
                return

    # Update circles for player 2
    for circle in circles_p2[:]:
        circle['x'] += CIRCLE_SPEED * (current_time - circle['last_update'])
        circle['last_update'] = current_time

        if circle['x'] > WINDOW_WIDTH:
            circles_p2.remove(circle)
            player2_missed_circles += 1
            print(f"Player 2 Missed Circles: {player2_missed_circles}")
            if player2_missed_circles >= MAX_MISSED_CIRCLES:
                game_is_over = True
                print("Player 1 wins! Player 2 missed too many circles!")
                return

    # Spawn new circles
    if current_time - last_circle_spawn_time > 2:
        # Spawn circle for player 1 (from right)
        circles_p1.append({
            'x': WINDOW_WIDTH,
            'y': random.randint(CIRCLE_RADIUS, WINDOW_HEIGHT - CIRCLE_RADIUS),
            'radius': CIRCLE_RADIUS,
            'is_special': random.random() < 0.2,
            'last_update': current_time
        })
        # Spawn circle for player 2 (from left)
        circles_p2.append({
            'x': 0,
            'y': random.randint(CIRCLE_RADIUS, WINDOW_HEIGHT - CIRCLE_RADIUS),
            'radius': CIRCLE_RADIUS,
            'is_special': random.random() < 0.2,
            'last_update': current_time
        })
        last_circle_spawn_time = current_time

    # Detect collisions
    for circle in circles_p1[:]:
        circle_box = {
            'x': circle['x'] - circle['radius'],
            'y': circle['y'] - circle['radius'],
            'width': 2 * circle['radius'],
            'height': 2 * circle['radius']
        }
        for bullet in bullets_p1[:]:
            bullet_box = {
                'x': bullet['x'],
                'y': bullet['y'],
                'width': 1,
                'height': 1
            }
            if (circle_box['x'] < bullet_box['x'] + bullet_box['width'] and
                circle_box['x'] + circle_box['width'] > bullet_box['x'] and
                circle_box['y'] < bullet_box['y'] + bullet_box['height'] and
                circle_box['y'] + circle_box['height'] > bullet_box['y']):
                player1_score += SPECIAL_CIRCLE_POINTS if circle['is_special'] else 1
                print(f"Player 1 Score updated! Current Score: {player1_score}")
                circles_p1.remove(circle)
                bullets_p1.remove(bullet)
                break
        for bullet in bullets_p2[:]:
            bullet_box = {
                'x': bullet['x'],
                'y': bullet['y'],
                'width': 1,
                'height': 1
            }
            if (circle_box['x'] < bullet_box['x'] + bullet_box['width'] and
                circle_box['x'] + circle_box['width'] > bullet_box['x'] and
                circle_box['y'] < bullet_box['y'] + bullet_box['height'] and
                circle_box['y'] + circle_box['height'] > bullet_box['y']):
                player2_score += SPECIAL_CIRCLE_POINTS if circle['is_special'] else 1
                print(f"Player 2 Score updated! Current Score: {player2_score}")
                circles_p1.remove(circle)
                bullets_p2.remove(bullet)
                break

    for circle in circles_p2[:]:
        circle_box = {
            'x': circle['x'] - circle['radius'],
            'y': circle['y'] - circle['radius'],
            'width': 2 * circle['radius'],
            'height': 2 * circle['radius']
        }
        for bullet in bullets_p1[:]:
            bullet_box = {
                'x': bullet['x'],
                'y': bullet['y'],
                'width': 1,
                'height': 1
            }
            if (circle_box['x'] < bullet_box['x'] + bullet_box['width'] and
                circle_box['x'] + circle_box['width'] > bullet_box['x'] and
                circle_box['y'] < bullet_box['y'] + bullet_box['height'] and
                circle_box['y'] + circle_box['height'] > bullet_box['y']):
                player1_score += SPECIAL_CIRCLE_POINTS if circle['is_special'] else 1
                print(f"Player 1 Score updated! Current Score: {player1_score}")
                circles_p2.remove(circle)
                bullets_p1.remove(bullet)
                break
        for bullet in bullets_p2[:]:
            bullet_box = {
                'x': bullet['x'],
                'y': bullet['y'],
                'width': 1,
                'height': 1
            }
            if (circle_box['x'] < bullet_box['x'] + bullet_box['width'] and
                circle_box['x'] + circle_box['width'] > bullet_box['x'] and
                circle_box['y'] < bullet_box['y'] + bullet_box['height'] and
                circle_box['y'] + circle_box['height'] > bullet_box['y']):
                player2_score += SPECIAL_CIRCLE_POINTS if circle['is_special'] else 1
                print(f"Player 2 Score updated! Current Score: {player2_score}")
                circles_p2.remove(circle)
                bullets_p2.remove(bullet)
                break

    glutPostRedisplay()

# Mouse interaction for buttons
def handle_mouse(button, state, x, y):
    global is_paused, game_is_over, circles_p1, circles_p2, bullets_p1, bullets_p2
    global player1_score, player2_score, player1_missed_circles, player2_missed_circles, missed_shots
    global first_start, last_circle_spawn_time, current_score
    
    if state == GLUT_DOWN:
        y = WINDOW_HEIGHT - y  # Adjust y for OpenGL's coordinate system
        for name, params in BUTTONS.items():
            if (params['x'] <= x <= params['x'] + params['width'] and
                params['y'] <= y <= params['y'] + params['height']):
                if name == "start":
                    if first_start:
                        first_start = False
                        is_paused = False
                    else:
                        is_paused = not is_paused  # Toggle pause state
                elif name == "restart":
                    player1_score = 0
                    player2_score = 0
                    current_score = 0
                    player1_missed_circles = 0
                    player2_missed_circles = 0
                    missed_shots = 0
                    circles_p1 = []
                    circles_p2 = []
                    bullets_p1 = []
                    bullets_p2 = []
                    game_is_over = False
                    is_paused = False  # Don't pause on restart
                    last_circle_spawn_time = time.time()  # Reset spawn timer on restart
                elif name == "quit":
                    print(f"Final Scores - Player 1: {player1_score}, Player 2: {player2_score}. Goodbye!")
                    glutLeaveMainLoop()
                break

# Handle keyboard input
def handle_keyboard(key, x, y):
    global player1_position_y, player1_position_x, player2_position_y, player2_position_x, bullets_p1, bullets_p2

    if not game_is_over:
        # Player 1 controls (WASD for movement, SPACE for shooting)
        if key == b'w' and player1_position_y < WINDOW_HEIGHT - SHIP_HEIGHT/2:
            player1_position_y += SHIP_SPEED
        elif key == b's' and player1_position_y > SHIP_HEIGHT/2:
            player1_position_y -= SHIP_SPEED
        elif key == b'a' and player1_position_x > SHIP_WIDTH:
            player1_position_x -= SHIP_SPEED
        elif key == b'd' and player1_position_x < WINDOW_WIDTH/2 - SHIP_WIDTH:
            player1_position_x += SHIP_SPEED
        elif key == b' ':
            bullets_p1.append({
                'x': player1_position_x + SHIP_WIDTH,
                'y': player1_position_y,
                'last_update': time.time()
            })

        # Player 2 controls (IJKL for movement, P for shooting)
        if key == b'i' and player2_position_y < WINDOW_HEIGHT - SHIP_HEIGHT/2:
            player2_position_y += SHIP_SPEED
        elif key == b'k' and player2_position_y > SHIP_HEIGHT/2:
            player2_position_y -= SHIP_SPEED
        elif key == b'j' and player2_position_x > WINDOW_WIDTH/2 + SHIP_WIDTH:
            player2_position_x -= SHIP_SPEED
        elif key == b'l' and player2_position_x < WINDOW_WIDTH - SHIP_WIDTH:
            player2_position_x += SHIP_SPEED
        elif key == b'p':
            bullets_p2.append({
                'x': player2_position_x - SHIP_WIDTH,
                'y': player2_position_y,
                'last_update': time.time()
            })

# Main render function
def render_game():
    glClear(GL_COLOR_BUFFER_BIT)

    if not game_is_over:
        # Render both ships
        render_ship(player1_position_x, player1_position_y, True)
        render_ship(player2_position_x, player2_position_y, False)

        # Render bullets
        for bullet in bullets_p1:
            draw_circle(bullet['x'], bullet['y'], 5)
        for bullet in bullets_p2:
            draw_circle(bullet['x'], bullet['y'], 5)

        # Render circles for both players
        for circle in circles_p1:
            render_circle(circle['x'], circle['y'], circle['radius'], circle['is_special'])
        for circle in circles_p2:
            render_circle(circle['x'], circle['y'], circle['radius'], circle['is_special'])

        # Render scores
        # (You'll need to add text rendering for scores)

    render_buttons()
    glutSwapBuffers()

# Initialize OpenGL
def init():
    glClearColor(0, 0, 0, 0)
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)


glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
glutInitWindowPosition(500, 100)
glutCreateWindow(b"Shoot the Circles!")
init()
glutDisplayFunc(render_game)
glutIdleFunc(update_game_state)
glutKeyboardFunc(handle_keyboard)
glutMouseFunc(handle_mouse)
glutMainLoop()
