# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tela "Configurações": tamanho da letra e cores (ADR-0006).

O próprio usuário abre esta tela por um botão com texto sempre visível no
cabeçalho. Cada escolha vale na hora e fica gravada. A escolha atual mostra "✓"
e uma borda grossa (nunca só a cor).
"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.config import LETRAS, PALETAS  # noqa: E402
from moa.core.contexto import Contexto  # noqa: E402
from moa.ui.theme import ROTULOS_DAS_LETRAS, ROTULOS_DAS_PALETAS, amostra  # noqa: E402
from moa.ui.widgets import aviso, caixa_h, caixa_v, limpar, rotulo  # noqa: E402


def _quadradinho(cor: str) -> Gtk.DrawingArea:
    """Uma amostra de cor de 26 px, com borda escura."""
    area = Gtk.DrawingArea()
    area.set_size_request(26, 26)

    def desenhar(_a, cr):
        r, g, b = (int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5))
        cr.set_source_rgb(r, g, b)
        cr.rectangle(1, 1, 24, 24)
        cr.fill_preserve()
        cr.set_source_rgb(0.12, 0.1, 0.07)
        cr.set_line_width(2)
        cr.stroke()
        return False

    area.connect("draw", desenhar)
    return area


class SettingsView:
    def __init__(self, contexto: Contexto):
        self.ctx = contexto
        self.raiz = caixa_v(16)
        self.raiz.set_border_width(24)
        self.primeiro_botao: Gtk.Widget | None = None
        self.atualizar()

    def atualizar(self) -> None:
        config = self.ctx.preferencias.config
        limpar(self.raiz)
        self.primeiro_botao = None
        if self.ctx.session.aviso is not None:
            a = self.ctx.session.aviso
            self.raiz.pack_start(aviso(a.texto), False, False, 0)

        colunas = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL if config.letra == "normal"
                          else Gtk.Orientation.VERTICAL, spacing=22)
        colunas.set_homogeneous(config.letra == "normal")

        letra = self._cartao("Tamanho da letra")
        for chave in LETRAS:
            letra.pack_start(self._opcao(ROTULOS_DAS_LETRAS[chave], chave == config.letra,
                                         lambda c=chave: self._mudar(letra=c)), False, False, 0)
        letra.pack_start(rotulo("Exemplo: Tocando agora, faixa 3 de 8", "moa-exemplo"),
                         False, False, 0)
        colunas.pack_start(letra, True, True, 0)

        cores = self._cartao("Cores")
        cores.pack_start(rotulo("Escolha o que fica mais fácil de ver. Isso não muda o som."),
                         False, False, 0)
        for chave in PALETAS:
            cores.pack_start(self._opcao(ROTULOS_DAS_PALETAS[chave], chave == config.paleta,
                                         lambda c=chave: self._mudar(paleta=c),
                                         amostras=amostra(chave)), False, False, 0)
        cores.pack_start(rotulo("O Moa nunca usa só a cor para dizer algo: sempre há também "
                                "texto e formas.", "moa-nota"), False, False, 0)
        colunas.pack_start(cores, True, True, 0)
        self.raiz.pack_start(colunas, False, False, 0)
        self.raiz.show_all()

    def _cartao(self, titulo: str) -> Gtk.Box:
        cartao = caixa_v(10)
        cartao.get_style_context().add_class("moa-cartao")
        cartao.pack_start(rotulo(titulo, "moa-grande"), False, False, 0)
        return cartao

    def _opcao(self, texto: str, escolhida: bool, ao_clicar, amostras=()) -> Gtk.Button:
        b = Gtk.Button()
        linha = caixa_h(12)
        linha.pack_start(rotulo("✓" if escolhida else " ", "moa-forte", quebrar=False),
                         False, False, 0)
        linha.pack_start(rotulo(texto, "moa-forte"), True, True, 0)
        if amostras:
            quadros = caixa_h(6)
            for cor in amostras:
                quadros.pack_start(_quadradinho(cor), False, False, 0)
            linha.pack_end(quadros, False, False, 0)
        b.add(linha)
        b.get_style_context().add_class("moa-opcao")
        if escolhida:
            b.get_style_context().add_class("moa-escolhida")
        b.connect("clicked", lambda _b: ao_clicar())
        if self.primeiro_botao is None:
            self.primeiro_botao = b
        return b

    def _mudar(self, **mudancas) -> None:
        self.ctx.session.acao()
        self.ctx.preferencias.mudar(**mudancas)

    def foco_inicial(self) -> Gtk.Widget | None:
        return self.primeiro_botao
