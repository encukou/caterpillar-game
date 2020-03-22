import pyglet

class Window(pyglet.window.Window):
    def __init__(self):
        super().__init__(width=1024, height=576, resizable=True)

    def run(self):
        pyglet.app.run()

    def on_key_press(self, key, mod):
        if key == pyglet.window.key.F:
            self.set_fullscreen(not self.fullscreen)
            print(self.width)
            print(self.height)
