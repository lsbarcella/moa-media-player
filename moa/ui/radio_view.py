# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tela "Tocando agora": o rádio antigo, com visor que fala.

Estado em três canais ao mesmo tempo (lâmpada, palavra e forma/cor do botão),
para ninguém depender só da cor. Desenho aprovado em `docs/preview/moa-preview.html`.
"""

from types import SimpleNamespace

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.contexto import Contexto  # noqa: E402
from moa.core.player import DEGRAU_MAXIMO  # noqa: E402
from moa.ui.widgets import classe, definir_texto_do_botao, texto_de, aviso, capa_do_disco, botao, caixa_h, caixa_v, icone, limpar, rotulo  # noqa: E402

LARGURA_PARA_EMPILHAR = 900


class RadioView:
    def __init__(self, contexto: Contexto):
        self.ctx = contexto
        self.raiz = caixa_v(0)
        self.raiz.set_border_width(24)
        # Peças fixas: o aviso em cima e, embaixo, o painel do rádio e o lugar da lista.
        self.topo = caixa_v(0)
        self.quadro = Gtk.Box(spacing=24)
        self.painel = caixa_v(0)
        self.lugar_da_lista = caixa_v(0)
        self.quadro.pack_start(self.painel, False, False, 0)
        self.quadro.pack_start(self.lugar_da_lista, True, True, 0)
        self.raiz.pack_start(self.topo, False, False, 0)
        self.raiz.pack_start(self.quadro, True, True, 0)
        self._p: SimpleNamespace | None = None          # os widgets do painel do rádio
        self._chave_do_topo: tuple | None = None
        self._foco_pendente = False
        self.botao_principal: Gtk.Widget | None = None
        self.rotulo_do_tempo: Gtk.Label | None = None
        # O botão "+" de cada música abre o painel "Em qual disco?".
        self.ao_pedir_outro_disco = self._pedir_outro_disco
        self._empilhado: bool | None = None
        # A lista de músicas pode ter centenas de linhas. Ela só é refeita quando algo que
        # aparece nela muda; mexer no volume, por exemplo, não a toca.
        self._lista: Gtk.Widget | None = None
        self._chave_da_lista: tuple | None = None      # o que, se mudar, exige refazer tudo
        self._marca: tuple[int, bool] | None = None     # (faixa atual, tocando): muda em lugar só
        self._linhas: list[tuple[Gtk.Widget, Gtk.Box]] = []     # (moldura, caixa dos nomes) de cada música
        self._nota: Gtk.Label | None = None             # "Tocando agora" / "Parado aqui"
        contexto.ao_mudar_a_colecao(self._esquecer_a_lista)
        self.raiz.connect("size-allocate", self._ao_mudar_de_tamanho)
        self.atualizar()

    def _deve_empilhar(self) -> bool:
        grande = self.ctx.preferencias.config.letra != "normal"
        return grande or self.raiz.get_allocated_width() < LARGURA_PARA_EMPILHAR

    def _ao_mudar_de_tamanho(self, *_args) -> None:
        if self._deve_empilhar() != self._empilhado:
            self.atualizar()

    # -- desenho -----------------------------------------------------------------------

    def _esquecer_a_lista(self) -> None:
        self._chave_da_lista = None

    def _chave_da_lista_atual(self) -> tuple | None:
        radio = self.ctx.radio
        if not radio.tem_disco:
            return None
        return (radio.disco.id, radio.disco.tracks, self.ctx.session.aviso)

    def _marca_atual(self) -> tuple[int, bool]:
        return (self.ctx.player.indice, self.ctx.radio.tocando)

    def atualizar(self) -> None:
        """Refaz só o que mudou. A lista de músicas NUNCA troca de pai: mudar um widget de pai
        desfaz e refaz por dentro todas as linhas (centenas), e isso era a travada."""
        ctx = self.ctx
        visor = ctx.radio.visor()
        a = ctx.session.aviso
        aviso_do_topo = a if (a is not None and a.ancora is None) else None   # com âncora fica na linha da música
        chave_do_topo = (aviso_do_topo, visor is None)
        if chave_do_topo != self._chave_do_topo:
            self._chave_do_topo = chave_do_topo
            limpar(self.topo)
            if aviso_do_topo is not None:
                self.topo.pack_start(aviso(aviso_do_topo.texto,
                                           ctx.session.desfazer if aviso_do_topo.desfazer else None,
                                           aviso_do_topo.rotulo_do_desfazer), False, False, 0)
            if visor is None:
                self.topo.pack_start(rotulo("Nenhum disco no rádio. Pegue um disco na estante."),
                                     False, False, 0)
            self.topo.show_all()
        if visor is None:
            self._lista = None
            self._chave_da_lista = None
            self._p = None
            self.botao_principal = None
            self.rotulo_do_tempo = None
            limpar(self.lugar_da_lista)
            limpar(self.painel)
            return

        chave = self._chave_da_lista_atual()
        reaproveitar = self._lista is not None and chave == self._chave_da_lista
        self._empilhado = self._deve_empilhar()
        self.quadro.set_orientation(Gtk.Orientation.VERTICAL if self._empilhado
                                    else Gtk.Orientation.HORIZONTAL)
        if self._p is None:
            self._construir_painel(visor)
            self.painel.pack_start(self._p.corpo, False, False, 0)
            self.painel.show_all()
            self._foco_pendente = True
        else:
            self._atualizar_painel(visor)
        if reaproveitar:
            self._mover_a_marca()           # trocar de faixa ou pausar mexe em duas linhas só
        else:
            limpar(self.lugar_da_lista)
            self._lista = self._lista_de_musicas()
            self._chave_da_lista = chave
            self._marca = self._marca_atual()
            self.lugar_da_lista.pack_start(self._lista, True, True, 0)
            # Mostra as linhas uma vez e depois o `show_all` da janela passa a pular a lista.
            self._lista.show_all()
            self._lista.set_no_show_all(True)
        self.quadro.show()
        self.lugar_da_lista.show()

    # -- o painel do rádio: montado uma vez e atualizado no lugar ------------------------
    # Recriar o painel a cada clique obrigava o GTK a recalcular estilo, tamanho e desenho de
    # todos os botões (no notebook do usuário, ~190 ms só para mudar o volume). Agora só o que
    # mudou é mexido, e o GTK redesenha só essas partes.

    def _construir_painel(self, visor) -> None:
        p = SimpleNamespace()
        p.disco_id = self.ctx.radio.disco.id
        p.luz = None
        corpo = caixa_v(14)
        corpo.get_style_context().add_class("moa-radio")
        corpo.set_size_request(420, -1)
        p.corpo = corpo

        # lâmpada + palavra
        estado = caixa_h(10)
        p.lampada = Gtk.Box()
        p.lampada.get_style_context().add_class("moa-lampada")
        p.lampada.set_valign(Gtk.Align.CENTER)
        estado.pack_start(p.lampada, False, False, 0)
        p.palavra = rotulo("", "moa-forte", quebrar=False)
        estado.pack_start(p.palavra, False, False, 0)
        corpo.pack_start(estado, False, False, 0)

        # visor
        p.moldura = caixa_h(14)
        p.moldura.get_style_context().add_class("moa-visor")
        p.capa = capa_do_disco(self.ctx, self.ctx.radio.disco, 120)
        p.moldura.pack_start(p.capa, False, False, 0)
        texto = caixa_v(4)
        p.linha_de_estado = rotulo("", "moa-forte")
        p.titulo = rotulo("", "moa-grande")
        p.disco = rotulo("")
        p.faixa = rotulo("")
        p.tempo = rotulo("")
        p.nota = rotulo("", "moa-nota-visor")
        p.nota.set_no_show_all(True)            # só aparece quando há o que dizer
        for etiqueta in (p.linha_de_estado, p.titulo, p.disco, p.faixa, p.tempo, p.nota):
            texto.pack_start(etiqueta, False, False, 0)
        p.moldura.pack_start(texto, True, True, 0)
        corpo.pack_start(p.moldura, False, False, 0)
        self.rotulo_do_tempo = p.tempo

        # botões: anterior / tocar-pausar / próxima (o do meio troca quando muda o estado)
        p.controles = Gtk.Grid(column_spacing=10, column_homogeneous=False)
        corpo.pack_start(p.controles, False, False, 0)

        # volume em degraus
        volume = caixa_v(8)
        volume.get_style_context().add_class("moa-volume")
        linha = caixa_h(8)
        p.menos = botao("Mais baixo", ao_clicar=self._volume_menos)
        p.mais = botao("Mais alto", ao_clicar=self._volume_mais)
        barras = caixa_h(4)
        barras.set_halign(Gtk.Align.CENTER)
        barras.set_valign(Gtk.Align.CENTER)
        p.barras = []
        for _ in range(DEGRAU_MAXIMO):
            barra = Gtk.Box()
            barra.get_style_context().add_class("moa-barra")
            barras.pack_start(barra, False, False, 0)
            p.barras.append(barra)
        linha.pack_start(p.menos, True, True, 0)
        linha.pack_start(barras, False, False, 0)
        linha.pack_start(p.mais, True, True, 0)
        volume.pack_start(linha, False, False, 0)
        legenda = caixa_h(8)
        legenda.set_halign(Gtk.Align.CENTER)
        legenda.pack_start(icone("volume", "#FFFFFF", "#2B2118"), False, False, 0)
        p.legenda = rotulo("", "moa-forte", centro=True)
        legenda.pack_start(p.legenda, False, False, 0)
        volume.pack_start(legenda, False, False, 0)
        corpo.pack_start(volume, False, False, 0)

        # "Voz mais clara"
        p.clara = botao("Voz mais clara: desligada", "moa-clara-desligada", ao_clicar=self._alternar_voz)
        corpo.pack_start(p.clara, False, False, 0)

        corpo.pack_start(botao("Guardar o disco na estante e parar", ao_clicar=self._guardar, icone_nome="disco"),
                         False, False, 0)
        self._p = p
        self._atualizar_painel(visor)

    def _atualizar_painel(self, visor) -> None:
        p = self._p
        radio = self.ctx.radio
        classe(p.lampada, "moa-acesa", visor.luz_acesa)
        texto_de(p.palavra, visor.palavra)
        if radio.disco.id != p.disco_id:                 # outro disco: troca só a capa
            p.moldura.remove(p.capa)
            p.capa = capa_do_disco(self.ctx, radio.disco, 120)
            p.moldura.pack_start(p.capa, False, False, 0)
            p.moldura.reorder_child(p.capa, 0)
            p.capa.show_all()
            p.disco_id = radio.disco.id
        texto_de(p.linha_de_estado, visor.linha_de_estado)
        texto_de(p.titulo, visor.titulo)
        texto_de(p.disco, f"Disco: {visor.disco}")
        texto_de(p.faixa, visor.faixa)
        texto_de(p.tempo, visor.tempo)
        texto_de(p.nota, visor.nota or "")
        p.nota.set_visible(bool(visor.nota))
        if p.luz != visor.luz_acesa:
            self._montar_controles(visor.luz_acesa)

        degrau = self.ctx.player.degrau_de_volume
        definir_texto_do_botao(p.menos, "No mínimo" if degrau <= 0 else "Mais baixo")
        definir_texto_do_botao(p.mais, "No máximo" if degrau >= DEGRAU_MAXIMO else "Mais alto")
        classe(p.menos, "moa-inativo", degrau <= 0)
        classe(p.mais, "moa-inativo", degrau >= DEGRAU_MAXIMO)
        for k, barra in enumerate(p.barras):
            classe(barra, "moa-acesa", k < degrau)
        texto_de(p.legenda, f"Volume: {degrau} de {DEGRAU_MAXIMO}")

        ligada = self.ctx.player.voz_mais_clara
        definir_texto_do_botao(p.clara, f"Voz mais clara: {'ligada' if ligada else 'desligada'}")
        classe(p.clara, "moa-clara-ligada", ligada)
        classe(p.clara, "moa-clara-desligada", not ligada)

    def _montar_controles(self, tocando: bool) -> None:
        """Anterior / Tocar ou Pausar / Próxima. Só é refeito quando troca Tocar por Pausar."""
        p = self._p
        limpar(p.controles)
        anterior = botao("Anterior", ao_clicar=self._anterior, icone_nome="anterior")
        if tocando:
            principal = botao("Pausar", "moa-pausar", ao_clicar=self._alternar, icone_nome="pausar")
        else:
            principal = botao("Tocar", "moa-tocar", ao_clicar=self._alternar, icone_nome="tocar")
        proxima = botao("Próxima", ao_clicar=self._proxima, icone_nome="proxima")
        for coluna, (widget, largura) in enumerate(((anterior, 1), (principal, 2), (proxima, 1))):
            widget.set_hexpand(True)
            p.controles.attach(widget, coluna * 2, 0, largura, 1)
        p.controles.show_all()
        p.luz = tocando
        self.botao_principal = principal
        self._foco_pendente = True

    def _lista_de_musicas(self) -> Gtk.Widget:
        radio = self.ctx.radio
        disco = radio.disco
        atual = self.ctx.player.indice
        coluna = caixa_v(8)
        coluna.pack_start(rotulo("Músicas deste disco", "moa-grande"), False, False, 0)
        self._linhas = []
        self._nota = None
        for i, musica in enumerate(disco.tracks):
            moldura = caixa_v(6)
            moldura.get_style_context().add_class("moa-linha")
            linha = caixa_h(8)
            if i == atual:
                moldura.get_style_context().add_class("moa-agora")
            conteudo = caixa_h(12)
            conteudo.pack_start(rotulo(str(i + 1), "moa-forte", quebrar=False), False, False, 0)
            nomes = caixa_v(0)
            nomes.set_valign(Gtk.Align.CENTER)
            nomes.pack_start(rotulo(musica.title, xalign=0.0), False, False, 0)
            if getattr(disco, "eh_montado", False):
                origem = self.ctx.disco_de_origem(musica)
                if origem is not None:
                    nomes.pack_start(rotulo(f"do disco {origem.title}", "moa-nota"), False, False, 0)
            if i == atual:
                self._nota = rotulo(self._texto_da_nota(radio.tocando), "moa-nota")
                nomes.pack_start(self._nota, False, False, 0)
            self._linhas.append((moldura, nomes))
            conteudo.pack_start(nomes, True, True, 0)
            b = Gtk.Button()
            b.add(conteudo)
            b.get_style_context().add_class("moa-faixa")
            b.connect("clicked", lambda _b, k=i: self._tocar_faixa(k))
            linha.pack_start(b, True, True, 0)
            if self.ao_pedir_outro_disco is not None:
                linha.pack_start(
                    botao("Colocar em outro disco", icone_nome="mais",
                          ao_clicar=lambda k=i: self.ao_pedir_outro_disco(k)),
                    False, False, 0)
            moldura.pack_start(linha, False, False, 0)
            a = self.ctx.session.aviso
            if a is not None and a.ancora == str(musica.path):
                moldura.pack_start(aviso(a.texto, self.ctx.session.desfazer if a.desfazer else None, a.rotulo_do_desfazer),
                                   False, False, 0)
            coluna.pack_start(moldura, False, False, 0)
        coluna.pack_start(botao("Mexer neste disco", ao_clicar=self._mexer_no_disco),
                          False, False, 8)
        return coluna

    @staticmethod
    def _texto_da_nota(tocando: bool) -> str:
        return "Tocando agora" if tocando else "Parado aqui"

    def _mover_a_marca(self) -> None:
        """Passa o "Tocando agora" para a faixa certa, sem refazer a lista (podem ser centenas)."""
        marca = self._marca_atual()
        if marca == self._marca:
            return
        antes, _ = self._marca or (None, None)
        indice, tocando = marca
        if indice != antes and self._linhas:
            if self._nota is not None:
                self._nota.get_parent().remove(self._nota)
                self._nota = None
            if antes is not None and antes < len(self._linhas):
                self._linhas[antes][0].get_style_context().remove_class("moa-agora")
            if indice < len(self._linhas):
                moldura, nomes = self._linhas[indice]
                moldura.get_style_context().add_class("moa-agora")
                self._nota = rotulo(self._texto_da_nota(tocando), "moa-nota")
                nomes.pack_start(self._nota, False, False, 0)
                self._nota.show()
        elif self._nota is not None:
            self._nota.set_text(self._texto_da_nota(tocando))
        self._marca = marca

    def _mexer_no_disco(self) -> None:
        from moa.core.session import Tela
        self.ctx.session.acao()
        self.ctx.session.disco_aberto_id = self.ctx.radio.disco.id
        self.ctx.session.ir_para(Tela.EDITAR)

    def _pedir_outro_disco(self, indice: int) -> None:
        self.ctx.session.acao()
        self.ctx.session.abrir_painel_mais(self.ctx.radio.disco.tracks[indice])

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

    def ao_entrar(self) -> None:
        self._foco_pendente = True          # ao chegar nesta tela, o foco vai para Tocar/Pausar

    def foco_inicial(self) -> Gtk.Widget | None:
        if not self._foco_pendente:
            return None                     # só um valor mudou: o foco fica onde o usuário o deixou
        self._foco_pendente = False
        return self.botao_principal
