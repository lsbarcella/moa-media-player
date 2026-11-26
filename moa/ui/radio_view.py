# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tela "Tocando agora": o rádio antigo, com visor que fala.

Estado em três canais ao mesmo tempo (lâmpada, palavra e forma/cor do botão),
para ninguém depender só da cor. Desenho aprovado em `docs/preview/moa-preview.html`.
"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.contexto import Contexto  # noqa: E402
from moa.core.player import DEGRAU_MAXIMO  # noqa: E402
from moa.ui.widgets import Capa, aviso, botao, caixa_h, caixa_v, limpar, rotulo  # noqa: E402

LARGURA_PARA_EMPILHAR = 900


class RadioView:
    def __init__(self, contexto: Contexto):
        self.ctx = contexto
        self.raiz = caixa_v(0)
        self.raiz.set_border_width(24)
        self.botao_principal: Gtk.Widget | None = None
        self.rotulo_do_tempo: Gtk.Label | None = None
        # A tela de "montar disco" (U8) liga o botão "+" de cada música aqui.
        self.ao_pedir_outro_disco = None
        self._empilhado: bool | None = None
        self.raiz.connect("size-allocate", self._ao_mudar_de_tamanho)
        self.atualizar()

    def _deve_empilhar(self) -> bool:
        grande = self.ctx.preferencias.config.letra != "normal"
        return grande or self.raiz.get_allocated_width() < LARGURA_PARA_EMPILHAR

    def _ao_mudar_de_tamanho(self, *_args) -> None:
        if self._deve_empilhar() != self._empilhado:
            self.atualizar()

    # -- desenho -----------------------------------------------------------------------

    def atualizar(self) -> None:
        ctx = self.ctx
        limpar(self.raiz)
        self.botao_principal = None
        self.rotulo_do_tempo = None
        visor = ctx.radio.visor()
        if ctx.session.aviso is not None:
            a = ctx.session.aviso
            self.raiz.pack_start(aviso(a.texto, ctx.session.desfazer if a.desfazer else None),
                                 False, False, 0)
        if visor is None:
            self.raiz.pack_start(rotulo("Nenhum disco no rádio. Pegue um disco na estante."),
                                 False, False, 0)
            self.raiz.show_all()
            return
        self._empilhado = self._deve_empilhar()
        quadro = Gtk.Box(orientation=Gtk.Orientation.VERTICAL if self._empilhado
                         else Gtk.Orientation.HORIZONTAL, spacing=24)
        quadro.pack_start(self._radio(visor), False, False, 0)
        quadro.pack_start(self._lista_de_musicas(), True, True, 0)
        self.raiz.pack_start(quadro, True, True, 0)
        self.raiz.show_all()

    def _radio(self, visor) -> Gtk.Widget:
        radio = self.ctx.radio
        corpo = caixa_v(14)
        corpo.get_style_context().add_class("moa-radio")
        corpo.set_size_request(420, -1)

        # lâmpada + palavra
        estado = caixa_h(10)
        lampada = Gtk.Box()
        lampada.get_style_context().add_class("moa-lampada")
        if visor.luz_acesa:
            lampada.get_style_context().add_class("moa-acesa")
        lampada.set_valign(Gtk.Align.CENTER)
        estado.pack_start(lampada, False, False, 0)
        estado.pack_start(rotulo(visor.palavra, "moa-forte", quebrar=False), False, False, 0)
        corpo.pack_start(estado, False, False, 0)

        # visor
        moldura = caixa_h(14)
        moldura.get_style_context().add_class("moa-visor")
        disco = radio.disco
        moldura.pack_start(Capa(disco, self.ctx.miniaturas.get(disco.id), 120),
                           False, False, 0)
        texto = caixa_v(4)
        texto.pack_start(rotulo(visor.linha_de_estado, "moa-forte"), False, False, 0)
        texto.pack_start(rotulo(visor.titulo, "moa-grande"), False, False, 0)
        texto.pack_start(rotulo(f"Disco: {visor.disco}"), False, False, 0)
        texto.pack_start(rotulo(visor.faixa), False, False, 0)
        self.rotulo_do_tempo = rotulo(visor.tempo)
        texto.pack_start(self.rotulo_do_tempo, False, False, 0)
        if visor.nota:
            texto.pack_start(rotulo(visor.nota, "moa-nota-visor"), False, False, 0)
        moldura.pack_start(texto, True, True, 0)
        corpo.pack_start(moldura, False, False, 0)

        # botões: anterior / tocar-pausar / próxima
        controles = Gtk.Grid(column_spacing=10, column_homogeneous=False)
        anterior = botao("Anterior", ao_clicar=self._anterior)
        if visor.luz_acesa:
            principal = botao("Pausar", "moa-pausar", ao_clicar=self._alternar)
        else:
            principal = botao("Tocar", "moa-tocar", ao_clicar=self._alternar)
        proxima = botao("Próxima", ao_clicar=self._proxima)
        for coluna, (widget, largura) in enumerate(((anterior, 1), (principal, 2), (proxima, 1))):
            widget.set_hexpand(True)
            controles.attach(widget, coluna * 2, 0, largura, 1)
        corpo.pack_start(controles, False, False, 0)
        self.botao_principal = principal

        # volume em degraus
        degrau = self.ctx.player.degrau_de_volume
        volume = caixa_v(8)
        volume.get_style_context().add_class("moa-volume")
        linha = caixa_h(8)
        menos = botao("No mínimo" if degrau <= 0 else "Mais baixo",
                      ao_clicar=self._volume_menos)
        mais = botao("No máximo" if degrau >= DEGRAU_MAXIMO else "Mais alto",
                     ao_clicar=self._volume_mais)
        if degrau <= 0:
            menos.get_style_context().add_class("moa-inativo")
        if degrau >= DEGRAU_MAXIMO:
            mais.get_style_context().add_class("moa-inativo")
        barras = caixa_h(4)
        barras.set_halign(Gtk.Align.CENTER)
        barras.set_valign(Gtk.Align.CENTER)
        for k in range(DEGRAU_MAXIMO):
            barra = Gtk.Box()
            barra.get_style_context().add_class("moa-barra")
            if k < degrau:
                barra.get_style_context().add_class("moa-acesa")
            barras.pack_start(barra, False, False, 0)
        linha.pack_start(menos, True, True, 0)
        linha.pack_start(barras, False, False, 0)
        linha.pack_start(mais, True, True, 0)
        volume.pack_start(linha, False, False, 0)
        volume.pack_start(rotulo(f"Volume: {degrau} de {DEGRAU_MAXIMO}", "moa-forte", centro=True),
                          False, False, 0)
        corpo.pack_start(volume, False, False, 0)

        # "Voz mais clara"
        ligada = self.ctx.player.voz_mais_clara
        clara = botao(f"Voz mais clara: {'ligada' if ligada else 'desligada'}",
                      "moa-clara-ligada" if ligada else "moa-clara-desligada",
                      ao_clicar=self._alternar_voz)
        corpo.pack_start(clara, False, False, 0)

        corpo.pack_start(botao("Guardar o disco na estante e parar", ao_clicar=self._guardar),
                         False, False, 0)
        return corpo

    def _lista_de_musicas(self) -> Gtk.Widget:
        radio = self.ctx.radio
        disco = radio.disco
        atual = self.ctx.player.indice
        coluna = caixa_v(8)
        coluna.pack_start(rotulo("Músicas deste disco", "moa-grande"), False, False, 0)
        for i, musica in enumerate(disco.tracks):
            linha = caixa_h(8)
            linha.get_style_context().add_class("moa-linha")
            if i == atual:
                linha.get_style_context().add_class("moa-agora")
            conteudo = caixa_h(12)
            conteudo.pack_start(rotulo(str(i + 1), "moa-forte", quebrar=False), False, False, 0)
            nomes = caixa_v(0)
            nomes.set_valign(Gtk.Align.CENTER)
            nomes.pack_start(rotulo(musica.title, xalign=0.0), False, False, 0)
            if i == atual:
                nomes.pack_start(
                    rotulo("Tocando agora" if radio.tocando else "Parado aqui", "moa-nota"),
                    False, False, 0)
            conteudo.pack_start(nomes, True, True, 0)
            b = Gtk.Button()
            b.add(conteudo)
            b.get_style_context().add_class("moa-faixa")
            b.connect("clicked", lambda _b, k=i: self._tocar_faixa(k))
            linha.pack_start(b, True, True, 0)
            if self.ao_pedir_outro_disco is not None:
                linha.pack_start(
                    botao("＋ Colocar em outro disco",
                          ao_clicar=lambda k=i: self.ao_pedir_outro_disco(k)),
                    False, False, 0)
            coluna.pack_start(linha, False, False, 0)
        return coluna

    # -- tempo (chamado por um relógio da janela, sem redesenhar a tela) ------------------

    def atualizar_tempo(self) -> None:
        if self.rotulo_do_tempo is not None:
            self.rotulo_do_tempo.set_text(self.ctx.radio.texto_do_tempo())

    # -- ações ---------------------------------------------------------------------------------

    def _acao(self, funcao) -> None:
        self.ctx.session.acao()
        funcao()

    def _alternar(self) -> None:
        self._acao(self.ctx.radio.alternar)

    def _anterior(self) -> None:
        self._acao(self.ctx.radio.anterior)

    def _proxima(self) -> None:
        self._acao(self.ctx.radio.proxima)

    def _volume_mais(self) -> None:
        self._acao(self.ctx.radio.volume_mais)

    def _volume_menos(self) -> None:
        self._acao(self.ctx.radio.volume_menos)

    def _alternar_voz(self) -> None:
        self._acao(self.ctx.radio.alternar_voz_mais_clara)

    def _tocar_faixa(self, indice: int) -> None:
        self._acao(lambda: self.ctx.radio.tocar_faixa(indice))

    def _guardar(self) -> None:
        from moa.core.session import Tela
        self.ctx.session.acao()
        self.ctx.radio.guardar_o_disco_e_parar()
        self.ctx.session.ir_para(Tela.ESTANTE)

    def foco_inicial(self) -> Gtk.Widget | None:
        return self.botao_principal
