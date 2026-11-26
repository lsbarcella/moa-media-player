# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Blocos reutilizáveis da interface: botão com texto, capa de disco, aviso.

Regras do projeto que estes blocos garantem em um lugar só:
- Todo botão tem TEXTO (o ícone, quando existe, só acompanha).
- Um clique ativa; nada de arrastar, duplo clique ou botão direito.
- As cores e os tamanhos vêm do tema (`theme.py`), por classes de estilo.
"""

from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, GLib, Gtk, Pango, PangoCairo  # noqa: E402

from moa.core.covers import substitute_cover  # noqa: E402

LADO_DA_CAPA = 150
LADO_DA_CAPA_PEQUENA = 84


def rotulo(texto: str, *classes: str, quebrar: bool = True, centro: bool = False,
           xalign: float = 0.0, largura_maxima: int = 0) -> Gtk.Label:
    """Um texto na tela. Quebra de linha ligada, para caber com a letra grande."""
    etiqueta = Gtk.Label(label=texto)
    etiqueta.set_line_wrap(quebrar)
    etiqueta.set_xalign(0.5 if centro else xalign)
    if largura_maxima:
        etiqueta.set_max_width_chars(largura_maxima)    # sem isto a grade fica com poucas colunas
    if centro:
        etiqueta.set_justify(Gtk.Justification.CENTER)
    for classe in classes:
        etiqueta.get_style_context().add_class(classe)
    return etiqueta


PASTA_DOS_ICONES = Path(__file__).parent / "icons"
NOMES_DOS_ICONES = ("tocar", "pausar", "anterior", "proxima", "volume", "voltar",
                    "engrenagem", "mais", "caixa", "disco")
LADO_DO_ICONE = 32


def icone(nome: str, cor: str = "#1E1913", fundo: str = "#FFFFFF",
          lado: int = LADO_DO_ICONE) -> Gtk.Image:
    """Um ícone de aparelho antigo (SVG original do projeto), na cor pedida.

    Ícone nunca vem sozinho: sempre acompanha um texto (restrição do projeto).
    """
    svg = (PASTA_DOS_ICONES / f"{nome}.svg").read_text(encoding="utf-8")
    svg = svg.replace("__COR__", cor).replace("__FUNDO__", fundo)
    carregador = GdkPixbuf.PixbufLoader.new_with_type("svg")
    carregador.set_size(lado, lado)
    carregador.write(svg.encode("utf-8"))
    carregador.close()
    imagem = Gtk.Image.new_from_pixbuf(carregador.get_pixbuf())
    imagem.set_valign(Gtk.Align.CENTER)
    return imagem


# Botões de fundo escuro (verde, preto) levam o ícone branco.
_CLASSES_DE_FUNDO_ESCURO = {"moa-pri", "moa-tocar"}


def botao(texto: str, *classes: str, ao_clicar=None, icone_nome: str | None = None) -> Gtk.Button:
    """Botão grande com texto sempre visível (e ícone opcional ao lado)."""
    b = Gtk.Button()
    caixa = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    caixa.set_halign(Gtk.Align.CENTER)
    if icone_nome is not None:
        escuro = bool(_CLASSES_DE_FUNDO_ESCURO & set(classes))
        caixa.pack_start(icone(icone_nome, "#FFFFFF" if escuro else "#1E1913",
                               "#1E1913" if escuro else "#FFFFFF"), False, False, 0)
    etiqueta = Gtk.Label(label=texto)
    etiqueta.set_line_wrap(True)
    etiqueta.set_justify(Gtk.Justification.CENTER)
    caixa.pack_start(etiqueta, False, False, 0)
    b.add(caixa)
    contexto = b.get_style_context()
    contexto.add_class("moa-btn")
    for classe in classes:
        contexto.add_class(classe)
    if ao_clicar is not None:
        b.connect("clicked", lambda _b: ao_clicar())
    b.set_focus_on_click(True)
    return b


def caixa_v(espaco: int = 12) -> Gtk.Box:
    return Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=espaco)


def caixa_h(espaco: int = 12) -> Gtk.Box:
    return Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=espaco)


def limpar(contêiner: Gtk.Container) -> None:
    for filho in contêiner.get_children():
        contêiner.remove(filho)


_cache_de_imagens: dict[tuple[str, int], GdkPixbuf.Pixbuf | None] = {}


def _carregar_miniatura(caminho: Path, lado: int) -> GdkPixbuf.Pixbuf | None:
    chave = (str(caminho), lado)
    if chave not in _cache_de_imagens:
        try:
            _cache_de_imagens[chave] = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(caminho), lado, lado, False)
        except GLib.Error:
            _cache_de_imagens[chave] = None
    return _cache_de_imagens[chave]


class Capa(Gtk.DrawingArea):
    """A capa de um disco: a miniatura, ou o nome em letras grandes sobre uma cor.

    A capa substituta é desenhada (sem arquivo), com a mesma cor sempre para o
    mesmo nome (regra do M1) e texto branco de alto contraste.
    """

    def __init__(self, disco, miniatura: Path | None, lado: int = LADO_DA_CAPA):
        super().__init__()
        self.lado = lado
        self._pixbuf = _carregar_miniatura(miniatura, lado) if miniatura else None
        self._substituta = substitute_cover(disco)
        self.set_size_request(lado, lado)
        self.set_halign(Gtk.Align.CENTER)
        self.get_style_context().add_class("moa-capa")
        self.connect("draw", self._desenhar)

    def _desenhar(self, _area, cr) -> bool:
        lado = self.lado
        if self._pixbuf is not None:
            Gtk.render_background(self.get_style_context(), cr, 0, 0, lado, lado)
            from gi.repository import Gdk
            Gdk.cairo_set_source_pixbuf(cr, self._pixbuf,
                                        (lado - self._pixbuf.get_width()) / 2,
                                        (lado - self._pixbuf.get_height()) / 2)
            cr.paint()
            return False
        fundo = self._substituta.background
        cr.set_source_rgb(*(int(fundo[i:i + 2], 16) / 255 for i in (1, 3, 5)))
        cr.rectangle(0, 0, lado, lado)
        cr.fill()
        cor = self._substituta.text_color
        cr.set_source_rgb(*(int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5)))
        layout = PangoCairo.create_layout(cr)
        fonte = Pango.FontDescription("Sans Bold")
        fonte.set_absolute_size(20 * Pango.SCALE)     # texto nunca abaixo de 20 px
        layout.set_font_description(fonte)
        layout.set_width((lado - 16) * Pango.SCALE)
        layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        layout.set_alignment(Pango.Alignment.CENTER)
        layout.set_ellipsize(Pango.EllipsizeMode.END)
        layout.set_height((lado - 16) * Pango.SCALE)
        layout.set_text(self._substituta.title, -1)
        _, altura = layout.get_pixel_size()
        cr.move_to(8, max(8, (lado - altura) / 2))
        PangoCairo.show_layout(cr, layout)
        return False


def aviso(texto: str, ao_desfazer=None) -> Gtk.Widget:
    """Faixa de aviso calmo. Fica até a próxima ação do usuário."""
    caixa = caixa_h(14)
    caixa.get_style_context().add_class("moa-aviso")
    caixa.pack_start(rotulo(texto), True, True, 0)
    if ao_desfazer is not None:
        caixa.pack_start(botao("Desfazer", ao_clicar=ao_desfazer), False, False, 0)
    caixa.set_margin_bottom(14)
    return caixa
