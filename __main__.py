import time

from oled import OLEDCtrl, SHUTDOWN, REBOOT
from scene import Scene

def prepare_ctrl():
    def draw0(state, ctrl):
        ctrl.putline("lasdlsfad laks alsfdkjd")

    s0 = Scene(draw_func=draw0, refresh_interval=5)

    def init1(state, ctrl):
         state['select'] = 0

    def draw1(state, ctrl):
        line = '1 pressed hahahadsflkjasl lask'
        for idx in (0, 1):
            if state['select'] == idx:
                ctrl.putline(line, inverted=True, mode='scroll')
            else:
                ctrl.putline(line)

    def s1_key1_handler(state):
        state['select'] = 1 - state['select']
        return (None, [('setframe', 0)])

    s1 = Scene(draw_func=draw1, init_func=init1)
    s1.add_keymap_entry(1, s1_key1_handler)

    def draw2(state, ctrl):
        ctrl.putline('2 pressed')
        ctrl.putline('2 pressed', inverted=True)

    s2 = Scene(draw_func=draw2)

    def draw3(state, ctrl):
        ctrl.putline('')
        ctrl.putline('Cancel', inverted=True)
        ctrl.putline('Shutdown')
        ctrl.putline('Reboot')
        ctrl.putline('')
        ctrl.putline('F1: Confirm')
        ctrl.putline('F3: Cycle opts')

    s3 = Scene(draw_func=draw3)

    def shutdown_f(ctrl):
        ctrl.loop_break = True
        ctrl.display_off(force=True)

    def reboot_f(ctrl):
        ctrl.loop_break = True
        ctrl.display_off(force=True)

    s0.add_keymap_entries(
        (1, s1),
        (2, s2),
        (3, s3),
    )

    s1.add_keymap_entries(
        (2, s2),
        (3, s3),
    )

    s2.add_keymap_entries(
        (1, s1),
        (2, None),
        (3, s3),
    )

    s3.add_keymap_entries(
        (1, s1),
        (2, s2),
        (3, None),
    )

    ctrl = OLEDCtrl(init_scene=s0)
    return ctrl


def main():

    main_ctrl = prepare_ctrl()
    main_ctrl.run()

if __name__ == '__main__':
    main()
