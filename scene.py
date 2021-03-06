import time

cmd_map = {}

def setframe(scene, n):
    scene.frame = n

def addframe(scene, n):
    scene.frame += n
    
cmd_map['setframe'] = setframe
cmd_map['addframe'] = addframe

popme = ('pop', None)

class Scene(object):
    _next_id = 0

    @classmethod
    def _inc_next_id(cls):
        cls._next_id += 1

    def __init__(self, _id=None,
                 draw_func=None, init_func=None, finish_func=None,
                 keymap=None, key_func=None,
                 clear=True, line_mode=True, flush=True, keep_state=False,
                 refresh_interval=0.1):

        if _id:
            self._id = _id
        else:
            self._id = self._next_id
            self._inc_next_id()

        self._init_func = init_func
        self._draw_func = draw_func
        self._finish_func = finish_func
        self._keymap = keymap if keymap else {}
        self._key_func = key_func

        self.clear = clear
        self.line_mode = line_mode
        self.flush = flush
        self.refresh_interval = refresh_interval
        self.keep_state = keep_state

        self.frame = 0
        self._state = {}
        self._post_cmds = []

    def __int__(self):
        return self._id

    # helper functions either return (new_scene, cmds) or None
    # set new_scene = None if there's no scene switch
    def _process_result(self, res):
        if res:
            new_scene, cmds = res
            self.handle_cmds(cmds)
            return new_scene
        else:
            return None

    def init(self, reset_frame=True):
        # self._init_func may be empty
        if reset_frame:
            self.frame = 0

        if self._init_func:
            if not self.keep_state:
                self._state.clear()

            res = self._init_func(self._state)
            return self._process_result(res)

    def draw(self, display, inc_frame=1):
        inc_frame_cmd = 'post_addframe'
        inc_frame_cmdl = (inc_frame_cmd, inc_frame)

        if self._draw_func:

            res = self._draw_func(self._state, display)
        
            if res:
                new_scene, cmds = res
            else:
                res = (None, [inc_frame_cmdl])
        else:
            res = (None, [inc_frame_cmdl])
        return self._process_result(res)

    def finish(self):
        if self._finish_func:
            res = self._finish_func()
            return self._process_result(res)

    def add_keymap_entry(self, key, entry):
        self._keymap[key] = entry

    def add_keymap_entries(self, *kes):
        for key, entry in kes:
            self.add_keymap_entry(key, entry)

    def handle_key(self, key):
        """handle key input/press

        Parameters:
        key: either parameter used by `self._key_func` or key of `self._keymap`

        Returns:
        Scene: new scene.
        if scene does not change return None

        if `self._key_func` exist, then use it first"""

        if self._key_func:
            res = self._key_func(key, self._state)

        elif self._keymap:
            handler = self._keymap[key]
            try:
                res = handler(self._state)
            except TypeError as e:
                res = (handler, [])
        else:
            res = (None, [])

        return self._process_result(res)

    def handle_cmds(self, cmds):
        if cmds:
            for cmdl in cmds:
                cmd = cmdl[0]
                args = cmdl[1:]

                if cmd.startswith('post_'):
                    cmd = cmd.replace('post_', '', 1)
                    new_cmdl = (cmd, ) + tuple(args)
                    self.push_to_post_cmds(new_cmdl)
                else:
                    self.handle_cmd(cmd, args)

    def handle_cmd(self, cmd, args):
        cmd_f = cmd_map[cmd]
        cmd_f(self, *args)

    def push_to_post_cmds(self, cmdl):
        self._post_cmds.append(cmdl)

    def run_post_cmds(self):
        if self._post_cmds:
            cmds = self._post_cmds
            self._post_cmds = []
            self.handle_cmds(cmds)

# scene for simply display messages
class MessageScene(Scene):

    def __init__(self, messages, mode='wrap', accept_key=True, timeout=None, **kwargs):

        super().__init__(**kwargs)

        def init_func(state):
            state['messages'] = messages
            if timeout:
                state['end_time'] = time.time() + timeout

        def draw_func(state, disp):
            for message in messages:
                disp.putline(message, mode=mode)
            end_time = state.get('end_time')
            if end_time and time.time() > end_time:
                return (popme, [])

        self._init_func = init_func
        self._draw_func = draw_func

        if accept_key:
            def key_func(key, state):
                return (popme, [])
            self._key_func = key_func

# keyboard doesn't handle shift well so we prepare our own map

def _prepare_shift_keymap():
    downs = r"""`1234567890[]-='\/;,."""
    ups   = r"""~!@#$%^&*(){}_+"|?:<>"""
    return dict(zip(downs, ups))

_shift_keymap = _prepare_shift_keymap()

def _get_shift_key(keyname):
    return _shift_keymap.get(keyname, keyname.upper())

# scene for simple keyboard input
class KbInputScene(Scene):

    def __init__(self, input_finish_func, message='type',
                 previous_scene=None, password=False, cancel_fkey=3,
                 confirm_keys={'enter'}, cancel_keys={'esc'},
                 delete_keys={'delete', 'backspace'},
                 **kwargs):

        import threading
        from importlib import reload
        import keyboard
        reload(keyboard)

        super().__init__(**kwargs)

        self._input_finish_func = input_finish_func
        self.previous_scene = previous_scene
        self.password = password
        self.cancel_fkey = cancel_fkey
        self.confirm_keys = confirm_keys
        self.cancel_keys = cancel_keys
        self.delete_keys = delete_keys

        self.lock = threading.Lock()
        self.status = ''
        self.shift = False
        self.buffer = []
        self.hooked = None

        def init_func(state):

            self.status = 'normal'
            self.buffer = []

            # install a keyboard hook
            self.hooked = None

            def hook_func(e):
                key = e.name

                if 'shift' in e.name and e.event_type == 'up':
                    with self.lock:
                        self.shift = False

                if e.event_type != 'down':
                    return

                if key in self.cancel_keys:
                    with self.lock:
                        self.buffer = []
                        self.status = 'cancel'
                        self.unhook()

                elif key in self.confirm_keys:
                    with self.lock:
                        self.status = 'confirmed'
                        self.unhook()

                elif key in self.delete_keys:
                    with self.lock:
                        if self.buffer:
                            self.buffer.pop()

                elif 'shift' in key:
                    with self.lock:
                        self.shift = True

                elif len(key) == 1:
                    with self.lock:
                        if self.shift:
                            key = _get_shift_key(key)
                        self.buffer.append(key)

            self.hooked = keyboard.hook(hook_func)

        self._init_func = init_func

        def draw_func(state, disp):

            with self.lock:
                l = self.buffer
                char_num = len(l)
                if char_num > 1 and self.password:
                    l = ['*'] * (char_num - 1) + [l[-1]]

                s = ''.join(l)
                disp.putline(message + ", F%d to cancel" % self.cancel_fkey)
                disp.putline(s, mode='wrap')
                disp.putline(self.status)
                if self.status in ('cancel', 'confirmed'):
                    s = ''.join(self.buffer)
                    return self._input_finish_func(s, self.status, self._state)

        self._draw_func = draw_func

        def key_func(key, state):
            if key == cancel_fkey:
                self.unhook()
                if self.previous_scene:
                    return (self.previous_scene, [])
                else:
                    return (popme, [])

        self._key_func = key_func

    def unhook(self):
        import keyboard
        try:
            keyboard.unhook(self.hooked)
        except KeyError:
            pass
