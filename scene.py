class Scene(object):
    _next_id = 1

    @classmethod
    def _inc_next_id(cls):
        cls._next_id += 1
        
    def __init__(self,
                 init_func, draw_func, keymap=None, keyfunc=None,
                 clear=True, flush=True, refresh_interval=1):

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
        self._init_func(self._state, oledctrl)
        if reset_frame:
            self.frame = 0

    def draw(self, oledctrl, inc_frame=True):
        self._draw_func(self._state, oledctrl)
        if inc_frame:
            self.frame += 1

    def add_keymap_entry(key, entry):
        self._keymap[key] = entry

    def handle_key(self, key):
        """handle key input/press

        Parameters:
        key: either parameter used by `self._keyfunc` or key of `self._keymap`

        Returns:
        Scene: new scene.
        if scene does not change return None

        if `self._keyfunc` exist, then use it first"""

        if self._keyfunc:
            return self._keyfunc(key, self._state)
        else:
            handler = self._keymap[key]
            try:
                return handler(self._state)
            except TypeError:
                return handler
