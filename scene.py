cmd_map = {}

def setframe(scene, n):
    scene.frame = n
    
cmd_map['setframe'] = setframe

class Scene(object):
    _next_id = 0

    @classmethod
    def _inc_next_id(cls):
        cls._next_id += 1

    def __init__(self,
                 draw_func, init_func=None, keymap=None, keyfunc=None,
                 clear=True, flush=True, refresh_interval=0.1):

        self._id = self._next_id
        self._inc_next_id()

        self._init_func = init_func
        self._draw_func = draw_func
        self._keymap = keymap if keymap else {}
        self._keyfunc = keyfunc

        self.clear = clear
        self.flush = flush
        self.refresh_interval = refresh_interval

        self._state = {}
        self.frame = 0

    def __int__(self):
        return self._id

    def init(self, oledctrl, reset_frame=True):
        # self._init_func may be empty
        if reset_frame:
            self.frame = 0

        if self._init_func:
            new_state, cmds = self._init_func(self._state, oledctrl)
            self.handle_cmds(cmds)
            return new_state

    def draw(self, oledctrl, inc_frame=1):
        new_state, cmds = self._draw_func(self._state, oledctrl)
        self.handle_cmds(cmds)
        return inc_frame

    def add_keymap_entry(self, key, entry):
        self._keymap[key] = entry

    def add_keymap_entries(self, *kes):
        for key, entry in kes:
            self.add_keymap_entry(key, entry)

    def handle_key(self, key):
        """handle key input/press

        Parameters:
        key: either parameter used by `self._keyfunc` or key of `self._keymap`

        Returns:
        Scene: new scene.
        if scene does not change return None

        if `self._keyfunc` exist, then use it first"""

        if self._keyfunc:
            res = self._keyfunc(key, self._state)
        else:
            handler = self._keymap[key]
            try:
                res = handler(self._state)
            except TypeError as e:
                res = (handler, ())

        new_state, cmds = res
        self.handle_cmds(cmds)
        return new_state

    def handle_cmds(self, cmds):
        if cmds:
            for cmdl in cmds:
                cmd = cmdl[0]
                args = cmdl[1:]
                self.handle_cmd(cmd, args)

    def handle_cmd(self, cmd, args):
        cmd_f = cmd_map[cmd]
        cmd_f(self, *args)
