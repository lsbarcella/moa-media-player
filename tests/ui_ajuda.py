# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Ajudas para testar a interface sem abrir janela visível (KTD15).

`Gtk.OffscreenWindow` desenha o conteúdo numa imagem em memória. Precisa de uma
sessão gráfica (DISPLAY); sem ela, os testes de interface são pulados.
"""

import time
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402


def tem_display() -> bool:
    return Gdk.Display.get_default() is not None


def girar(segundos: float = 0.3) -> None:
    """Deixa o laço de eventos do GTK trabalhar um pouco (layout, desenho, mensagens)."""
    contexto = GLib.MainContext.default()
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        while contexto.iteration(False):
            pass
        time.sleep(0.01)


def desenhar(conteudo, destino: Path | None = None, largura: int = 1100, altura: int = 760):
    """Desenha o conteúdo numa janela fora da tela e devolve o Pixbuf (e grava o PNG)."""
    janela = Gtk.OffscreenWindow()
    janela.set_size_request(largura, altura)
    janela.add(conteudo.raiz)
    janela.show_all()
    girar(0.4)
    pixbuf = janela.get_pixbuf()
    if destino is not None:
        pixbuf.savev(str(destino), "png", [], [])
    janela.remove(conteudo.raiz)
    janela.destroy()
    return pixbuf


def todos_os_widgets(raiz: Gtk.Widget):
    """Percorre a árvore de widgets (para conferir tamanhos e textos)."""
    yield raiz
    if isinstance(raiz, Gtk.Container):
        for filho in raiz.get_children():
            yield from todos_os_widgets(filho)


def textos(raiz: Gtk.Widget) -> list[str]:
    return [w.get_text() for w in todos_os_widgets(raiz) if isinstance(w, Gtk.Label)]


def botoes(raiz: Gtk.Widget) -> list[Gtk.Button]:
    return [w for w in todos_os_widgets(raiz) if isinstance(w, Gtk.Button)]


def botao_com_texto(raiz: Gtk.Widget, texto: str) -> Gtk.Button:
    for b in botoes(raiz):
        if texto in textos(b):
            return b
    raise AssertionError(f"não achei o botão {texto!r}; textos na tela: {textos(raiz)}")
