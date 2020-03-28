import pyglet

from .util import pushed_matrix

WIDTH = 1024
HEIGHT = 576

KEY_MAP = {
    pyglet.window.key.F: 'fullscreen',
    pyglet.window.key.S: 'screenshot',
    pyglet.window.key.ESCAPE: 'end',
    pyglet.window.key.LEFT: 'left',
    pyglet.window.key.RIGHT: 'right',
    pyglet.window.key.UP: 'up',
    pyglet.window.key.DOWN: 'down',

    **{getattr(pyglet.window.key, f'_{i}'): str(i) for i in range(10)},
    **{getattr(pyglet.window.key, f'NUM_{i}'): str(i) for i in range(10)},
}

class Window(pyglet.window.Window):
    def __init__(self, initial_scene, **kwargs):
        super().__init__(width=WIDTH, height=HEIGHT, resizable=True)
        self.scene = initial_scene

    def run(self, fps=30):
        pyglet.clock.schedule_interval(self.tick, 1/fps)
        pyglet.app.run()

    def on_draw(self):
        self.clear()

        if self.height / HEIGHT < self.width / WIDTH:
            zoom = self.height / HEIGHT
            translate_x = (self.width / zoom - WIDTH) / 2
            translate_y = 0
        else:
            zoom = self.width / WIDTH
            translate_x = 0
            translate_y = (self.height / zoom - HEIGHT) / 2

        with pushed_matrix():
            # Draw current scene
            pyglet.gl.glScalef(zoom, zoom, 1)
            pyglet.gl.glTranslatef(translate_x, translate_y, 1)
            try:
                self.scene.draw()
            except:
                import traceback
                traceback.print_exc()
                raise

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
            handle_command = getattr(self.scene, 'handle_command')
            if handle_command:
                handle_command(command)
