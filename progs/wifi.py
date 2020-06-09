import time
from operator import itemgetter

from consts import SHUTDOWN, REBOOT, EXIT
from oled import OLEDCtrl
from scene import Scene, MessageScene, KbInputScene, popme
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
    def s2_init(state):
        conns = utils.get_saved_connections()
        conns.sort(key=itemgetter('up', 'name'))
        state['conns'] = conns
        state['selected'] = 0

    def s2_draw(state, disp):

        conns = state['conns']
        selected = state['selected']

        conn_lines = [str(conn['up']) + ' ' + conn['name'] for conn in conns]
        lines = ['cancel'] + conn_lines + ['new connection']

        if selected >= disp.line_num:
            start = selected - disp.line_num + 1
            end = selected + 1
        else:
            start = 0
            end = disp.line_num

        on_screen_lines = lines[start:end]

        for idx, line in enumerate(on_screen_lines):

            if start + idx == state['selected']:
                inverted = True
                mode = 'scroll'
            else:
                inverted = False
                mode = 'truncate'

            disp.putline(line, inverted=inverted, mode=mode)

    s2 = Scene(init_func=s2_init, draw_func=s2_draw,
               refresh_interval=0.3)

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

    # scene 4 add wifi ap
    def s4_init(state):
        state['selected'] = 0
        aps = utils.get_wifi_aps()
        faps = [ap for ap in aps if ap['in_use'] == 0]
        faps.sort(key=itemgetter('strength', 'ssid'), reverse=True)
        state['aps'] = faps

    def s4_draw(state, disp):
        aps = state['aps']
        selected = state['selected']

        def format_strenght(n):
            return str(n) if n < 100 else '??'

        ap_lines = [format_strenght(ap['strength']) + ' ' + ap['ssid'] for ap in aps]
        lines = ['cancel'] + ap_lines

        if selected >= disp.line_num:
            start = selected - disp.line_num + 1
            end = selected + 1
        else:
            start = 0
            end = disp.line_num

        on_screen_lines = lines[start:end]

        for idx, line in enumerate(on_screen_lines):

            if start + idx == state['selected']:
                inverted = True
                mode = 'scroll'
            else:
                inverted = False
                mode = 'truncate'

            disp.putline(line, inverted=inverted, mode=mode)

    s4 = Scene(init_func=s4_init, draw_func=s4_draw)

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

    def s2_key1_handler(state):
        selected = state['selected']
        conns = state['conns']
        conn_num = len(conns)

        if selected == 0:
            # 'cancel' -> s0
            new_scene = s0
        elif selected == conn_num + 1:
            # 'new connection' -> new connection scene
            new_scene = ('push', s4)
        else:
            selected_conn = conns[selected - 1]
            up = selected_conn['up']
            uuid = selected_conn['uuid']

            if up == 0:
                action = 'up'
            else:
                action = 'down'

            cmd_tmpl = 'nmcli connection %s uuid %s'
            cmd = cmd_tmpl % (action, uuid)
            code, msg = utils.run_cmd_with_timeout(cmd, 15)
            new_scene = None

        return (new_scene, [])

    def s2_key2_handler(state):
        selected = state['selected']
        conns = state['conns']
        conn_num = len(conns)
        state['selected'] = (selected + 1) % (conn_num + 2)

    s2.add_keymap_entries(
        (1, s2_key1_handler),
        (2, s2_key2_handler),
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


    # s4 keymap

    # create a new scene for connect to certain ap
    def create_ap_connect_scene(ssid):
        cmd_tmpl = 'nmcli device wifi connect "%s" password "%s"'
        message = 'input password for %s' % ssid

        def input_finish_func(s, status, state):
            if status == 'cancel':
                return (popme, [])
            elif status == 'confirmed':
                passwd = s
                cmd = cmd_tmpl % (ssid, passwd)
                utils.run_cmd_with_timeout(cmd, 100)
                return (s2, [])

        apc_scene = KbInputScene(input_finish_func,
                                 message=message,
                                 password=True)
        return apc_scene

    def s4_key1_handler(state):
        selected = state['selected']
        aps = state['aps']
        ap_num = len(aps)

        if selected == 0:
            # 'cancel' -> back to previous scene
            new_scene = popme

        else:
            selected_ap = aps[selected - 1]
            selected_ssid = selected_ap['ssid']
            new_scene = create_ap_connect_scene(selected_ssid)
            new_scene = ('push', new_scene)

        return (new_scene, [])

    # cycle through options
    def s4_key2_handler(state):
        selected = state['selected']
        aps = state['aps']
        ap_num = len(aps)
        state['selected'] = (selected + 1) % (ap_num + 1)

    s4.add_keymap_entries(
        (1, s4_key1_handler),
        (2, s4_key2_handler),
        (3, s3),
    )

    ctrl = OLEDCtrl(init_scene=s0)
    return ctrl


def main():

    main_ctrl = prepare_ctrl()
    main_ctrl.run()

if __name__ == '__main__':
    main()
