#!/usr/bin/env python3
from sense_hat import SenseHat
import time
import random

class PlantGame:
    # Colors
    B  = [0, 0, 0]        # black
    G  = [0, 255, 0]      # green (leaves)
    BR = [139, 69, 19]    # brown (soil / stem base color)
    BL = [0, 120, 255]    # blue (water)
    Y  = [255, 255, 0]    # yellow (seed)
    W  = [255, 255, 255]  # white (pot)
    R  = [255, 0, 0]      # red (error / sad face)
    GR = [0, 200, 0]      # bright green for flash

    def __init__(self):
        self.sense = SenseHat()
        self.sense.clear()
        # Game state
        self.pot_x = 3        # pot occupies pot_x and pot_x+1 (0..6 valid)
        self.seed_x = 0      # seed column (0..7)
        self.seed_dir = 1    # direction: 1 right, -1 left
        self.seed_hit = False
        # Timing
        self.frame_delay = 0.12

    # ---------- Drawing utilities ----------
    def soil_frame(self, seed_col=None):
        """Return 64-element pixel list with soil; optional seed (yellow) at row 6."""
        pixels = []
        for r in range(8):
            for c in range(8):
                if r == 7:
                    pixels.append(self.BR)
                else:
                    pixels.append(self.B)
        if seed_col is not None and 0 <= seed_col < 8:
            pixels[6*8 + seed_col] = self.Y
        return pixels

    def draw_pot_on(self, pixels, pot_col):
        """Modify pixel list to add pot (two white pixels) at top row."""
        if 0 <= pot_col < 8:
            pixels[0 * 8 + pot_col] = self.W
        if 0 <= pot_col + 1 < 8:
            pixels[0 * 8 + pot_col + 1] = self.W
        return pixels

    def set_full_color(self, color):
        """Fill whole matrix with a single color and update."""
        pixels = [color] * 64
        self.sense.set_pixels(pixels)

    # ---------- Joystick handling ----------
    def poll_joystick(self):
        """Return last pressed action string or None: 'left','right','down','middle'."""
        action = None
        events = list(self.sense.stick.get_events())
        # process only pressed actions, take last relevant
        for e in events:
            if e.action != "pressed":
                continue
            if e.direction in ("left", "right", "down", "middle"):
                action = e.direction
        return action

    # ---------- Animations & effects ----------
    def blink_color(self, color, duration=2.0, period=0.25):
        """Blink whole matrix with color on/off for duration seconds."""
        end = time.time() + duration
        on = True
        while time.time() < end:
            self.set_full_color(color if on else self.B)
            on = not on
            time.sleep(period)
        # leave blank after blink
        self.sense.clear()

    def show_scroll(self, text, color, speed=0.09):
        """Show scroll text once (slower default)."""
        # sense.show_message blocks until done
        self.sense.show_message(text, scroll_speed=speed, text_colour=color)

    # ---------- Droplets logic ----------
    def drop_one_droplet(self, pot_col, seed_col):
        """Animate a single droplet falling from pot_col+1. Return True if it hits seed."""
        droplet_x = pot_col + 1
        # drop from y=1 to y=6
        for y in range(1, 7):
            frame = self.soil_frame(seed_col)
            frame = self.draw_pot_on(frame, pot_col)
            if 0 <= droplet_x < 8:
                frame[y*8 + droplet_x] = self.BL
            self.sense.set_pixels(frame)
            time.sleep(0.15)
        # collision check at bottom row (y=6)
        hit = (droplet_x == seed_col)
        return hit

    def drop_sequence(self, pot_col, seed_col):
        """
        Drop up to 3 droplets:
        - If first droplet hits seed, then drop two *additional* droplets guaranteed to fall on seed (seed frozen)
          then return True (hit).
        - Otherwise continue through remaining droplets; if any hit, return True.
        - If none hit, return False.
        """
        # Seed is considered frozen during the entire drop sequence
        # Attempt first droplet
        for i in range(3):
            hit = self.drop_one_droplet(pot_col, seed_col)
            if hit:
                # If first droplet (i==0) hits: drop two more targeted droplets on seed
                if i == 0:
                    # two additional drops that fall on seed (even if seed would have moved normally)
                    for _ in range(2):
                        # animate another droplet falling on same column
                        for y in range(1, 7):
                            frame = self.soil_frame(seed_col)
                            frame = self.draw_pot_on(frame, pot_col)
                            if 0 <= pot_col+1 < 8:
                                frame[y*8 + (pot_col+1)] = self.BL
                            self.sense.set_pixels(frame)
                            time.sleep(0.15)
                # set hit flag and stop sequence
                self.seed_hit = True
                return True
            # small delay between independent droplets when miss
            time.sleep(0.25)
        # none hit
        return False

    # ---------- Tree growth ----------
    def animate_growth(self, seed_col):
        """
        3 stages over TOTAL of 6 seconds -> 2s each.
        After completion hold final tree for 5 seconds.
        """
        for stage in range(1, 4):
            frame = self.soil_frame(None)
            # We draw stem in brown to sit on soil and leave leaves green
            if stage >= 1:
                frame[6*8 + seed_col] = self.BR
            if stage >= 2:
                frame[5*8 + seed_col] = self.BR
            if stage >= 3:
                frame[4*8 + seed_col] = self.BR
                # leaves row (3)
                for dx in (-1, 0, 1):
                    c = seed_col + dx
                    if 0 <= c < 8:
                        frame[3*8 + c] = self.G
                # extra top leaf at row 2
                if 0 <= seed_col < 8:
                    frame[2*8 + seed_col] = self.G
            self.sense.set_pixels(frame)
            time.sleep(2.0)  # 2 seconds per stage -> total 6s
        # hold final tree for 5 seconds
        time.sleep(5.0)

    # ---------- Sad face ----------
    def show_sad(self):
        face = [self.B] * 64
        # eyes (x=2,y=2) index 18 ; (x=5,y=2) index 21
        face[18] = self.R
        face[21] = self.R
        # mouth indices around row 5 small curve
        face[41] = self.R
        face[42] = self.R
        face[43] = self.R
        self.sense.set_pixels(face)

    # ---------- Main round ----------
    def play_round(self):
        # initialize seed & pot state
        self.pot_x = 3
        self.seed_x = random.randint(0, 7)  # allow seed anywhere initially
        # ensure seed moves across full 0..7 width
        self.seed_dir = 1 if random.choice([True, False]) else -1
        self.seed_hit = False

        # brief intro frame
        self.sense.show_message("Get Ready", scroll_speed=0.08, text_colour=self.W)

        # Move seed automatically for some time before waiting for player drop
        pre_move_steps = 20
        for _ in range(pre_move_steps):
            # move seed
            self.seed_x += self.seed_dir
            # reverse at full edges 0..7 to traverse full width
            if self.seed_x < 0:
                self.seed_x = 1
                self.seed_dir = 1
            elif self.seed_x > 7:
                self.seed_x = 6
                self.seed_dir = -1
            frame = self.soil_frame(self.seed_x)
            frame = self.draw_pot_on(frame, self.pot_x)
            self.sense.set_pixels(frame)
            time.sleep(self.frame_delay)

        # Now allow player to move pot and press down to drop. Seed continues moving until drop.
        dropped = False
        while not dropped:
            # move seed
            self.seed_x += self.seed_dir
            if self.seed_x < 0:
                self.seed_x = 1
                self.seed_dir = 1
            elif self.seed_x > 7:
                self.seed_x = 6
                self.seed_dir = -1

            # draw current frame
            frame = self.soil_frame(self.seed_x)
            frame = self.draw_pot_on(frame, self.pot_x)
            self.sense.set_pixels(frame)

            # poll joystick
            action = self.poll_joystick()
            if action == "left" and self.pot_x > 0:
                self.pot_x -= 1
            elif action == "right" and self.pot_x < 6:
                self.pot_x += 1
            elif action == "down":
                # seed frozen during drop sequence
                dropped = True
            elif action == "middle":
                # if user presses middle here, treat as restart request (break to outer controls)
                return "restart"
            time.sleep(self.frame_delay)

        # At this point the player pressed down: run drop sequence (seed_x frozen)
        hit = self.drop_sequence(self.pot_x, self.seed_x)

        if hit:
            # flash green (blink) for 2 seconds
            self.blink_color(self.GR, duration=2.0, period=0.25)
            # show life-saved message slower so everyone can read
            self.show_scroll("Life saved", color=self.G, speed=0.08)
            # animate tree growth for 6 seconds total and hold for 5s
            self.animate_growth(self.seed_x)
            return "completed"
        else:
            # flash red for 2 seconds
            self.blink_color(self.R, duration=2.0, period=0.25)
            # show wasted message slower
            self.show_scroll("Water wasted", color=self.R, speed=0.08)
            # show Retry prompt text on matrix (not scrolling) - we will use show_message for clarity then display "Retry"
            self.show_scroll("Retry", color=self.W, speed=0.08)
            # also show static "Retry" as three-letter word via set_pixels if you prefer (but show_message is readable)
            return "missed"

    # ---------- Public run loop ----------
    def run(self):
        try:
            while True:
                result = self.play_round()
                # Wait for middle press to restart (or immediate restart if play_round returned "restart")
                waiting = True
                while waiting:
                    act = self.poll_joystick()
                    if act == "middle":
                        waiting = False
                        break
                    # Small idle frame showing soil and pot (just for feedback)
                    frame = self.soil_frame(self.seed_x if result != "completed" else None)
                    frame = self.draw_pot_on(frame, self.pot_x)
                    self.sense.set_pixels(frame)
                    time.sleep(0.12)
        except KeyboardInterrupt:
            self.sense.clear()

# ---------- Run the game ----------
if __name__ == "__main__":
    PlantGame().run()
