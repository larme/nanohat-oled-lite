cmd_map = {}

def setframe(scene, n):
    scene.frame = n

def addframe(scene, n):
    scene.frame += n
    
cmd_map['setframe'] = setframe
cmd_map['addframe'] = addframe

class Scene(object):
    _next_id = 0

    @classmethod
    def _inc_next_id(cls):
        cls._next_id += 1

    def __init__(self, _id=None,
                 draw_func=None, init_func=None, finish_func=None,
                 keymap=None, keyfunc=None,
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
        self._keyfunc = keyfunc

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
        key: either parameter used by `self._keyfunc` or key of `self._keymap`

        Returns:
        Scene: new scene.
        if scene does not change return None

        if `self._keyfunc` exist, then use it first"""

        if self._keyfunc:
            res = self._keyfunc(key, self._state)

        elif self._keymap:
            handler = self._keymap[key]
            try:
                res = handler(self._state)
            except TypeError as e:
                res = (handler, [])
        else:
            res = (handler, [])

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

