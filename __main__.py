import time
from oled import OLEDCtrl, SHUTDOWN, REBOOT

def zero_f(ctrl):
    ctrl.draw_bytes(ctrl.splash)
    ctrl.extend_display_next_refresh_time(10)

def one_f(ctrl):
    ctrl.clear_lines()
    ctrl.putline('1 pressed')
    ctrl.putline('1 pressed', inverted=True)
    ctrl.display_flush()
    ctrl.extend_display_next_refresh_time(10)

def two_f(ctrl):
    ctrl.clear_lines()
    ctrl.putline('2 pressed')
    ctrl.putline('2 pressed', inverted=True)
    ctrl.display_flush()
    ctrl.extend_display_next_refresh_time(2)

def three_f(ctrl):
    ctrl.clear_lines()
    ctrl.putline('')
    ctrl.putline('Cancel', inverted=True)
    ctrl.putline('Shutdown')
    ctrl.putline('Reboot')
    ctrl.putline('')
    ctrl.putline('F1: Confirm')
    ctrl.putline('F3: Cycle opts')
    ctrl.display_flush()
    ctrl.extend_display_next_refresh_time(5)

def four_f(ctrl):
    ctrl.clear_lines()
    ctrl.putline('')
    ctrl.putline('Cancel')
    ctrl.putline('Shutdown', inverted=True)
    ctrl.putline('Reboot')
    ctrl.putline('')
    ctrl.putline('F1: Confirm')
    ctrl.putline('F3: Cycle opts')
    ctrl.display_flush()
    ctrl.extend_display_next_refresh_time(5)

def five_f(ctrl):
    ctrl.clear_lines()
    ctrl.putline('')
    ctrl.putline('Cancel')
    ctrl.putline('Shutdown')
    ctrl.putline('Reboot', inverted=True)
    ctrl.putline('')
    ctrl.putline('F1: Confirm')
    ctrl.putline('F3: Cycle opts')
    ctrl.display_flush()
    ctrl.extend_display_next_refresh_time(5)

def shutdown_f(ctrl):
    ctrl.loop_break = True
    ctrl.display_off(force=True)

def reboot_f(ctrl):
    ctrl.loop_break = True
    ctrl.display_off(force=True)

def main():
    scene2keymap = {}
    scene2keymap[0] = [1, 2, 3]
    scene2keymap[1] = [0, 2, 3]
    scene2keymap[2] = [1, 0, 3]
    scene2keymap[3] = [1, 2, 4]
    scene2keymap[4] = [SHUTDOWN, 4, 5]
    scene2keymap[5] = [REBOOT, 5, 3]
    scene2keymap[SHUTDOWN] = [0, 0, 0]
    scene2keymap[REBOOT] = [0, 0, 0]
    
    scene2cmd = {}
    scene2cmd[0] = zero_f
    scene2cmd[1] = one_f
    scene2cmd[2] = two_f
    scene2cmd[3] = three_f
    scene2cmd[4] = four_f
    scene2cmd[5] = five_f

    scene2cmd[SHUTDOWN] = shutdown_f
    scene2cmd[REBOOT] = reboot_f

    main_ctrl = OLEDCtrl(scene2keymap, scene2cmd)
    main_ctrl.run()

if __name__ == '__main__':
    main()
