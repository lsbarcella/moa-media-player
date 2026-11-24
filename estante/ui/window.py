"""Janela principal. Neste marco (M0) ela é só uma janela vazia em tela cheia."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs) -> None:
        super().__init__(title="Estante", **kwargs)
        self.add(Gtk.Label(label="Estante"))
        self.fullscreen()
        self.show_all()
