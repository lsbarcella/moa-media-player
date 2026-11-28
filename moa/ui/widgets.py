# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Blocos reutilizáveis da interface: botão com texto, capa de disco, aviso.

Regras do projeto que estes blocos garantem em um lugar só:
- Todo botão tem TEXTO (o ícone, quando existe, só acompanha).
- Um clique ativa; nada de arrastar, duplo clique ou botão direito.
- As cores e os tamanhos vêm do tema (`theme.py`), por classes de estilo.
"""

import logging
import time
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, GLib, Gtk, Pango, PangoCairo  # noqa: E402

from moa.core.covers import substitute_cover  # noqa: E402

log = logging.getLogger(__name__)

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


_cache_de_icones: dict[tuple[str, str, str, int], GdkPixbuf.Pixbuf] = {}


def icone(nome: str, cor: str = "#1E1913", fundo: str = "#FFFFFF",
          lado: int = LADO_DO_ICONE) -> Gtk.Image:
    """Um ícone de aparelho antigo (SVG original do projeto), na cor pedida.

    Ícone nunca vem sozinho: sempre acompanha um texto (restrição do projeto).
    O SVG é lido e convertido uma vez só por combinação (nome, cores, tamanho): uma lista
    com centenas de músicas pede o mesmo ícone centenas de vezes.
    """
    chave = (nome, cor, fundo, lado)
    pixbuf = _cache_de_icones.get(chave)
    if pixbuf is None:
        pixbuf = _converter_icone(nome, cor, fundo, lado)
        _cache_de_icones[chave] = pixbuf
    imagem = Gtk.Image.new_from_pixbuf(pixbuf)
    imagem.set_valign(Gtk.Align.CENTER)
    return imagem


def _converter_icone(nome: str, cor: str, fundo: str, lado: int) -> GdkPixbuf.Pixbuf:
    svg = (PASTA_DOS_ICONES / f"{nome}.svg").read_text(encoding="utf-8")
    svg = svg.replace("__COR__", cor).replace("__FUNDO__", fundo)
    carregador = GdkPixbuf.PixbufLoader.new_with_type("svg")
    carregador.set_size(lado, lado)
    carregador.write(svg.encode("utf-8"))
    carregador.close()
    return carregador.get_pixbuf()


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


class EmPedacos:
    """Faz uma lista longa de tarefas pequenas aos poucos, sem travar a tela.

    Montar centenas de linhas de uma vez deixa o notebook antigo parado por meio segundo ou mais.
    Aqui a primeira fatia (pelo menos `minimo` itens) é feita na hora, então as primeiras linhas
    já aparecem; o resto vem em fatias de ~`orcamento_ms` ms, devolvendo o controle ao GTK entre
    elas (cliques e teclas continuam sendo atendidos). Listas curtas terminam na própria chamada.

    Para o autor (vem de TypeScript): é como processar um array em lotes com `requestIdleCallback`.
    """

    def __init__(self, itens, fazer, minimo: int = 30, orcamento_ms: float = 10.0,
                 ao_terminar=None) -> None:
        self._itens = list(itens)
        self._fazer = fazer
        self._minimo = minimo
        self._orcamento = orcamento_ms / 1000
        self._ao_terminar = ao_terminar
        self._posicao = 0
        self._fonte: int | None = None
        self._cancelado = False

    @property
    def pendente(self) -> bool:
        return not self._cancelado and self._posicao < len(self._itens)

    def iniciar(self) -> "EmPedacos":
        self._fatia(garantir=self._minimo)
        if self.pendente:
            self._fonte = GLib.idle_add(self._continuar)
        return self

    def cancelar(self) -> None:
        self._cancelado = True
        if self._fonte is not None:
            GLib.source_remove(self._fonte)
            self._fonte = None

    def terminar_agora(self) -> None:
        """Faz o que falta de uma vez (usado quando o resto precisa existir já)."""
        if self._fonte is not None:
            GLib.source_remove(self._fonte)
            self._fonte = None
        self._fatia(garantir=len(self._itens))

    def _continuar(self) -> bool:
        self._fatia(garantir=1)
        if self.pendente:
            return True
        self._fonte = None
        return False

    def _fatia(self, garantir: int) -> None:
        if self._cancelado:
            return
        inicio = time.perf_counter()
        feitos = 0
        while self._posicao < len(self._itens):
            if feitos >= garantir and time.perf_counter() - inicio >= self._orcamento:
                break
            item = self._itens[self._posicao]
            self._posicao += 1                  # avança antes: um item que falha não prende a fila
            feitos += 1
            try:
                self._fazer(item)
            except Exception:
                log.exception("não consegui montar um item da lista (%r); sigo com os outros", item)
        if self._posicao >= len(self._itens) and self._ao_terminar is not None:
            terminar, self._ao_terminar = self._ao_terminar, None
            terminar()


def texto_de(etiqueta: Gtk.Label, texto: str) -> None:
    """Muda o texto de um rótulo só se for diferente (cada mudança custa um redesenho)."""
    if etiqueta.get_text() != texto:
        etiqueta.set_text(texto)


def definir_texto_do_botao(botao_: Gtk.Button, texto: str) -> None:
    """Muda o texto de um botão feito por `botao()` (o rótulo é o último item da caixa interna)."""
    texto_de(botao_.get_child().get_children()[-1], texto)


def classe(widget: Gtk.Widget, nome: str, ligada: bool) -> None:
    """Liga ou desliga uma classe de estilo, só se mudou (mexer no estilo à toa invalida o desenho)."""
    contexto = widget.get_style_context()
    if contexto.has_class(nome) != ligada:
        (contexto.add_class if ligada else contexto.remove_class)(nome)


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


class Mosaico(Gtk.DrawingArea):
    """Capa de disco montado: 2x2 quadrados com as cores dos discos de onde vêm as faixas."""

    def __init__(self, cores: list[str], lado: int = LADO_DA_CAPA):
        super().__init__()
        self.lado = lado
        self.cores = cores or ["#444444"]
        self.set_size_request(lado, lado)
        self.set_halign(Gtk.Align.CENTER)
        self.get_style_context().add_class("moa-capa")
        self.connect("draw", self._desenhar)

    def _desenhar(self, _area, cr) -> bool:
        metade = self.lado / 2
        for i in range(4):
            cor = self.cores[i % len(self.cores)]
            cr.set_source_rgb(*(int(cor[k:k + 2], 16) / 255 for k in (1, 3, 5)))
            cr.rectangle((i % 2) * metade, (i // 2) * metade, metade, metade)
            cr.fill()
        if self.lado >= 120:                        # a etiqueta "Montado" só cabe nas capas grandes
            cr.set_source_rgb(0.12, 0.1, 0.07)
            cr.rectangle(0, self.lado - 30, self.lado, 30)
            cr.fill()
            cr.set_source_rgb(1, 1, 1)
            layout = PangoCairo.create_layout(cr)
            fonte = Pango.FontDescription("Sans Bold")
            fonte.set_absolute_size(20 * Pango.SCALE)
            layout.set_font_description(fonte)
            layout.set_text("Montado", -1)
            cr.move_to(8, self.lado - 28)
            PangoCairo.show_layout(cr, layout)
        return False


def capa_do_disco(contexto, disco, lado: int = LADO_DA_CAPA) -> Gtk.Widget:
    """A capa certa para o disco: miniatura/substituta (disco) ou mosaico (disco montado)."""
    if getattr(disco, "eh_montado", False):
        cores = []
        for faixa in disco.tracks:
            origem = contexto.disco_de_origem(faixa)
            if origem is not None:
                cor = substitute_cover(origem).background
                if cor not in cores:
                    cores.append(cor)
        return Mosaico(cores, lado)
    return Capa(disco, contexto.miniaturas.get(disco.id), lado)


def aviso(texto: str, ao_desfazer=None, rotulo_do_botao: str = "Desfazer") -> Gtk.Widget:
    """Faixa de aviso calmo. Fica até a próxima ação do usuário."""
    caixa = caixa_h(14)
    caixa.get_style_context().add_class("moa-aviso")
    caixa.pack_start(rotulo(texto), True, True, 0)
    if ao_desfazer is not None:
        caixa.pack_start(botao(rotulo_do_botao, ao_clicar=ao_desfazer), False, False, 0)
    caixa.set_margin_bottom(14)
    return caixa
