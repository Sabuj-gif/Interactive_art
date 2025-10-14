#!/usr/bin/env python3
# plant_game.py - Sense HAT 8x8 game (Python)
# Controls:
#   - joystick LEFT/RIGHT to move the pot (two white pixels at top row)
#   - joystick MIDDLE to drop water (3 droplets)
# If any droplet hits the yellow seed, a tree grows and "THANK YOU" scrolls.

import time
from sense_hat import SenseHat

sense = SenseHat()
sense.clear()

# Colors (R, G, B)
B  = (0, 0, 0)          # black
G  = (0, 255, 0)        # green
BR = (139, 69, 19)      # brown (soil/pot base)
BL = (0, 119, 255)      # blue (drop)
Y  = (255, 215, 0)      # yellow (seed)
W  = (255, 255, 255)    # white (pot)
R  = (255, 0, 0)        # red (unused)
S  = (255, 51, 170)     # pink flash
T  = (51, 255, 255)     # cyan flash

# Globals
pot_x = 3
seed_x = 2
seed_dir = 1
drops_hit = 0
seed_hit_pos = -1

def draw_soil(seed_col, seed_visible=True):
    """Clear matrix and draw soil (bottom row) and optionally the seed."""
    # fill black
    for y in range(8):
        for x in range(8):
            sense.set_pixel(x, y, B)
    # soil bottom row
    for x in range(8):
        sense.set_pixel(x, 7, BR)
    # seed one row above soil (y=6)
    if seed_visible and 0 <= seed_col < 8:
        sense.set_pixel(seed_col, 6, Y)

def draw_pot(pot_col):
    """Draw the pot as two white pixels at top row (y=0)."""
    # clear top row pixels where pot sits so draw only pot
    # ensure pot_col in valid range 0..6
    if pot_col < 0: pot_col = 0
    if pot_col > 6: pot_col = 6
    sense.set_pixel(pot_col, 0, W)
    sense.set_pixel(pot_col+1, 0, W)

def draw_drop(drop_col, y):
    """Draw a single drop pixel at given (drop_col, y)."""
    if 0 <= drop_col < 8 and 0 <= y < 8:
        sense.set_pixel(drop_col, y, BL)

def jig_jag_flash():
    """Flash the whole matrix alternating S and T."""
    for i in range(12):
        color = S if i % 2 == 0 else T
        for y in range(8):
            for x in range(8):
                sense.set_pixel(x, y, color)
        time.sleep(0.08)

def grow_tree(seed_col):
    """Grow a simple tree at the seed_col location in 3 stages."""
    for stage in range(1, 4):
        # redraw soil background
        draw_soil(-1, seed_visible=False)
        # trunk growth (brown)
        if stage >= 1 and 0 <= seed_col < 8:
            sense.set_pixel(seed_col, 6, BR)
        if stage >= 2:
            sense.set_pixel(seed_col, 5, BR)
        if stage >= 3:
            sense.set_pixel(seed_col, 4, BR)
            # leaves 3rd row (y=3)
            for dx in (-1, 0, 1):
                c = seed_col + dx
                if 0 <= c < 8:
                    sense.set_pixel(c, 3, G)
            # extra top leaf at y=2
            if 0 <= seed_col < 8:
                sense.set_pixel(seed_col, 2, G)
        time.sleep(2)
    time.sleep(5)

def scroll_thank_you():
    """Scroll 'THANK YOU' across the 8x8 using built-in function for simplicity."""
    # show_message will use scroll; use green text on brown background for soil contrast
    sense.show_message("THANK YOU", text_colour=G, back_colour=BR, scroll_speed=0.06)

def main_loop():
    global pot_x, seed_x, seed_dir, drops_hit, seed_hit_pos

    try:
        while True:
            # reset state
            drops_hit = 0
            seed_hit_pos = -1
            pot_x = 3
            seed_x = 2
            seed_dir = 1

            # Seed moves automatically for a while
            for _ in range(20):
                seed_x += seed_dir
                if seed_x <= 1 or seed_x >= 6:
                    seed_dir *= -1
                draw_soil(seed_x, seed_visible=True)
                draw_pot(pot_x)
                time.sleep(0.15)

            # Let user move pot and press middle to drop
            middle_pressed = False
            # clear any existing joystick event queue
            sense.stick.get_events()
            while not middle_pressed:
                # handle joystick events (non-blocking)
                events = sense.stick.get_events()
                for e in events:
                    # e.action can be 'pressed', 'released' or 'held'
                    if e.action == 'pressed':
                        if e.direction == 'left' and pot_x > 0:
                            pot_x -= 1
                        elif e.direction == 'right' and pot_x < 6:
                            pot_x += 1
                        elif e.direction == 'middle':
                            middle_pressed = True
                draw_soil(seed_x, seed_visible=True)
                draw_pot(pot_x)
                time.sleep(0.08)

            # Drop 3 droplets and detect hits
            for d in range(3):
                # drop falls from y=1 to y=6 (just above seed)
                for y in range(1, 7):
                    draw_soil(seed_x, seed_visible=True)
                    draw_pot(pot_x)
                    draw_drop(pot_x + 1, y)
                    time.sleep(0.18)
                    # check collision: drop column (pot_x+1) meets seed_x at y==6
                    if (pot_x + 1) == seed_x and y == 6:
                        drops_hit += 1
                        seed_hit_pos = seed_x
                        # leave the drop drawn briefly then break to next droplet
                        time.sleep(0.12)
                        break

            # Result
            if drops_hit >= 1:
                jig_jag_flash()
                grow_tree(seed_hit_pos if seed_hit_pos >= 0 else seed_x)
                scroll_thank_you()
            else:
                # missed — do a little blink and restart
                for i in range(4):
                    sense.clear()
                    time.sleep(0.2)
                    draw_soil(seed_x, seed_visible=True)
                    draw_pot(pot_x)
                    time.sleep(0.2)

            # small pause before next round
            time.sleep(0.5)

    except KeyboardInterrupt:
        # clean exit
        sense.clear()
        print("\nExiting. Matrix cleared.")
    finally:
        sense.clear()

if __name__ == "__main__":
    main_loop()
