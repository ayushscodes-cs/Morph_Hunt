import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ursina import Ursina, window

from client.client import ClientApp


_app_instance = None


def update():
    if _app_instance:
        _app_instance.update()


def input(key):
    if _app_instance:
        _app_instance.input(key)


def main():
    global _app_instance

    app = Ursina(
        title="Morph Hunt: The Object Among Us",
        borderless=False,
        fullscreen=False,
        development_mode=False,
        editor_ui_enabled=False,
        render_mode="default",
    )

    window.fullscreen = False
    window.borderless = False

    _app_instance = ClientApp()

    app.run()


if __name__ == "__main__":
    main()