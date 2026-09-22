"""House in the Rain: a small interactive PyOpenGL / GLUT scene.

A house stands in a steady downpour. Use the arrow keys to push the rain
sideways with wind, and the D / N keys to move the sky between day and night.

Controls
    Left / Right arrow   bend the rain to the left / right
    D                    brighten the sky, towards day
    N                    darken the sky, towards night
    Esc                  quit
"""

import math
import os
import random

from OpenGL.GL import *
from OpenGL.GLUT import *

# The scene is laid out in a fixed 500 x 500 coordinate space and stretched to
# fill the window if it is resized.
WIDTH, HEIGHT = 500, 500
FRAME_MS = 16          # timer interval, ~60 frames per second
MAX_DT = 0.05          # longest single step, so a stalled window doesn't make the rain jump

DROP_COUNT = 150
DROP_LENGTH = 14.0     # length of one rain streak
FALL_SPEED = 220.0     # units per second
WIND_STEP = 25.0       # sideways speed added per arrow-key press
MAX_WIND = 250.0
DAYLIGHT_STEP = 0.05   # sky change per D / N key press

# House geometry, in scene units.
GROUND_TOP = 100
WALLS = (150, 100, 350, 300)
ROOF = ((150, 300), (350, 300), (250, 400))
DOOR = (225, 100, 275, 190)
DOOR_KNOB = (265, 145)
WINDOWS = ((170, 215, 215, 260), (285, 215, 330, 260))

# Colours as (night, day) pairs; the scene blends between them.
SKY_COLOR = ((0.02, 0.03, 0.10), (0.65, 0.82, 0.97))
GROUND_COLOR = ((0.04, 0.12, 0.05), (0.30, 0.58, 0.25))
WALL_COLOR = ((0.30, 0.26, 0.22), (0.93, 0.84, 0.68))
ROOF_COLOR = ((0.28, 0.08, 0.06), (0.70, 0.20, 0.12))
DOOR_COLOR = ((0.18, 0.10, 0.05), (0.45, 0.26, 0.12))
WINDOW_COLOR = ((1.00, 0.85, 0.40), (0.75, 0.88, 0.95))  # lamp-lit at night, glass by day
OUTLINE_COLOR = (0.80, 0.40, 0.10)

# Rain is light against a dark sky and dark against a bright one. Blending the
# two would make it fade into the sky at dusk, so it switches colour instead.
NIGHT_RAIN = (0.75, 0.82, 1.00)
DAY_RAIN = (0.12, 0.22, 0.50)
RAIN_SWITCH_AT = 0.6

ESC = b"\x1b"

daylight = 0.0  # 0 = night, 1 = day
wind = 0.0      # sideways speed of the rain, units per second
drops = [[random.uniform(0, WIDTH), random.uniform(0, HEIGHT + DROP_LENGTH)]
         for _ in range(DROP_COUNT)]
last_ms = 0


def blend(colors):
    """Mix a (night, day) colour pair according to the current daylight."""
    night, day = colors
    return tuple(n + (d - n) * daylight for n, d in zip(night, day))


def draw(mode, *vertices):
    """Draw one primitive from a list of (x, y) vertices."""
    glBegin(mode)
    for x, y in vertices:
        glVertex2f(x, y)
    glEnd()


def rect(mode, x0, y0, x1, y1):
    draw(mode, (x0, y0), (x1, y0), (x1, y1), (x0, y1))


def draw_ground():
    glColor3f(*blend(GROUND_COLOR))
    rect(GL_QUADS, 0, 0, WIDTH, GROUND_TOP)


def draw_house():
    glColor3f(*blend(WALL_COLOR))
    rect(GL_QUADS, *WALLS)
    glColor3f(*blend(ROOF_COLOR))
    draw(GL_TRIANGLES, *ROOF)
    glColor3f(*blend(DOOR_COLOR))
    rect(GL_QUADS, *DOOR)
    glColor3f(*blend(WINDOW_COLOR))
    for window in WINDOWS:
        rect(GL_QUADS, *window)

    glColor3f(*OUTLINE_COLOR)
    glLineWidth(3)
    rect(GL_LINE_LOOP, *WALLS)
    draw(GL_LINE_LOOP, *ROOF)
    glLineWidth(2)
    rect(GL_LINE_LOOP, *DOOR)
    for x0, y0, x1, y1 in WINDOWS:
        rect(GL_LINE_LOOP, x0, y0, x1, y1)
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        draw(GL_LINES, (mid_x, y0), (mid_x, y1), (x0, mid_y), (x1, mid_y))
    glPointSize(6)
    draw(GL_POINTS, DOOR_KNOB)


def draw_rain():
    # Each streak trails back along the drop's velocity, so wind visibly bends the rain.
    speed = math.hypot(wind, FALL_SPEED)
    tail_dx = -wind / speed * DROP_LENGTH
    tail_dy = FALL_SPEED / speed * DROP_LENGTH

    glColor3f(*(NIGHT_RAIN if daylight < RAIN_SWITCH_AT else DAY_RAIN))
    glLineWidth(1.5)
    glBegin(GL_LINES)
    for x, y in drops:
        glVertex2f(x, y)
        glVertex2f(x + tail_dx, y + tail_dy)
    glEnd()


def draw_scene():
    glClearColor(*blend(SKY_COLOR), 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    draw_ground()
    draw_house()
    draw_rain()


def update(dt):
    for drop in drops:
        drop[0] += wind * dt
        drop[1] -= FALL_SPEED * dt
        if drop[1] + DROP_LENGTH < 0:
            # Fell out of view: recycle it at the top, somewhere new.
            drop[1] += HEIGHT + DROP_LENGTH
            drop[0] = random.uniform(0, WIDTH)
        # Wrap sideways so a strong wind can't blow all the rain off screen.
        drop[0] %= WIDTH


def display():
    draw_scene()
    glutSwapBuffers()


def reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, WIDTH, 0, HEIGHT, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def on_timer(_value):
    global last_ms
    now = glutGet(GLUT_ELAPSED_TIME)
    update(min((now - last_ms) / 1000.0, MAX_DT))
    last_ms = now
    glutPostRedisplay()
    glutTimerFunc(FRAME_MS, on_timer, 0)


def on_key(key, _x, _y):
    global daylight
    key = key.lower()
    if key == b"d":
        daylight = min(1.0, daylight + DAYLIGHT_STEP)
    elif key == b"n":
        daylight = max(0.0, daylight - DAYLIGHT_STEP)
    elif key == ESC:
        quit_app()


def on_special_key(key, _x, _y):
    global wind
    if key == GLUT_KEY_LEFT:
        wind = max(-MAX_WIND, wind - WIND_STEP)
    elif key == GLUT_KEY_RIGHT:
        wind = min(MAX_WIND, wind + WIND_STEP)


def quit_app():
    # freeglut can leave the main loop cleanly; classic GLUT (e.g. on macOS) cannot.
    if bool(glutLeaveMainLoop):
        glutLeaveMainLoop()
    else:
        os._exit(0)


def main():
    global last_ms
    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutCreateWindow(b"House in the Rain")
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(on_key)
    glutSpecialFunc(on_special_key)
    last_ms = glutGet(GLUT_ELAPSED_TIME)
    glutTimerFunc(FRAME_MS, on_timer, 0)
    glutMainLoop()


if __name__ == "__main__":
    main()
