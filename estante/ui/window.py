"""Janela principal. Neste marco (M0) ela é só uma janela vazia, como qualquer programa."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs) -> None:
        super().__init__(title="Estante", **kwargs)
        self.add(Gtk.Label(label="Estante"))
        # Janela normal de programa, com barra de título e X visíveis (ADR-0002).
        self.set_default_size(1024, 700)
        self.show_all()
