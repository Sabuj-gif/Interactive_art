from sense_hat import SenseHat
import time
import random

class PlantGame:
    # --- Colors ---
    B  = [0, 0, 0]       # Black
    G  = [0, 255, 0]     # Green
    BR = [139, 69, 19]   # Brown (soil)
    BL = [0, 120, 255]   # Blue (water)
    Y  = [255, 255, 0]   # Yellow (seed)
    W  = [255, 255, 255] # White (pot)
    R  = [255, 0, 0]     # Red (sad face)

    def __init__(self):
        self.sense = SenseHat()
        self.sense.clear()
        self.frame_delay = 0.12
        self.reset_state()

    # -----------------------------
    #   GAME STATE MANAGEMENT
    # -----------------------------
    def reset_state(self):
        self.pot_x = 3
        self.seed_x = random.randint(1, 6)
        self.seed_dir = 1
        self.seed_hit = False
        self.running = True

    # -----------------------------
    #   DRAWING HELPERS
    # -----------------------------
    def draw_soil(self, seed_col=None):
        pixels = []
        for r in range(8):
            for c in range(8):
                if r == 7:
                    pixels.append(self.BR)
                else:
                    pixels.append(self.B)
        if seed_col is not None:
            pixels[6 * 8 + seed_col] = self.Y
        return pixels

    def draw_pot(self, pixels):
        pixels[self.pot_x] = self.W
        if self.pot_x + 1 < 8:
            pixels[self.pot_x + 1] = self.W
        return pixels

    # -----------------------------
    #   JOYSTICK INPUT
    # -----------------------------
    def handle_joystick(self):
        for e in self.sense.stick.get_events():
            if e.action != "pressed":
                continue
            if e.direction == "left" and self.pot_x > 0:
                self.pot_x -= 1
            elif e.direction == "right" and self.pot_x < 6:
                self.pot_x += 1
            elif e.direction == "down":
                return "drop"
            elif e.direction == "middle":
                return "retry"
        return None

    # -----------------------------
    #   ANIMATION LOGIC
    # -----------------------------
    def move_seed(self):
        self.seed_x += self.seed_dir
        if self.seed_x <= 1 or self.seed_x >= 6:
            self.seed_dir *= -1

    def drop_water(self):
        """Drop 3 separate droplets and check collision with seed"""
        for drop in range(3):
            for y in range(1, 7):
                frame = self.draw_soil(self.seed_x)
                frame = self.draw_pot(frame)
                if self.pot_x + 1 < 8:
                    frame[y * 8 + self.pot_x + 1] = self.BL
                self.sense.set_pixels(frame)
                time.sleep(0.15)

                # Collision check (bottom row)
                if y == 6 and (self.pot_x + 1) == self.seed_x:
                    self.seed_hit = True
                    return
            time.sleep(0.25)

    # -----------------------------
    #   RESULTS (TREE OR SAD FACE)
    # -----------------------------
    def grow_tree(self):
        """Animate 3 growth stages"""
        for stage in range(1, 4):
            frame = self.draw_soil(None)
            if stage >= 1:
                frame[6 * 8 + self.seed_x] = self.BR
            if stage >= 2:
                frame[5 * 8 + self.seed_x] = self.BR
            if stage >= 3:
                frame[4 * 8 + self.seed_x] = self.BR
                if self.seed_x - 1 >= 0:
                    frame[3 * 8 + self.seed_x - 1] = self.G
                frame[3 * 8 + self.seed_x] = self.G
                if self.seed_x + 1 < 8:
                    frame[3 * 8 + self.seed_x + 1] = self.G
                frame[2 * 8 + self.seed_x] = self.G
            self.sense.set_pixels(frame)
            time.sleep(1.5)
        self.sense.show_message("Plant Grown!", scroll_speed=0.05, text_colour=self.G)

    def sad_face(self):
        face = [self.B] * 64
        face[18] = self.R
        face[21] = self.R
        face[41] = self.R
        face[42] = self.R
        face[43] = self.R
        self.sense.set_pixels(face)
        self.sense.show_message("You wasted water!", text_colour=self.R, scroll_speed=0.05)
        time.sleep(2)

    # -----------------------------
    #   MAIN GAMEPLAY
    # -----------------------------
    def play_round(self):
        self.reset_state()
        drop_triggered = False

        # Moving seed + joystick until drop
        while not drop_triggered:
            self.move_seed()
            frame = self.draw_soil(self.seed_x)
            frame = self.draw_pot(frame)
            self.sense.set_pixels(frame)
            action = self.handle_joystick()
            if action == "drop":
                drop_triggered = True
            time.sleep(self.frame_delay)

        # Droplet animation
        self.drop_water()

        # Outcome
        if self.seed_hit:
            self.grow_tree()
        else:
            self.sad_face()

    # -----------------------------
    #   MAIN LOOP
    # -----------------------------
    def run(self):
        self.sense.show_message("Water the Plant!", scroll_speed=0.05, text_colour=self.W)
        while True:
            self.play_round()
            # Ask for retry
            self.sense.show_message("Press middle to retry", scroll_speed=0.05, text_colour=self.W)
            waiting = True
            while waiting:
                action = self.handle_joystick()
                if action == "retry":
                    waiting = False
                time.sleep(0.1)

# -----------------------------
# Run game
# -----------------------------
if __name__ == "__main__":
    try:
        PlantGame().run()
    except KeyboardInterrupt:
        sense = SenseHat()
        sense.clear()
