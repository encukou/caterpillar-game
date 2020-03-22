import pyglet

class Window(pyglet.window.Window):
    def __init__(self, initial_scene):
        super().__init__(width=1024, height=576, resizable=True)
        self.scene = initial_scene

    def run(self, fps=30):
        pyglet.app.run()

    def on_draw(self):
        # Set up alpha blending
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)

        # Draw current scene
        self.scene.draw()

    def on_key_press(self, key, mod):
        if key == pyglet.window.key.F:
            self.set_fullscreen(not self.fullscreen)
            print(self.width)
            print(self.height)
