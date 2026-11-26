"""Aplicação GTK. Gtk.Application garante instância única via D-Bus."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk  # noqa: E402

from moa.ui.window import MainWindow  # noqa: E402

APPLICATION_ID = "br.tcc.Moa"


class MoaApp(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id=APPLICATION_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self) -> None:
        # Se a janela já existe (app aberto de novo), só a traz para frente.
        window = self.props.active_window
        if window is None:
            window = MainWindow(application=self)
        window.present()
