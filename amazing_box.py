"""Amazing Box: bouncing, blinking points in a PyOpenGL / GLUT window.

Right-click anywhere to release a point that travels diagonally and bounces
off the edges of the window.

Controls
    Right click          spawn a point at the cursor
    Left click           toggle blinking
    Up / Down arrow      speed up / slow down every point
    Space                freeze / unfreeze (other controls are ignored while frozen)
    Esc                  quit
"""

import colorsys
import os
import random
from dataclasses import dataclass

from OpenGL.GL import *
from OpenGL.GLUT import *

WINDOW_WIDTH, WINDOW_HEIGHT = 500, 500
FRAME_MS = 16          # timer interval, ~60 frames per second
MAX_DT = 0.05          # longest single step, so a stalled window doesn't make points jump

POINT_SIZE = 8
BASE_SPEED = 90.0      # units per second along each axis
SPEED_FACTOR = 1.25    # speed multiplier per Up / Down key press
MIN_SPEED, MAX_SPEED = 0.1, 20.0
BLINK_PERIOD = 1.0     # seconds for one visible + hidden cycle

HINT = "Right-click to add a point"
HINT_FONT = GLUT_BITMAP_HELVETICA_18
ESC = b"\x1b"


@dataclass
class Point:
    x: float
    y: float
    dx: float
    dy: float
    color: tuple


width, height = WINDOW_WIDTH, WINDOW_HEIGHT  # the box is the whole window
points = []
speed = 1.0
blinking = False
frozen = False
clock = 0.0  # animation time in seconds; stands still while frozen
last_ms = 0


def spawn_point(x, y):
    dx = random.choice((-1, 1)) * BASE_SPEED
    dy = random.choice((-1, 1)) * BASE_SPEED
    # Full saturation and brightness, so no point is lost against the black box.
    color = colorsys.hsv_to_rgb(random.random(), 0.85, 1.0)
    points.append(Point(x, y, dx, dy, color))


def update(dt):
    global clock
    if frozen:
        return
    clock += dt
    step = speed * dt
    lo_x, hi_x = POINT_SIZE / 2, width - POINT_SIZE / 2
    lo_y, hi_y = POINT_SIZE / 2, height - POINT_SIZE / 2
    for p in points:
        p.x += p.dx * step
        p.y += p.dy * step
        # Bounce by setting the direction rather than flipping it, so a point
        # that overshoots an edge can't get stuck there flipping back and forth.
        if p.x <= lo_x:
            p.x, p.dx = lo_x, abs(p.dx)
        elif p.x >= hi_x:
            p.x, p.dx = hi_x, -abs(p.dx)
        if p.y <= lo_y:
            p.y, p.dy = lo_y, abs(p.dy)
        elif p.y >= hi_y:
            p.y, p.dy = hi_y, -abs(p.dy)


def draw_hint():
    text_width = sum(glutBitmapWidth(HINT_FONT, ord(ch)) for ch in HINT)
    glColor3f(0.6, 0.6, 0.6)
    glRasterPos2f((width - text_width) / 2, height / 2)
    for ch in HINT:
        glutBitmapCharacter(HINT_FONT, ord(ch))


def draw_scene():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    if not points:
        draw_hint()
        return

    hidden = blinking and clock % BLINK_PERIOD >= BLINK_PERIOD / 2
    if hidden:
        return
    glPointSize(POINT_SIZE)
    glBegin(GL_POINTS)
    for p in points:
        glColor3f(*p.color)
        glVertex2f(p.x, p.y)
    glEnd()


def display():
    draw_scene()
    glutSwapBuffers()


def reshape(w, h):
    # Keep one scene unit per pixel, so mouse coordinates map straight onto the box.
    global width, height
    width, height = max(w, 1), max(h, 1)
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def on_timer(_value):
    global last_ms
    now = glutGet(GLUT_ELAPSED_TIME)
    update(min((now - last_ms) / 1000.0, MAX_DT))
    last_ms = now
    glutPostRedisplay()
    glutTimerFunc(FRAME_MS, on_timer, 0)


def on_mouse(button, state, x, y):
    global blinking
    if frozen or state != GLUT_DOWN:
        return
    if button == GLUT_RIGHT_BUTTON:
        spawn_point(x, height - y)  # GLUT's mouse y grows downwards; OpenGL's grows upwards
    elif button == GLUT_LEFT_BUTTON:
        blinking = not blinking


def on_key(key, _x, _y):
    global frozen
    if key == b" ":
        frozen = not frozen
    elif key == ESC:
        quit_app()


def on_special_key(key, _x, _y):
    global speed
    if frozen:
        return
    if key == GLUT_KEY_UP:
        speed = min(MAX_SPEED, speed * SPEED_FACTOR)
    elif key == GLUT_KEY_DOWN:
        speed = max(MIN_SPEED, speed / SPEED_FACTOR)


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
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"Amazing Box")
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMouseFunc(on_mouse)
    glutKeyboardFunc(on_key)
    glutSpecialFunc(on_special_key)
    last_ms = glutGet(GLUT_ELAPSED_TIME)
    glutTimerFunc(FRAME_MS, on_timer, 0)
    glutMainLoop()


if __name__ == "__main__":
    main()
