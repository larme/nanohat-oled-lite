import time

from consts import SHUTDOWN, REBOOT, EXIT
from oled import OLEDCtrl
from scene import Scene
import utils

def prepare_ctrl():

    # scene shutdown
    s_shutdown = Scene(_id=SHUTDOWN)

    # scene reboot
    s_reboot = Scene(_id=REBOOT)

    # scene reboot
    s_exit = Scene(_id=EXIT)

    # scene 0
    def s0_draw(state, disp):
        disp.gen_random_splash()

    s0 = Scene(draw_func=s0_draw, line_mode=False, refresh_interval=1)

    # scene 1
    def s1_init(state):
         state['counter'] = 0


    def s1_draw(state, disp):

        if state['counter'] % 10 != 0:
            return

        def pl(line):
            disp.putline(line, mode='scroll')

        ip_lines = utils.get_ip_lines()
        for line in ip_lines:
            if not line:
                continue

            if line.startswith('lo '):
                continue

            pl(line)

        pl('')

        cpu_load_line = utils.get_cpu_load_line()
        pl(cpu_load_line)

        cpu_temp_line = utils.get_cpu_temp_line()
        pl(cpu_temp_line)

        mem_line = utils.get_mem_line()
        pl(mem_line)

        disk_line = utils.get_disk_line()
        pl(disk_line)

    s1 = Scene(draw_func=s1_draw, init_func=s1_init, refresh_interval=0.5)

    # scene 2
    def s2_draw(state, disp):
        disp.putline('2 pressed')
        disp.putline('2 pressed', inverted=True)

    s2 = Scene(draw_func=s2_draw)

    # scene 3
    def s3_init(state):
        state['selected'] = 0
        state['idx2opt'] = dict(enumerate(['cancel', 'shutdown', 'reboot']))
        state['handlers'] = {}

    def s3_draw(state, disp):
        selected = state['selected']
        idx2opt = state['idx2opt']

        disp.putline('')

        for idx in sorted(idx2opt.keys()):
            opt = idx2opt[idx]
            inverted = True if selected == idx else False
            disp.putline(opt, inverted=inverted)

        disp.putline('')
        disp.putline('F1: Confirm')
        disp.putline('F3: Cycle opts')

    s3 = Scene(init_func=s3_init, draw_func=s3_draw)

    # s0 keymap
    s0.add_keymap_entries(
        (1, s1),
        (2, s2),
        (3, s3),
    )

    # s1 keymap

    s1.add_keymap_entries(
        (1, s0),
        (2, s2),
        (3, s3),
    )

    # s2 keymap

    s2.add_keymap_entries(
        (1, s1),
        (2, None),
        (3, s3),
    )

    # s3 keymap
    # exec option
    def s3_key1_handler(state):
        selected = state['selected']
        idx2opt = state['idx2opt']
        selected_opt = idx2opt[selected]

        if selected_opt == 'cancel':
            new_scene = s0
        elif selected_opt == 'reboot':
            new_scene = s_reboot
        else:
            new_scene = s_shutdown

        return (new_scene, [])

    s3.add_keymap_entry(1, s3_key1_handler)

    # cycle through options
    def s3_key3_handler(state):
        selected = state['selected']
        opt_num = len(state['idx2opt'])
        state['selected'] = (selected + 1) % opt_num

    s3.add_keymap_entry(3, s3_key3_handler)

    s3.add_keymap_entries(
        (2, s2),
    )

    ctrl = OLEDCtrl(init_scene=s0)
    return ctrl


def main():

    main_ctrl = prepare_ctrl()
    main_ctrl.run()

if __name__ == '__main__':
    main()
