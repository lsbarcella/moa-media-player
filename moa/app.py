# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Aplicação GTK. Gtk.Application garante instância única via D-Bus."""

import logging
import os
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, Gtk  # noqa: E402

from moa.core import autostart, logsetup  # noqa: E402
from moa.core.config import Preferencias  # noqa: E402
from moa.core.contexto import Contexto  # noqa: E402
from moa.core.db import Database  # noqa: E402
from moa.ui.loader import Carregador  # noqa: E402
from moa.ui.window import MainWindow  # noqa: E402

APPLICATION_ID = "br.tcc.Moa"


def pasta_de_musica() -> Path:
    """A pasta de música do sistema (no Mint em português, ~/Música).

    `MOA_PASTA_DE_MUSICA` permite apontar para outra pasta (usado nas medições
    e nos testes com a coleção sintética).
    """
    outra = os.environ.get("MOA_PASTA_DE_MUSICA")
    if outra:
        return Path(outra)
    sistema = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC)
    return Path(sistema) if sistema else Path.home() / "Music"


def pasta_de_dados() -> Path:
    return Path(GLib.get_user_data_dir()) / "moa"


class MoaApp(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id=APPLICATION_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.contexto: Contexto | None = None

    def do_startup(self) -> None:
        """Roda uma vez, no primeiro processo (as aberturas seguintes só pedem a janela)."""
        Gtk.Application.do_startup(self)
        dados = pasta_de_dados()
        logsetup.configurar_log(dados)
        logsetup.instalar_gancho_de_excecao(self._avisar_falha)
        logging.getLogger(__name__).info("Moa Media Player iniciado")
        autostart.garantir(Path(GLib.get_user_config_dir()), dados)

    def _avisar_falha(self) -> None:
        """Mostra a frase calma. Pode vir de outra thread, então passa pela principal."""
        GLib.idle_add(self._mostrar_falha)

    def _mostrar_falha(self) -> bool:
        if self.contexto is not None:
            self.contexto.session.mostrar_falha(logsetup.MSG_FALHA_INESPERADA)
        return False        # False = não repetir

    def do_activate(self) -> None:
        # Se a janela já existe (app aberto de novo), só a traz para frente.
        window = self.props.active_window
        if window is None:
            dados = pasta_de_dados()
            caminho_do_banco = dados / "moa.db"
            banco = Database.open(caminho_do_banco)
            self.contexto = Contexto(banco, Preferencias(), pasta_de_musica(),
                                     pasta_miniaturas=dados / "miniaturas")
            window = MainWindow(self.contexto, application=self)
            Carregador(self.contexto, caminho_do_banco, dados / "miniaturas").iniciar()
        window.present()
