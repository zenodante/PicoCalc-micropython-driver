from .screen import Screen


class Context:

    def __init__(self, cls=True, mouse=True):
        self.cls = cls

    def __enter__(self):
        Screen.init_tty()
        if self.cls:
            Screen.cls()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        Screen.goto(1, 1)
        Screen.cursor(True)
        Screen.deinit_tty()
        # This makes sure that entire screenful is scrolled up, and
        # any further output happens on a normal terminal line.
        #print()
