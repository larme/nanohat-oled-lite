import os
import random
import smbus2 as smbus
import subprocess
import time

from fonts import normal_font, inverted_font, unknown_char

KEY2PIN = {
    1: 0,
    2: 2,
    3: 3,
}

REBOOT = 98
SHUTDOWN = 99

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class OLEDCtrl(object):

    def __init__(self, state2keymap, state2cmd,
                 key2pin=KEY2PIN, keys=(1, 2, 3),
                 bus_num=0, polling_interval=0.05, display_off_timeout=30.0,
                 line_length=16, line_num=8):

        self.state2keymap = state2keymap
        self.state2cmd = state2cmd
        self.keys = keys
        self.key2pin = key2pin
        self.bus = smbus.SMBus(bus_num)
        self.polling_interval = polling_interval
        self.display_off_timeout = display_off_timeout
        self.line_length = line_length
        self.line_num = line_num

        self.loop_break = False
        self.display_refresh_time = 0
        self.current_time = time.time()
        self.extend_display_off_time()

        self.display_already_off = False

        self.state = 0
        self.keymap = self.state2keymap[self.state]
        self.lines = {}

        self.splash = []
        self.gen_random_splash()

    def init_setup(self):

        self.current_time = time.time()

        # initialize GPIO
        for key in self.keys:
            with open('/sys/class/gpio/export', 'w') as f:
                pin = self.key2pin[key]
                f.write('%d\n' % pin)
            
        tmpl = '/sys/class/gpio/gpio%d/direction'
        for key in self.keys:
            pin = self.key2pin[key]
            path = tmpl % pin
            with open(path, 'w') as f:
                f.write('in\n')

        self.bus.write_i2c_block_data(0x3c, 0x00, [
            0xae,       # set display off
            0x00,       # set lower column address
            0x10,       # set higher column address
            0x40,       # set display start line
            0xb0, 0x81, # set page address
            0xcf,       # set screen flip
            0xa1,       # set segment remap
            0xa8,       # set multiplex ratio
            0x3f,       # set duty 1/64
            0xc8,       # set com scan direction
            0xd3, 0x00, # set display offset
            0xd5, 0x80, # set osc division
            0xd9, 0xf1, # set pre-charge period
            0xda, 0x12, # set com pins
            0xdb, 0x40, # set vcomh
            0x8d, 0x14, # set charge pump on
            0xa6,       # set display normal (not inverse)
            0x20, 0x00, # set horizontal addressing mode
            0xaf        # set display on
        ])

    def loop(self):

        while not self.loop_break:
            time.sleep(self.polling_interval)
            self.current_time = time.time()

            if self.keydown(1):
                continue

            if self.keydown(2):
                continue

            if self.keydown(3):
                continue

            # not here until all key are released
            self.keymap = self.state2keymap[self.state]

            if self.current_time > self.display_off_time:
                self.display_off()
                continue
 
            elif self.current_time > self.display_refresh_time:
                self.display_on()
                self.state2cmd[self.state](self)

    def cleanup(self):

        self.display_off(force=True)

        # release GPIO
        for key in self.keys:
            with open('/sys/class/gpio/unexport', 'w') as f:
                pin = self.key2pin[key]
                f.write('%d\n' % pin)

        # do it again just in case
        self.display_off(force=True)
        time.sleep(1)

        if self.state == SHUTDOWN:
            print("shutdown!")
            os.system('shutdown now')
        elif self.state == REBOOT:
            print("reboot!")
            os.system('reboot')
        else:
            exit(0)

    def run(self):
        try:
            self.init_setup()
            self.loop()

        except KeyboardInterrupt:
            print(' CTRL+C detected')

        finally:
            self.cleanup()

    def keydown(self, idx):
        dev_tmpl = '/sys/class/gpio/gpio%d/value'
        pin = self.key2pin[idx]
        dev = dev_tmpl % pin
        with open(dev) as f:
            if f.read(1) == '1':
                self.state = self.keymap[idx - 1]
                self.display_refresh_time = 0
                self.extend_display_off_time()
                return True
            else:
                return False

    def putline(self, line, pos=None, inverted=False):
        if not pos:
            if self.lines:
                pos = max(self.lines.keys()) + 1
            else:
                pos = 0

        if pos >= self.line_num:
            return

        char_num = len(line)
        diff = self.line_length - char_num
        if diff > 0:
            line = line + ' ' * diff
        else:
            line = line[:self.line_length]

        if inverted:
            font = inverted_font
        else:
            font = normal_font

        line_bs = [b for c in line for b in font.get(c, unknown_char)]

        self.lines[pos] = line_bs

    def display_flush(self):
        space = normal_font[' ']
        empty_line = space * self.line_length

        bs = [b for idx in range(self.line_num)
              for b in self.lines.get(idx, empty_line)]

        self.draw_bytes(bs)

    def clear_lines(self):
        for i in range(self.line_num):
            if i in self.lines:
                del(self.lines[i])

    def display_off(self, force=False):
        if (not self.display_already_off) or force:
            self.bus.write_i2c_block_data(0x3c, 0x00, [0xae])
            self.gen_random_splash()
            self.display_already_off = True

    def display_on(self):
        self.bus.write_i2c_block_data(0x3c, 0x00, [0xaf])
        self.display_already_off = False

    def draw_bytes(self, bs):
        blocks = chunks(bs, 32)
        for block in blocks:
            self.bus.write_i2c_block_data(0x3c, 0x40, block)

    def gen_random_splash(self):
        byte_num = int(128 * 64 / 8)
        self.splash = [random.randrange(256) for i in range(byte_num)]

    def extend_display_off_time(self, timeout=None):
        if not timeout:
            timeout = self.display_off_timeout

        self.display_off_time = self.current_time + timeout
