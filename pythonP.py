from sense_hat import SenseHat
from time import sleep

sense = SenseHat()
sense.clear()

# Colors
W = (255, 255, 255)  # white
B = (0, 0, 255)      # blue
G = (0, 255, 0)      # green
Br = (139, 69, 19)   # brown (tree trunk)
R = (255, 0, 0)      # red
Bl = (0, 0, 0)       # black (background)

# --- Tree stages ---
def tree_stage(stage):
    img = [Bl]*64
    if stage == 1:  # small sprout
        img[52] = Br
        img[44] = G
    elif stage == 2:  # mid tree
        img[52] = Br
        img[44] = Br
        img[36] = G
        img[35] = G
        img[37] = G
    elif stage == 3:  # full tree (perfectly aligned)
        for i in [52, 44, 36]:  # single vertical trunk
            img[i] = Br
        # Main T-shaped leaves (5 pixels)
        for i in [27, 28, 29, 30, 31]:
            img[i] = G
        # Smaller upper layer (3 pixels)
        for i in [19, 20, 21]:
            img[i] = G
        # Top pixel
        img[12] = G
    return img

# --- Draw pot ---
def draw_pot(x):
    img = [Bl]*64
    img[0 + x] = W
    img[1 + x] = W
    img[8 + x + 1] = W  # drop indicator
    return img

# --- Droplet animation ---
def drop_water(x, seed_x):
    for drop in range(3):
        for y in range(1, 7):
            frame = [Bl]*64
            # Pot
            frame[x] = W
            frame[x+1] = W
            frame[8 + x + 1] = W  # drop indicator
            # Droplet
            frame[y*8 + (x+1)] = B
            # Seed
            frame[seed_x + 56] = G
            sense.set_pixels(frame)
            sleep(0.15)
        sleep(0.2)

# --- Flash color ---
def flash(color, duration):
    sense.clear(color)
    sleep(duration)
    sense.clear()

# --- Display messages with slower scroll ---
def show_message(msg, color):
    sense.show_message(msg, scroll_speed=0.06, text_colour=color)

# --- Game main loop ---
def game():
    pot_x = 3
    seed_x = 3

    # Intro arrow
    sense.clear()
    arrow = [
        Bl, Bl, W, W, W, Bl, Bl, Bl,
        Bl, Bl, Bl, W, W, Bl, Bl, Bl,
        Bl, Bl, Bl, W, W, Bl, Bl, Bl,
        Bl, Bl, Bl, W, W, Bl, Bl, Bl,
        Bl, Bl, Bl, W, W, Bl, Bl, Bl,
        Bl, Bl, Bl, W, W, Bl, Bl, Bl,
        Bl, Bl, W, W, W, Bl, Bl, Bl,
        Bl, Bl, Bl, Bl, Bl, Bl, Bl, Bl
    ]
    sense.set_pixels(arrow)
    # Wait for right press
    while True:
        e = sense.stick.get_events()
        if any(ev.direction == "right" and ev.action == "pressed" for ev in e):
            break
        sleep(0.1)

    # Start game
    while True:
        frame = draw_pot(pot_x)
        frame[56 + seed_x] = G  # seed
        sense.set_pixels(frame)

        for event in sense.stick.get_events():
            if event.action == "pressed":
                if event.direction == "left" and pot_x > 0:
                    pot_x -= 1
                elif event.direction == "right" and pot_x < 6:
                    pot_x += 1
                elif event.direction == "down":
                    drop_water(pot_x, seed_x)
                    if pot_x == seed_x:
                        flash((0, 255, 0), 2)
                        for stage in range(1, 4):
                            sense.set_pixels(tree_stage(stage))
                            sleep(2)  # total 6 seconds grow time
                        flash((0, 255, 0), 0.5)
                        show_message("Life saved", (0, 255, 0))
                        # keep tree until middle press
                        sense.set_pixels(tree_stage(3))
                        while True:
                            ev = sense.stick.get_events()
                            if any(e.direction == "middle" and e.action == "pressed" for e in ev):
                                return game()  # restart game
                            sleep(0.1)
                    else:
                        flash(R, 2)
                        show_message("Water wasted", R)
                        show_message("Retry", W)
                        while True:
                            ev = sense.stick.get_events()
                            if any(e.direction == "middle" and e.action == "pressed" for e in ev):
                                return game()  # restart
                            sleep(0.1)

# --- Run the game ---
game()
