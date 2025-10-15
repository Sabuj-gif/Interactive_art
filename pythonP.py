from sense_hat import SenseHat
from time import sleep

sense = SenseHat()

# === COLORS ===
B = [0, 0, 0]       # Black (background)
G = [0, 255, 0]     # Green (plant)
Br = [139, 69, 19]  # Brown (tree log)
W = [255, 255, 255] # White (pot / arrow)
Bl = [0, 0, 255]    # Blue (water)
R = [255, 0, 0]     # Red (fail)
Y = [255, 255, 0]   # Yellow (seed)

# === GAME ELEMENTS ===
pot_x = 3
seed_x = 3
water_y = 1

# === FUNCTION TO DRAW ===
def draw_scene(pot_x, seed_x, water=None):
    sense.clear()
    pixels = [[B for _ in range(8)] for _ in range(8)]
    
    # Draw pot (2 pixels wide + one below for alignment)
    pixels[0][pot_x] = W
    if pot_x + 1 < 8:
        pixels[0][pot_x + 1] = W
    pixels[1][pot_x] = W  # below pixel indicating where water falls

    # Draw seed
    pixels[7][seed_x] = Y

    # Draw water if falling
    if water is not None:
        y = water["y"]
        if 0 <= y < 8:
            pixels[y][water["x"]] = Bl

    # Flatten list for set_pixels
    sense.set_pixels(sum(pixels, []))


def flash(color, duration=2):
    sense.clear(color)
    sleep(duration)
    sense.clear()


def show_message(text, color):
    sense.show_message(text, text_colour=color, scroll_speed=0.08)


def grow_tree(seed_x):
    # Draw tree step-by-step (log first, then leaves)
    stages = []

    # Log grows one pixel at a time (single column)
    for i in range(1, 5):
        stage = [[B for _ in range(8)] for _ in range(8)]
        for j in range(8 - i, 8):
            stage[j][seed_x] = Br
        stage[7][seed_x] = Y
        stages.append(stage)

    # Leaves stage (top T, then 3, then 1)
    leaf_stage = [[B for _ in range(8)] for _ in range(8)]
    for j in range(4, 8):
        leaf_stage[j][seed_x] = Br  # trunk

    # Leaves: main T-shape
    for dx in range(-2, 3):
        if 0 <= seed_x + dx < 8:
            leaf_stage[3][seed_x + dx] = G
    # Above 3 pixels
    for dx in range(-1, 2):
        if 0 <= seed_x + dx < 8:
            leaf_stage[2][seed_x + dx] = G
    # Top pixel
    leaf_stage[1][seed_x] = G
    stages.append(leaf_stage)

    # Animate growth
    for stage in stages:
        sense.set_pixels(sum(stage, []))
        sleep(1.5)  # slower growth (≈6 seconds total)

    # Hold final tree for 5 seconds
    sleep(5)


def main():
    global pot_x, seed_x
    sense.clear()

    # Display right-facing arrow (centered)
    arrow = [
        B, B, B, B, B, B, B, B,
        B, B, B, B, B, W, W, B,
        B, B, B, B, W, W, W, W,
        B, B, B, W, W, W, W, W,
        B, B, B, B, W, W, W, W,
        B, B, B, B, B, W, W, B,
        B, B, B, B, B, B, B, B,
        B, B, B, B, B, B, B, B
    ]
    sense.set_pixels(arrow)

    # Wait for RIGHT press to start
    while True:
        for event in sense.stick.get_events():
            if event.direction == "right" and event.action == "pressed":
                game_loop()
                return
        sleep(0.1)


def game_loop():
    global pot_x, seed_x
    pot_x = 3
    seed_x = 3
    draw_scene(pot_x, seed_x)
    sleep(0.5)

    while True:
        for event in sense.stick.get_events():
            if event.action == "pressed":
                if event.direction == "left":
                    pot_x = max(0, pot_x - 1)
                elif event.direction == "right":
                    pot_x = min(6, pot_x + 1)
                elif event.direction == "down":
                    if pot_x == seed_x:
                        # Success: drop 3 droplets, then grow tree
                        for _ in range(3):
                            for y in range(2, 8):
                                draw_scene(pot_x, seed_x, {"x": pot_x, "y": y})
                                sleep(0.1)
                            sense.clear()
                            draw_scene(pot_x, seed_x)
                            sleep(0.1)
                        flash([0, 255, 0], 2)  # green flash
                        grow_tree(seed_x)
                        show_message("Life saved", [0, 255, 0])

                        # Wait until middle button pressed to restart
                        while True:
                            for event2 in sense.stick.get_events():
                                if event2.direction == "middle" and event2.action == "pressed":
                                    main()
                                    return
                            sleep(0.1)

                    else:
                        # Missed
                        flash(R, 2)
                        show_message("Water wasted", R)
                        show_message("Retry", W)
                        while True:
                            for event3 in sense.stick.get_events():
                                if event3.direction == "middle" and event3.action == "pressed":
                                    main()
                                    return
                            sleep(0.1)

            draw_scene(pot_x, seed_x)
        sleep(0.1)


# === RUN GAME ===
main()
