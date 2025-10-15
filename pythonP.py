from sense_hat import SenseHat
import time
import random

sense = SenseHat()

# ----- Colors -----
B  = [0, 0, 0]       # Black (background)
G  = [0, 255, 0]     # Green (plant)
BR = [139, 69, 19]   # Brown (soil)
BL = [0, 120, 255]   # Blue (water)
Y  = [255, 255, 0]   # Yellow (seed)
W  = [255, 255, 255] # White (pot)
R  = [255, 0, 0]     # Red (sad face)

# ----- Globals -----
pot_x = 3
seed_x = 2
seed_dir = 1
seed_hit = False


# ----- Draw Soil and Seed -----
def draw_soil(seed_col=None):
    pixels = []
    for r in range(8):
        for c in range(8):
            if r == 7:
                pixels.append(BR)
            else:
                pixels.append(B)
    if seed_col is not None:
        pixels[6*8 + seed_col] = Y
    return pixels


# ----- Draw Pot -----
def draw_pot(pixels, pot_col):
    pixels[pot_col] = W
    if pot_col + 1 < 8:
        pixels[pot_col + 1] = W
    return pixels


# ----- Drop 3 separate droplets -----
def drop_water(pot_col, seed_col):
    global seed_hit

    for drop in range(3):
        for y in range(1, 7):
            frame = draw_soil(seed_col)
            frame = draw_pot(frame, pot_col)
            # droplet under right side of pot
            if pot_col + 1 < 8:
                frame[y*8 + pot_col + 1] = BL
            sense.set_pixels(frame)
            time.sleep(0.15)

            # collision check
            if y == 6 and (pot_col + 1) == seed_col:
                seed_hit = True
                return  # stop further droplets

        time.sleep(0.25)


# ----- Tree Growth Animation -----
def grow_tree(seed_col):
    for stage in range(1, 4):
        frame = draw_soil(None)
        # stem
        if stage >= 1:
            frame[6*8 + seed_col] = BR
        if stage >= 2:
            frame[5*8 + seed_col] = BR
        if stage >= 3:
            frame[4*8 + seed_col] = BR
            if seed_col - 1 >= 0:
                frame[3*8 + seed_col - 1] = G
            frame[3*8 + seed_col] = G
            if seed_col + 1 < 8:
                frame[3*8 + seed_col + 1] = G
            frame[2*8 + seed_col] = G
        sense.set_pixels(frame)
        time.sleep(1.5)
    sense.show_message("Plant Grown!", scroll_speed=0.05, text_colour=G)


# ----- Sad face when missed -----
def sad_face():
    face = [B]*64
    face[18] = R
    face[21] = R
    face[41] = R
    face[42] = R
    face[43] = R
    sense.set_pixels(face)
    sense.show_message("You wasted water!", text_colour=R, scroll_speed=0.05)
    time.sleep(2)


# ----- Main Game -----
def play_game():
    global pot_x, seed_x, seed_dir, seed_hit
    pot_x = 3
    seed_x = random.randint(1, 6)
    seed_dir = 1
    seed_hit = False
    game_over = False
    middle_pressed = False

    # Move seed automatically first for 20 steps
    for _ in range(20):
        seed_x += seed_dir
        if seed_x <= 1 or seed_x >= 6:
            seed_dir *= -1
        frame = draw_soil(seed_x)
        frame = draw_pot(frame, pot_x)
        sense.set_pixels(frame)
        time.sleep(0.15)

    # Wait for joystick actions
    def handle_event(event):
        nonlocal middle_pressed
        global pot_x
        if event.action == "pressed":
            if event.direction == "left" and pot_x > 0:
                pot_x -= 1
            elif event.direction == "right" and pot_x < 6:
                pot_x += 1
            elif event.direction == "down":
                middle_pressed = True

    sense.stick.direction_any = handle_event

    while not middle_pressed:
        # keep moving seed until pot dropped
        seed_x += seed_dir
        if seed_x <= 1 or seed_x >= 6:
            seed_dir *= -1
        frame = draw_soil(seed_x)
        frame = draw_pot(frame, pot_x)
        sense.set_pixels(frame)
        time.sleep(0.12)

    # Drop water
    drop_water(pot_x, seed_x)

    # Outcome
    if seed_hit:
        grow_tree(seed_x)
    else:
        sad_face()


# ----- Retry Loop -----
while True:
    play_game()
    sense.show_message("Press middle to retry", scroll_speed=0.05, text_colour=W)

    waiting = True
    def retry_event(event):
        nonlocal waiting
        if event.action == "pressed" and event.direction == "middle":
            waiting = False

    sense.stick.direction_any = retry_event
    while waiting:
        time.sleep(0.1)
