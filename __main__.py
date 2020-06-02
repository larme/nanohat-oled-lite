import time
from oled import OLEDCtrl, SHUTDOWN

def zero_f(ctrl):
    ctrl.draw_bytes(ctrl.splash)
    ctrl.display_refresh_time = time.time() + ctrl.display_off_timeout

def one_f(ctrl):
    ctrl.clear_lines()
    ctrl.putline('1 pressed')
    ctrl.putline('1 pressed', inverted=True)
    ctrl.display_flush()

def two_f(ctrl):
    ctrl.clear_lines()
    ctrl.putline('2 pressed')
    ctrl.putline('2 pressed', inverted=True)
    ctrl.display_flush()

def three_f(ctrl):
    ctrl.clear_lines()
    ctrl.putline('No', inverted=True)
    ctrl.putline('Yes')
    ctrl.putline('F3: Toggle Choices')
    ctrl.display_flush()

def shutdown_f(ctrl):
    ctrl.loop_break = True

def four_f(ctrl):
    ctrl.clear_lines()
    ctrl.putline('No')
    ctrl.putline('Yes', inverted=True)
    ctrl.putline('F3: Toggle Choices')
    ctrl.display_flush()

def main():
    state2keymap = {}
    state2keymap[0] = [1, 2, 3]
    state2keymap[1] = [0, 2, 3]
    state2keymap[2] = [1, 0, 3]
    state2keymap[3] = [1, 2, 4]
    state2keymap[4] = [SHUTDOWN, 4, 3]
    state2keymap[SHUTDOWN] = [0, 0, 0]
    
    state2cmd = {}
    state2cmd[0] = zero_f
    state2cmd[1] = one_f
    state2cmd[2] = two_f
    state2cmd[3] = three_f
    state2cmd[4] = four_f

    state2cmd[SHUTDOWN] = shutdown_f

    main_ctrl = OLEDCtrl(state2keymap, state2cmd)
    main_ctrl.run()

if __name__ == '__main__':
    main()
