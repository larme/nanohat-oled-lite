import os
import random
import smbus2 as smbus
import subprocess
import time

from consts import SHUTDOWN, REBOOT, EXIT
from fonts import normal_font, inverted_font, unknown_char

KEY2PIN = {
    1: 0,
    2: 2,
    3: 3,
}

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class OLEDCtrl(object):

    def __init__(self, init_scene,
                 key2pin=KEY2PIN, keys=(1, 2, 3),
                 bus_num=0, display_off_timeout=30.0,
                 polling_interval=0.2, turbo_polling_interval=0.01,
                 line_length=16, line_num=8):

        self.keys = keys
        self.key2pin = key2pin
        self.bus = smbus.SMBus(bus_num)
        self.polling_interval = polling_interval
        self.turbo_polling_interval = turbo_polling_interval
        self.display_off_timeout = display_off_timeout
        self.line_length = line_length
        self.line_num = line_num

        self.loop_break = False
        self.display_refresh_time = 0
        self.current_time = time.time()
        self.extend_display_off_time()

        self.display_already_off = False

        self.scene = init_scene
        self.pending_key = None
        self.pending_scene = None
        self.lines = {}
        self.buffer = {}

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

            if self.display_already_off:
                polling_interval = self.polling_interval
            else:
                polling_interval = self.turbo_polling_interval

            time.sleep(polling_interval)
            self.current_time = time.time()

            if self.keydown(1):
                continue

            if self.keydown(2):
                continue

            if self.keydown(3):
                continue

            # not here until all key are released
            # if pending_key or pending_scene exists, update scene

            new_scene = self.pending_scene
            self.pending_scene = None

            if self.pending_key:
                new_scene = self.scene.handle_key(self.pending_key)
                self.pending_key = None

            if new_scene:
                self.scene = new_scene
                new_scene = self.scene.init()
                self.scene.run_post_cmds()

                if new_scene:
                    self.pending_scene = new_scene
                    new_scene = None

            if int(self.scene) in (SHUTDOWN, REBOOT, EXIT):
                # or just break?
                self.loop_break = True

            if self.current_time > self.display_off_time:
                self.display_off()
                continue
 
            # one more frame
            elif self.current_time > self.display_refresh_time:
                self.display_on()
                s = self.scene
                if s.clear:
                    self.clear_lines()

                # scene draw lines to self.lines
                print(s.frame)
                new_scene = s.draw(self)
                self.render(clear=s.clear,
                            flush=s.flush,
                            line_mode=s.line_mode,
                            refresh_interval=s.refresh_interval)

                s.run_post_cmds()
                if new_scene:
                    self.pending_scene = new_scene
                    new_scene = None

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

        if int(self.scene) == SHUTDOWN:
            print("shutdown!")
            os.system('shutdown now')
        elif int(self.scene) == REBOOT:
            print("reboot!")
            os.system('reboot')
        else:
            exit(0)

    def run(self):
        try:
            self.init_setup()
            self.loop()

        except Exception as e:
            print("Error:", e)

        finally:
            self.cleanup()

    def keydown(self, idx):
        dev_tmpl = '/sys/class/gpio/gpio%d/value'
        pin = self.key2pin[idx]
        dev = dev_tmpl % pin
        with open(dev) as f:
            if f.read(1) == '1':
                self.pending_key = idx
                self.display_refresh_time = 0
                self.extend_display_off_time()
                return True
            else:
                return False

    def putline(self, line, pos=None, inverted=False, mode='truncate'):
        if not pos:
            if self.lines:
                pos = max(self.lines.keys()) + 1
            else:
                pos = 0

        if pos > self.line_num:
            return

        self.lines[pos] = (line, inverted, mode)

    def render(self, clear, line_mode, flush, refresh_interval):
        if clear:
            self.clear_buffer()

        if line_mode:
            self.lines_to_buffer()

        if flush:
            self.display_flush()

        if refresh_interval > 0:
            self.set_display_next_refresh_time(refresh_interval)

    def display_flush(self):
        self.render_buffer()

    def lines_to_buffer(self):
        for pos in range(self.line_num):
            line = self.lines.get(pos)
            if line:
                self.line_to_buffer(pos, *line)

    def line_to_buffer(self, pos, line, inverted, mode):

        if pos >= self.line_num:
            return

        if not line:
            line = ''

        char_num = len(line)

        if char_num > self.line_length:

            if mode == 'scroll':
                frame = self.scene.frame
                start = frame % char_num
                end = start + self.line_length
                line = line[start:end]
                lines = [line]

            elif mode == 'wrap':
                lines = list(chunks(line, self.line_length))

            # mode == 'truncate'
            else:
                line = line[:self.line_length]
                lines = [line]
        else:
            lines = [line]

        for idx, line in enumerate(lines):
            self._line_to_buffer(pos + idx, line, inverted)

    # here len(line) <= self.line_length
    def _line_to_buffer(self, pos, line, inverted):

        if pos >= self.line_num:
            return

        if not line:
            line = ''

        if inverted:
            font = inverted_font
        else:
            font = normal_font

        char_num = len(line)
        diff = self.line_length - char_num
        line = line + ' ' * diff

        line_bs = [b for c in line for b in font.get(c, unknown_char)]

        self.buffer[pos] = line_bs

    def render_buffer(self):
        space = normal_font[' ']
        empty_line = space * self.line_length

        bs = [b for idx in range(self.line_num)
              for b in self.buffer.get(idx, empty_line)]

        self._render_bytes(bs)

    def _render_bytes(self, bs):
        blocks = chunks(bs, 32)
        for block in blocks:
            self.bus.write_i2c_block_data(0x3c, 0x40, block)

    def clear_buffer(self):
        self.buffer.clear()

    def clear_lines(self):
        self.lines.clear()

    def display_off(self, force=False):
        if (not self.display_already_off) or force:
            self.bus.write_i2c_block_data(0x3c, 0x00, [0xae])
            self.gen_random_splash()
            self.display_already_off = True

    def display_on(self):
        self.bus.write_i2c_block_data(0x3c, 0x00, [0xaf])
        self.display_already_off = False

    def gen_random_splash(self):
        byte_num = int(128 * 64 / 8)
        self.splash = [random.randrange(256) for i in range(byte_num)]

    def extend_display_off_time(self, timeout=None):
        if not timeout:
            timeout = self.display_off_timeout

        self.display_off_time = self.current_time + timeout

    def set_display_next_refresh_time(self, timeout=1):
        self.display_refresh_time = self.current_time + timeout
