import pyglet

KEY_MAP = {
    pyglet.window.key.F: 'fullscreen',
    pyglet.window.key.S: 'screenshot',
    pyglet.window.key.ESCAPE: 'end',
    pyglet.window.key.LEFT: 'left',
    pyglet.window.key.RIGHT: 'right',
    pyglet.window.key.UP: 'up',
    pyglet.window.key.DOWN: 'down',
}

class Window(pyglet.window.Window):
    def __init__(self, initial_scene, **kwargs):
        super().__init__(width=1024, height=576, resizable=True)
        self.scene = initial_scene

    def run(self, fps=30):
        pyglet.clock.schedule_interval(self.tick, 1/fps)
        pyglet.app.run()

    def on_draw(self):
        self.clear()

        # Draw current scene
        try:
            self.scene.draw()
        except:
            import traceback
            traceback.print_exc()
            raise
        pyglet.text.Label('#1  ×2  4/5  100%  +300  25-03-2020', font_name='Aldrich', font_size=29, y=2*8+2, x=6*8).draw()
        pyglet.text.Label('30  -5', font_name='Aldrich', font_size=29/2, y=0*8+2, x=6*8).draw()

    def tick(self, dt):
        self.scene.tick(dt)

    def on_key_press(self, key, mod):
        command = KEY_MAP.get(key)
        if command == 'fullscreen':
            self.set_fullscreen(not self.fullscreen)
        elif command == 'end':
            raise KeyboardInterrupt()
        elif command == 'screenshot':
            pyglet.image.get_buffer_manager().get_color_buffer().save('screenshot.png')
        elif command is not None:
            self.scene.handle_command(command)
