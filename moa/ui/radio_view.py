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
from moa.ui import ornamentos  # noqa: E402
from moa.ui.instrumentos import BotaoDeVolume, LinhaDeProgresso  # noqa: E402
from moa.ui.widgets import EmPedacos, classe, definir_estado_da_tecla, definir_texto_do_botao, tecla_travavel, texto_de, aviso, capa_do_disco, botao, botao_so_com_icone, definir_nome_da_tecla, caixa_h, caixa_v, icone, limpar, rotulo  # noqa: E402

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
        # Cada coluna tem a SUA rolagem (ADR-0028): lado a lado, o painel do rádio fica parado e só a
        # lista de músicas rola. Empilhadas, a tela inteira rola (rolagem externa, da janela) e as
        # colunas não rolam sozinhas. Nenhum widget troca de pai ao mudar de modo: só mudam as políticas.
        self.painel_rolagem = Gtk.ScrolledWindow()
        self.painel_rolagem.set_overlay_scrolling(False)
        self.painel_rolagem.add(self.painel)
        self.lista_rolagem = Gtk.ScrolledWindow()
        self.lista_rolagem.set_overlay_scrolling(False)
        self.lista_rolagem.add(self.lugar_da_lista)
        self._rolagem_externa: Gtk.ScrolledWindow | None = None     # a da janela; entregue por `registrar`
        self.quadro.pack_start(self.painel_rolagem, False, False, 0)
        self.quadro.pack_start(self.lista_rolagem, True, True, 0)
        self.raiz.pack_start(self.topo, False, False, 0)
        self.raiz.pack_start(self.quadro, True, True, 0)
        self._p: SimpleNamespace | None = None          # os widgets do painel do rádio
        self._chave_do_topo: tuple | None = None
        self._foco_pendente = False
        self.botao_principal: Gtk.Widget | None = None
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
        self._construtor_da_lista: EmPedacos | None = None
        contexto.ao_mudar_a_colecao(self._esquecer_a_lista)
        contexto.radio.ao_mudar(self._ao_mudar_o_radio)
        self.raiz.connect("size-allocate", self._ao_mudar_de_tamanho)
        self.atualizar()

    @property
    def rolagem_externa(self) -> Gtk.ScrolledWindow | None:
        return self._rolagem_externa

    @rolagem_externa.setter
    def rolagem_externa(self, rolagem: Gtk.ScrolledWindow) -> None:
        self._rolagem_externa = rolagem
        if self._empilhado is not None:
            self._aplicar_o_modo(self._empilhado)

    def _deve_empilhar(self) -> bool:
        so_a_maior = self.ctx.preferencias.config.letra == "maior"
        return so_a_maior or self.raiz.get_allocated_width() < LARGURA_PARA_EMPILHAR

    def _aplicar_o_modo(self, empilhado: bool) -> None:
        """Lado a lado: a janela não rola e cada coluna rola sozinha. Empilhado: o contrário."""
        self.quadro.set_orientation(Gtk.Orientation.VERTICAL if empilhado else Gtk.Orientation.HORIZONTAL)
        nunca, automatica = Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC
        if self._rolagem_externa is not None:
            self._rolagem_externa.set_policy(automatica if empilhado else nunca,
                                             automatica if empilhado else nunca)
        for coluna in (self.painel_rolagem, self.lista_rolagem):
            coluna.set_policy(nunca, nunca if empilhado else automatica)
            coluna.set_propagate_natural_height(empilhado)
        self.painel_rolagem.set_propagate_natural_width(True)

    def _ao_mudar_de_tamanho(self, *_args) -> None:
        if self._deve_empilhar() != self._empilhado:
            self.atualizar()

    # -- desenho -----------------------------------------------------------------------

    def _esquecer_a_lista(self) -> None:
        self._chave_da_lista = None

    def _ao_mudar_o_radio(self) -> None:
        """Sem disco no rádio, para de montar a lista do disco que saiu (mesmo com a tela escondida)."""
        if not self.ctx.radio.tem_disco and self._construtor_da_lista is not None:
            self._construtor_da_lista.cancelar()

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
            if self._construtor_da_lista is not None:
                self._construtor_da_lista.cancelar()
            self._lista = None
            self._chave_da_lista = None
            self._p = None
            self.botao_principal = None
            limpar(self.lugar_da_lista)
            limpar(self.painel)
            return

        chave = self._chave_da_lista_atual()
        reaproveitar = self._lista is not None and chave == self._chave_da_lista
        empilhado = self._deve_empilhar()
        if empilhado != self._empilhado:
            self._empilhado = empilhado
            self._aplicar_o_modo(empilhado)
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
        corpo = caixa_v(8)
        corpo.get_style_context().add_class("moa-radio")
        corpo.set_size_request(420, -1)
        p.corpo = corpo

        ornamentos.instalar_parafusos(corpo)

        p.lampada = Gtk.Box()                  # a lâmpada-piloto fica no visor, junto da frase do estado
        p.lampada.get_style_context().add_class("moa-lampada")
        p.lampada.set_valign(Gtk.Align.CENTER)

        # visor
        p.moldura = caixa_h(14)
        p.moldura.get_style_context().add_class("moa-visor")
        p.capa = capa_do_disco(self.ctx, self.ctx.radio.disco, 120)
        p.moldura.pack_start(p.capa, False, False, 0)
        texto = caixa_v(4)
        p.linha_de_estado = rotulo("", "moa-forte")
        p.titulo = rotulo("", "moa-grande")
        p.sobre = rotulo("")                       # "Artista · Álbum · Ano"
        p.faixa = rotulo("")                       # "Faixa 3 de 12"
        p.progresso = LinhaDeProgresso(self._buscar)
        p.nota = rotulo("", "moa-nota-visor")
        p.nota.set_no_show_all(True)            # só aparece quando há o que dizer
        estado = caixa_h(10)
        estado.pack_start(p.lampada, False, False, 0)
        estado.pack_start(p.linha_de_estado, True, True, 0)
        texto.pack_start(estado, False, False, 0)
        for etiqueta in (p.titulo, p.sobre, p.faixa, p.progresso, p.nota):
            texto.pack_start(etiqueta, False, False, 0)
        p.moldura.pack_start(texto, True, True, 0)
        corpo.pack_start(p.moldura, False, False, 0)

        # botões: anterior / tocar-pausar / próxima (o do meio troca quando muda o estado)
        p.controles = Gtk.Grid(column_spacing=10, column_homogeneous=False)
        metal = caixa_v(0)                      # moldura de metal escovado atrás das três teclas
        metal.get_style_context().add_class("moa-bandeja")
        metal.pack_start(p.controles, False, False, 0)
        corpo.pack_start(metal, False, False, 0)

        # volume em degraus
        volume = caixa_v(8)
        volume.get_style_context().add_class("moa-volume")
        linha = caixa_h(8)
        p.menos = botao_so_com_icone("volume_menos", "Mais baixo", ao_clicar=self._volume_menos)
        p.mais = botao_so_com_icone("volume_mais", "Mais alto", ao_clicar=self._volume_mais)
        p.botao_volume = BotaoDeVolume(DEGRAU_MAXIMO)     # só mostra; quem gira é "Mais baixo/Mais alto"
        p.botao_volume.set_halign(Gtk.Align.CENTER)
        p.botao_volume.set_valign(Gtk.Align.CENTER)
        for tecla in (p.menos, p.mais):
            tecla.set_size_request(120, -1)             # tecla só com símbolo: larga o bastante, sem esticar
        linha.set_halign(Gtk.Align.CENTER)
        linha.pack_start(p.menos, False, False, 0)
        linha.pack_start(p.botao_volume, False, False, 12)
        linha.pack_start(p.mais, False, False, 0)
        volume.pack_start(linha, False, False, 0)
        legenda = caixa_h(8)
        legenda.set_halign(Gtk.Align.CENTER)
        legenda.pack_start(icone("volume", "#FFFFFF", "#2B2118"), False, False, 0)
        p.legenda = rotulo("", "moa-forte", centro=True)
        legenda.pack_start(p.legenda, False, False, 0)
        volume.pack_start(legenda, False, False, 0)
        corpo.pack_start(volume, False, False, 0)

        # "Voz mais clara"
        p.clara = tecla_travavel("Voz mais clara: desligada", False, "moa-clara-desligada",
                                 ao_clicar=self._alternar_voz)
        corpo.pack_start(p.clara, False, False, 0)

        corpo.pack_start(botao("Guardar o disco na estante e parar", ao_clicar=self._guardar, icone_nome="disco"),
                         False, False, 0)
        pe = caixa_h(12)                        # no pé do aparelho: a grade do alto-falante e a plaquinha MOA
        grade = Gtk.Box()
        grade.get_style_context().add_class("moa-grade")
        pe.pack_start(grade, True, True, 0)
        placa = caixa_h(0)
        placa.get_style_context().add_class("moa-plaquinha")
        placa.pack_start(rotulo("MOA", quebrar=False), False, False, 0)
        placa.set_valign(Gtk.Align.CENTER)
        pe.pack_start(placa, False, False, 0)
        corpo.pack_start(pe, False, False, 0)
        self._p = p
        self._atualizar_painel(visor)

    def _atualizar_painel(self, visor) -> None:
        p = self._p
        radio = self.ctx.radio
        classe(p.lampada, "moa-acesa", visor.luz_acesa)
        if radio.disco.id != p.disco_id:                 # outro disco: troca só a capa
            p.moldura.remove(p.capa)
            p.capa = capa_do_disco(self.ctx, radio.disco, 120)
            p.moldura.pack_start(p.capa, False, False, 0)
            p.moldura.reorder_child(p.capa, 0)
            p.capa.show_all()
            p.disco_id = radio.disco.id
        texto_de(p.linha_de_estado, visor.linha_de_estado)
        texto_de(p.titulo, visor.titulo)
        texto_de(p.sobre, visor.sobre_o_disco)
        texto_de(p.faixa, visor.faixa)
        p.progresso.atualizar_do_radio(radio)
        texto_de(p.nota, visor.nota or "")
        p.nota.set_visible(bool(visor.nota))
        if p.luz != visor.luz_acesa:
            self._montar_controles(visor.luz_acesa)

        degrau = self.ctx.player.degrau_de_volume
        definir_nome_da_tecla(p.menos, "Volume no mínimo" if degrau <= 0 else "Mais baixo")
        definir_nome_da_tecla(p.mais, "Volume no máximo" if degrau >= DEGRAU_MAXIMO else "Mais alto")
        classe(p.menos, "moa-inativo", degrau <= 0)
        classe(p.mais, "moa-inativo", degrau >= DEGRAU_MAXIMO)
        p.botao_volume.definir_degrau(degrau)
        texto_de(p.legenda, f"Volume: {degrau} de {DEGRAU_MAXIMO}")

        ligada = self.ctx.player.voz_mais_clara
        definir_texto_do_botao(p.clara, f"Voz mais clara: {'ligada' if ligada else 'desligada'}")
        classe(p.clara, "moa-clara-ligada", ligada)
        classe(p.clara, "moa-clara-desligada", not ligada)
        definir_estado_da_tecla(p.clara, ligada)

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
        """A lista de músicas do disco. Discos grandes são montados em pedaços (`EmPedacos`): as
        primeiras linhas aparecem na hora e o resto vem em seguida, sem prender a tela."""
        if self._construtor_da_lista is not None:
            self._construtor_da_lista.cancelar()
        disco = self.ctx.radio.disco
        coluna = caixa_v(8)
        coluna.pack_start(rotulo("Músicas deste disco", "moa-grande"), False, False, 0)
        coluna.pack_end(botao("Mexer neste disco", ao_clicar=self._mexer_no_disco), False, False, 8)
        self._linhas = []
        self._nota = None

        def acrescentar(item) -> None:
            i, musica = item
            linha = self._linha_da_musica(i, musica, disco)
            coluna.pack_start(linha, False, False, 0)
            linha.show_all()

        self._construtor_da_lista = EmPedacos(enumerate(disco.tracks), acrescentar).iniciar()
        return coluna

    def _linha_da_musica(self, i: int, musica, disco) -> Gtk.Widget:
        radio = self.ctx.radio
        atual = self.ctx.player.indice          # lido na hora: a faixa pode ter mudado durante a montagem
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
        return moldura

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
        if self._p is not None:
            self._p.progresso.atualizar_do_radio(self.ctx.radio)

    def _buscar(self, fracao: float) -> None:
        self.ctx.session.acao()
        self.ctx.radio.buscar_fracao(fracao)

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
