from .screen import Screen


class Context:

    def __init__(self):
        pass

    def __enter__(self):
        Screen.init_tty()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        Screen.deinit_tty()
        # This makes sure that entire screenful is scrolled up, and
        # any further output happens on a normal terminal line.
        print()
