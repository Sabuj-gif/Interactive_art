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
    """Return base frame (soil on bottom row). Optionally put a yellow seed at row 6."""
    pixels = []
    for y in range(8):
        for x in range(8):
            pixels.append(BROWN if y == 7 else BLACK)
    if seed_col is not None and 0 <= seed_col < 8:
        # yellow seed (use green for visibility)
        pixels[idx(seed_col, 6)] = GREEN
    return pixels

def draw_pot_on(frame, pot_x):
    """Draw pot (two white pixels on top row) and draw one indicator pixel under center."""
    if 0 <= pot_x < 8:
        frame[idx(pot_x, 0)] = WHITE
    if 0 <= pot_x + 1 < 8:
        frame[idx(pot_x + 1, 0)] = WHITE
    # drop indicator under the right pot pixel (center)
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

# ---------- Tree stages (6 stages total) ----------
def tree_stage(stage, trunk_x):
    f = [BLACK] * 64
    for x in range(8):
        f[idx(x, 7)] = BROWN
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

# ---------- Droplet single drop ----------
def drop_single(pot_x, seed_x_at_drop):
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

# ---------- Intro arrow ----------
def show_arrow_right():
    arrow = [BLACK]*64
    # long right arrow from column 1 to 7 (centered around middle rows)
    coords = [
        (1,2),(2,2),(3,2),(4,2),(5,2),(6,2),
        (1,3),(2,3),(3,3),(4,3),(5,3),(6,3),(7,3),
        (1,4),(2,4),(3,4),(4,4),(5,4),(6,4)
    ]
    for (x,y) in coords:
        arrow[idx(x,y)] = WHITE
    # arrow head (make it triangular at right end)
    for (x,y) in [(6,1),(7,2),(7,4),(6,5)]:
        arrow[idx(x,y)] = WHITE
    sense.set_pixels(arrow)

# ---------- Main game ----------
def run_game():
    tick = 0.10
    while True:
        show_arrow_right()
        started = False
        while not started:
            evs = sense.stick.get_events()
            for e in evs:
                if e.action == 'pressed' and e.direction == 'right':
                    started = True
                    break
            time.sleep(0.05)

        pot_x = 3
        seed_x = random.randint(0, 7)
        seed_dir = 1 if random.choice([True, False]) else -1
        round_active = True

        while round_active:
            seed_x += seed_dir
            if seed_x < 0:
                seed_x = 1
                seed_dir = 1
            elif seed_x > 7:
                seed_x = 6
                seed_dir = -1

            f = soil_frame(seed_x)
            draw_pot_on(f, pot_x)
            sense.set_pixels(f)

            evs = sense.stick.get_events()
            last = None
            for e in evs:
                if e.action == 'pressed' and e.direction in ('left','right','down','middle'):
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
                        evs2 = sense.stick.get_events()
                        for e2 in evs2:
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
                        evs2 = sense.stick.get_events()
                        for e2 in evs2:
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
