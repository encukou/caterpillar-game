import traceback
import datetime

import pyglet

from .util import pushed_matrix
from .ui import LevelSelect

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
    pyglet.window.key.ENTER: 'go',

    **{getattr(pyglet.window.key, f'_{i}'): str(i) for i in range(10)},
    **{getattr(pyglet.window.key, f'NUM_{i}'): str(i) for i in range(10)},
}

class Window(pyglet.window.Window):
    def __init__(self, initial_scene=None, state=None, **kwargs):
        super().__init__(width=WIDTH, height=HEIGHT, resizable=True)
        self.set_caption('Caterpillar Effect')
        if initial_scene is None:
            initial_scene = LevelSelect(state, self)
        self.scene = initial_scene

    def run(self, fps=30):
        pyglet.clock.schedule_interval(self.tick, 1/fps)
        pyglet.app.run()

    def get_zoom_translate(self):
        if self.height / HEIGHT < self.width / WIDTH:
            zoom = self.height / HEIGHT
            translate_x = (self.width / zoom - WIDTH) / 2
            translate_y = 0
        else:
            zoom = self.width / WIDTH
            translate_x = 0
            translate_y = (self.height / zoom - HEIGHT) / 2
        return zoom, translate_x, translate_y

    def on_draw(self):
        self.clear()

        zoom, translate_x, translate_y = self.get_zoom_translate()

        with pushed_matrix():
            # Draw current scene
            pyglet.gl.glScalef(zoom, zoom, 1)
            pyglet.gl.glTranslatef(translate_x, translate_y, 0)
            try:
                self.scene.draw()
            except:
                traceback.print_exc()
                raise

    def tick(self, dt):
        self.scene.tick(dt)

    def on_key_press(self, key, mod):
        try:
            command = KEY_MAP.get(key)
            if command == 'fullscreen':
                self.set_fullscreen(not self.fullscreen)
            elif command == 'screenshot':
                filename = f'screenshot-{datetime.datetime.now().isoformat(timespec="seconds")}.png'
                print('saving screenshot to:', filename)
                pyglet.image.get_buffer_manager().get_color_buffer().save(filename)
            elif command is not None:
                handle_command = getattr(self.scene, 'handle_command')
                if handle_command:
                    handled = handle_command(command)
                    if handled:
                        return

            if command == 'end':
                self.close()
        except:
            traceback.print_exc()
            raise

    def on_mouse_press(self, x, y, button, mod):
        zoom, translate_x, translate_y = self.get_zoom_translate()

        x = x / zoom - translate_x
        y = y / zoom - translate_y

        handle_click = getattr(self.scene, 'handle_click')
        if handle_click:
            handled = handle_click(x, y)
            if handled:
                return
