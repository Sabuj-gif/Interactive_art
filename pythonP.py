#!/usr/bin/env python3
from sense_hat import SenseHat
import time
import random

sense = SenseHat()
sense.clear()

# ---------- Colors ----------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
WATER = (0, 120, 255)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
BRIGHT_GREEN = (0, 200, 0)

# ---------- Helpers ----------
def idx(x, y):
    return y * 8 + x

def soil_frame(seed_col=None):
    """Return base frame (soil on bottom row). Optionally put a seed at row 6."""
    pixels = []
    for y in range(8):
        for x in range(8):
            pixels.append(BROWN if y == 7 else BLACK)
    if seed_col is not None and 0 <= seed_col < 8:
        pixels[idx(seed_col, 6)] = GREEN  # seed
    return pixels

def draw_pot_on(frame, pot_x):
    """Draw pot (two white pixels on top row) and one indicator pixel below."""
    if 0 <= pot_x < 8:
        frame[idx(pot_x, 0)] = WHITE
    if 0 <= pot_x + 1 < 8:
        frame[idx(pot_x + 1, 0)] = WHITE
    # drop indicator
    drop_x = pot_x + 1
    if 0 <= drop_x < 8:
        frame[idx(drop_x, 1)] = WHITE
    return frame

def set_all(color):
    sense.set_pixels([color] * 64)

def blink(color, duration=2.0, period=0.25):
    end = time.time() + duration
    on = True
    while time.time() < end:
        set_all(color if on else BLACK)
        on = not on
        time.sleep(period)
    sense.clear()

def show_scroll(text, color, speed=0.08):
    sense.show_message(text, scroll_speed=speed, text_colour=color)

# ---------- Tree stages ----------
def tree_stage(stage, trunk_x):
    """
    stage 1..6:
      1: trunk bottom
      2: trunk middle
      3: trunk upper
      4: 5-pixel T-bar of leaves
      5: 3-pixel row of leaves
      6: top single leaf
    """
    f = [BLACK] * 64
    for x in range(8):
        f[idx(x, 7)] = BROWN  # soil
    if stage >= 1:
        f[idx(trunk_x, 6)] = BROWN
    if stage >= 2:
        f[idx(trunk_x, 5)] = BROWN
    if stage >= 3:
        f[idx(trunk_x, 4)] = BROWN
    if stage >= 4:
        for dx in (-2, -1, 0, 1, 2):
            x = trunk_x + dx
            if 0 <= x < 8:
                f[idx(x, 3)] = GREEN
    if stage >= 5:
        for dx in (-1, 0, 1):
            x = trunk_x + dx
            if 0 <= x < 8:
                f[idx(x, 2)] = GREEN
    if stage >= 6:
        if 0 <= trunk_x < 8:
            f[idx(trunk_x, 1)] = GREEN
    return f

# ---------- Droplets ----------
def drop_single(pot_x, seed_x_at_drop):
    """Animate a droplet from pot_x+1 downward."""
    drop_x = pot_x + 1
    for y in range(1, 7):
        frame = soil_frame(seed_x_at_drop)
        draw_pot_on(frame, pot_x)
        if 0 <= drop_x < 8:
            frame[idx(drop_x, y)] = WATER
        sense.set_pixels(frame)
        time.sleep(0.15)
    return drop_x == seed_x_at_drop

def drop_sequence(pot_x, seed_x_at_drop):
    """Drop up to 3 droplets, with 2 extra visual ones if first hit occurs."""
    for attempt in range(3):
        hit = drop_single(pot_x, seed_x_at_drop)
        if hit:
            if attempt == 0:
                for _ in range(2):
                    for y in range(1, 7):
                        frame = soil_frame(seed_x_at_drop)
                        draw_pot_on(frame, pot_x)
                        if 0 <= pot_x + 1 < 8:
                            frame[idx(pot_x + 1, y)] = WATER
                        sense.set_pixels(frame)
                        time.sleep(0.12)
            return True
        time.sleep(0.25)
    return False

# ---------- Intro arrow (PERFECTLY POINTY VERSION) ----------
def show_arrow_right():
    """
    Display a right-pointing arrow starting from column 0,
    with a 5-column shaft and a 3-level triangular point.
    """
    arrow = [BLACK] * 64
    # Shaft: 5 columns (0–4), rows 2–4
    for x in range(0, 5):
        for y in (2, 3, 4):
            arrow[idx(x, y)] = WHITE
    # Arrowhead: like the tree top (5→3→1 pixels)
    # Row 1 (top of head)
    arrow[idx(5, 1)] = WHITE
    arrow[idx(6, 1)] = WHITE
    arrow[idx(7, 1)] = WHITE
    # Row 2 (middle)
    arrow[idx(6, 2)] = WHITE
    arrow[idx(7, 3)] = WHITE
    arrow[idx(6, 4)] = WHITE
    # Row 3 (bottom of head)
    arrow[idx(5, 5)] = WHITE
    arrow[idx(6, 5)] = WHITE
    arrow[idx(7, 5)] = WHITE

    sense.set_pixels(arrow)

# ---------- Main game ----------
def run_game():
    tick = 0.10
    while True:
        # show intro arrow and wait for right press to start
        show_arrow_right()
        started = False
        while not started:
            evs = sense.stick.get_events()
            for e in evs:
                if e.action == 'pressed' and e.direction == 'right':
                    started = True
                    break
            time.sleep(0.05)

        # initialize round
        pot_x = 3
        seed_x = random.randint(0, 7)
        seed_dir = 1 if random.choice([True, False]) else -1
        round_active = True

        while round_active:
            # move seed
            seed_x += seed_dir
            if seed_x < 0:
                seed_x, seed_dir = 1, 1
            elif seed_x > 7:
                seed_x, seed_dir = 6, -1

            # draw frame
            f = soil_frame(seed_x)
            draw_pot_on(f, pot_x)
            sense.set_pixels(f)

            # joystick input
            evs = sense.stick.get_events()
            last = None
            for e in evs:
                if e.action == 'pressed' and e.direction in ('left', 'right', 'down', 'middle'):
                    last = e.direction
            if last == 'left' and pot_x > 0:
                pot_x -= 1
            elif last == 'right' and pot_x < 6:
                pot_x += 1
            elif last == 'down':
                seed_at_drop = seed_x
                hit = drop_sequence(pot_x, seed_at_drop)
                if hit:
                    blink(BRIGHT_GREEN, duration=2.0, period=0.25)
                    for stage in range(1, 7):
                        sense.set_pixels(tree_stage(stage, seed_at_drop))
                        time.sleep(1.0)
                    time.sleep(5.0)
                    show_scroll("Life saved", GREEN, speed=0.08)
                    sense.set_pixels(tree_stage(6, seed_at_drop))
                    waiting = True
                    while waiting:
                        for e2 in sense.stick.get_events():
                            if e2.action == 'pressed' and e2.direction == 'middle':
                                waiting = False
                                break
                        time.sleep(0.05)
                    round_active = False
                else:
                    blink(RED, duration=2.0, period=0.25)
                    show_scroll("Water wasted", RED, speed=0.08)
                    show_scroll("Retry", WHITE, speed=0.08)
                    waiting = True
                    while waiting:
                        for e2 in sense.stick.get_events():
                            if e2.action == 'pressed' and e2.direction == 'middle':
                                waiting = False
                                break
                        time.sleep(0.05)
                    round_active = False
            elif last == 'middle':
                round_active = False

            time.sleep(tick)

# ---------- Start ----------
if __name__ == "__main__":
    try:
        run_game()
    except KeyboardInterrupt:
        sense.clear()
