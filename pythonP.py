#!/usr/bin/env python3
from sense_hat import SenseHat
import time, random

class PlantGame:
    # Colors
    B  = [0, 0, 0]        # background
    G  = [0, 255, 0]      # leaves
    BR = [139, 69, 19]    # brown (trunk / soil)
    BL = [0, 120, 255]    # blue (water)
    Y  = [255, 255, 0]    # yellow (seed)
    W  = [255, 255, 255]  # white (pot)
    R  = [255, 0, 0]      # red (fail)
    GR = [0, 200, 0]      # bright green (success)

    def __init__(self):
        self.sense = SenseHat()
        self.sense.clear()
        self.pot_x = 3
        self.seed_x = 0
        self.seed_dir = 1
        self.frame_delay = 0.12

    # ---------- Drawing ----------
    def soil_frame(self, seed_col=None):
        pixels = []
        for r in range(8):
            for c in range(8):
                pixels.append(self.BR if r==7 else self.B)
        if seed_col is not None:
            pixels[6*8 + seed_col] = self.Y
        return pixels

    def draw_pot_on(self, pixels, pot_col):
        # top 2 white pixels
        for dx in (0,1):
            if 0 <= pot_col+dx < 8:
                pixels[0*8 + pot_col+dx] = self.W
        # one guiding pixel under pot center
        center = pot_col + 1
        if 0 <= center < 8:
            pixels[1*8 + center] = self.W
        return pixels

    def poll_joystick(self):
        act = None
        for e in self.sense.stick.get_events():
            if e.action=="pressed" and e.direction in ("left","right","down","middle"):
                act = e.direction
        return act

    def set_full_color(self, color):
        self.sense.set_pixels([color]*64)

    # ---------- Effects ----------
    def blink_color(self, color, duration=2.0, period=0.25):
        end=time.time()+duration
        on=True
        while time.time()<end:
            self.set_full_color(color if on else self.B)
            on=not on
            time.sleep(period)
        self.sense.clear()

    def scroll(self,text,color,speed=0.08):
        self.sense.show_message(text,scroll_speed=speed,text_colour=color)

    # ---------- Droplets ----------
    def drop_one(self,pot_col,seed_col):
        drop_x = pot_col+1
        for y in range(1,7):
            frame=self.soil_frame(seed_col)
            frame=self.draw_pot_on(frame,pot_col)
            if 0<=drop_x<8: frame[y*8+drop_x]=self.BL
            self.sense.set_pixels(frame)
            time.sleep(0.15)
        return drop_x==seed_col

    def drop_sequence(self,pot_col,seed_col):
        for i in range(3):
            hit=self.drop_one(pot_col,seed_col)
            if hit:
                if i==0:   # drop two more right on seed
                    for _ in range(2):
                        self.drop_one(pot_col,seed_col)
                return True
            time.sleep(0.25)
        return False

    # ---------- Tree Growth ----------
    def animate_tree(self,seed_col):
        """
        New full tree: 2-column log, wide T, upper tiers (3, then 1 leaf).
        Total 6s (3 stages) + hold 5s.
        """
        for stage in range(1,4):
            f=self.soil_frame(None)
            # base trunk (2-column)
            if stage>=1:
                for dx in (0,1):
                    if 0<=seed_col+dx<8:
                        f[6*8 + seed_col+dx]=self.BR
            if stage>=2:
                for dx in (0,1):
                    if 0<=seed_col+dx<8:
                        f[5*8 + seed_col+dx]=self.BR
            if stage>=3:
                for dy in (4,3,2):
                    # thicker base trunk up to row 4
                    for dx in (0,1):
                        if 0<=seed_col+dx<8:
                            f[dy*8 + seed_col+dx]=self.BR
                # T-shaped main leaf line (5 pixels wide)
                for dx in range(-2,3):
                    c=seed_col+dx
                    if 0<=c<8:
                        f[2*8 + c]=self.G
                # 3-pixel leaf row above
                for dx in (-1,0,1):
                    c=seed_col+dx
                    if 0<=c<8:
                        f[1*8 + c]=self.G
                # single top leaf
                if 0<=seed_col<8:
                    f[0*8 + seed_col]=self.G
            self.sense.set_pixels(f)
            time.sleep(2)
        time.sleep(5)  # hold final tree

    # ---------- Round ----------
    def play_round(self):
        self.pot_x=3
        self.seed_x=random.randint(0,7)
        self.seed_dir=random.choice([-1,1])
        self.sense.show_message("Get Ready",scroll_speed=0.08,text_colour=self.W)

        # move seed before control
        for _ in range(20):
            self.seed_x+=self.seed_dir
            if self.seed_x<0:self.seed_x, self.seed_dir=1,1
            if self.seed_x>7:self.seed_x, self.seed_dir=6,-1
            f=self.draw_pot_on(self.soil_frame(self.seed_x),self.pot_x)
            self.sense.set_pixels(f)
            time.sleep(self.frame_delay)

        dropped=False
        while not dropped:
            self.seed_x+=self.seed_dir
            if self.seed_x<0:self.seed_x, self.seed_dir=1,1
            if self.seed_x>7:self.seed_x, self.seed_dir=6,-1
            f=self.draw_pot_on(self.soil_frame(self.seed_x),self.pot_x)
            self.sense.set_pixels(f)
            act=self.poll_joystick()
            if act=="left" and self.pot_x>0:self.pot_x-=1
            elif act=="right" and self.pot_x<6:self.pot_x+=1
            elif act=="down":dropped=True
            elif act=="middle":return "restart"
            time.sleep(self.frame_delay)

        hit=self.drop_sequence(self.pot_x,self.seed_x)
        if hit:
            self.blink_color(self.GR,2)
            self.animate_tree(self.seed_x)
            self.scroll("Life saved",self.G,0.08)
            self.scroll("Retry",self.W,0.08)
            return "completed"
        else:
            self.blink_color(self.R,2)
            self.scroll("Water wasted",self.R,0.08)
            self.scroll("Retry",self.W,0.08)
            return "missed"

    # ---------- Game Loop ----------
    def run(self):
        try:
            while True:
                result=self.play_round()
                waiting=True
                while waiting:
                    a=self.poll_joystick()
                    if a=="middle":waiting=False
                    time.sleep(0.12)
        except KeyboardInterrupt:
            self.sense.clear()

if __name__=="__main__":
    PlantGame().run()
