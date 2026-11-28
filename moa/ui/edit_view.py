# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tela "Mexendo no disco": mudar o nome, trocar a capa ou tirar da estante.

Mostra uma prévia ao vivo de como o disco vai ficar. "Guardar" × "Deixar como
estava" são dois botões grandes; depois de guardar, o aviso oferece "Como era antes".
"Apagar de vez" NÃO existe aqui (só na Lixeira, ADR-0007).
"""

import logging
import sqlite3
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core import box  # noqa: E402
from moa.core.contexto import Contexto  # noqa: E402
from moa.core.covers import CoverChoice, cover_options, make_thumbnail  # noqa: E402
from moa.core.models import Album  # noqa: E402
from moa.core.session import Tela  # noqa: E402
from moa.ui.widgets import (Capa, aviso, botao, capa_do_disco, caixa_h, caixa_v,  # noqa: E402
                            limpar, rotulo)

log = logging.getLogger(__name__)

MSG_FALHA = "Não consegui guardar. Tente de novo."


class EditView:
    def __init__(self, contexto: Contexto):
        self.ctx = contexto
        self.raiz = caixa_v(0)
        self.raiz.set_border_width(24)
        self.disco = None
        self.nome = ""
        self.escolha: CoverChoice | None = None       # None: não mexer na capa
        self.opcoes: list[tuple[str, CoverChoice, Path | None]] = []
        self.campo_do_nome: Gtk.Entry | None = None
        self._construido = False
        self._area_do_aviso: Gtk.Box | None = None
        self._area_da_previa: Gtk.Box | None = None
        self._area_da_galeria: Gtk.Box | None = None
        self._botao_do_foco: Gtk.Widget | None = None
        self.atualizar()

    # -- ciclo de vida ---------------------------------------------------------------------

    def ao_entrar(self) -> None:
        self._construido = False

    def atualizar(self) -> None:
        if not self._construido:
            self._construir()
        self._atualizar_aviso()

    def foco_inicial(self) -> Gtk.Widget | None:
        return self.campo_do_nome

    def _construir(self) -> None:
        ctx = self.ctx
        limpar(self.raiz)
        self.disco = ctx.disco(ctx.session.disco_aberto_id)
        self._construido = True
        if self.disco is None:
            self.raiz.pack_start(rotulo("Escolha um disco para mexer nele."), False, False, 0)
            self.campo_do_nome = None
            self.raiz.show_all()
            return
        self.nome = self.disco.title
        self.escolha = None
        self.opcoes = self._opcoes_de_capa()
        self._area_do_aviso = caixa_v(0)
        self.raiz.pack_start(self._area_do_aviso, False, False, 0)

        quadro = Gtk.Box(orientation=Gtk.Orientation.VERTICAL
                         if ctx.preferencias.config.letra != "normal"
                         else Gtk.Orientation.HORIZONTAL, spacing=26)
        self._area_da_previa = caixa_v(8)
        self._area_da_previa.get_style_context().add_class("moa-cartao")
        quadro.pack_start(self._area_da_previa, False, False, 0)

        direita = caixa_v(10)
        direita.pack_start(rotulo("Nome do disco", "moa-forte"), False, False, 0)
        self.campo_do_nome = Gtk.Entry()
        self.campo_do_nome.set_text(self.nome)
        self.campo_do_nome.connect("changed", self._ao_digitar_o_nome)
        direita.pack_start(self.campo_do_nome, False, False, 0)

        if isinstance(self.disco, Album):
            direita.pack_start(rotulo("Trocar a capa", "moa-forte"), False, False, 0)
            self._area_da_galeria = Gtk.FlowBox()
            self._area_da_galeria.set_selection_mode(Gtk.SelectionMode.NONE)
            self._area_da_galeria.set_activate_on_single_click(True)
            self._area_da_galeria.set_column_spacing(12)
            self._area_da_galeria.set_row_spacing(12)
            direita.pack_start(self._area_da_galeria, False, False, 0)
        else:
            direita.pack_start(rotulo("A capa deste disco montado é feita com as capas dos "
                                      "outros discos.", "moa-nota"), False, False, 0)

        botoes = caixa_h(12)
        botoes.pack_start(botao("Guardar", "moa-pri", "moa-grande", ao_clicar=self._guardar),
                          False, False, 0)
        botoes.pack_start(botao("Deixar como estava", "moa-grande", ao_clicar=self._cancelar),
                          False, False, 0)
        direita.pack_start(botoes, False, False, 0)

        saida = caixa_v(10)
        saida.pack_start(rotulo("Tirar da estante: o disco sai da estante e vai para a Lixeira. "
                                "As músicas continuam no computador."), False, False, 0)
        saida.pack_start(botao("Tirar da estante", icone_nome="lixeira", ao_clicar=self._tirar),
                         False, False, 0)
        direita.pack_start(saida, False, False, 12)
        quadro.pack_start(direita, True, True, 0)
        self.raiz.pack_start(quadro, True, True, 0)
        self.raiz.show_all()
        self._redesenhar_previa()
        self._redesenhar_galeria()

    def _opcoes_de_capa(self):
        """(rótulo, escolha, miniatura) de cada capa possível; só para discos de verdade."""
        if not isinstance(self.disco, Album):
            return []
        embutida, imagem = cover_options(self.disco)
        pasta = self.ctx.pasta_miniaturas
        opcoes = []
        for rotulo_, fonte, tipo in (("Capa do arquivo", embutida, "embedded"),
                                     ("Imagem da pasta", imagem, "file")):
            if fonte is not None:
                miniatura = make_thumbnail(fonte, pasta, 256) if pasta else None
                opcoes.append((rotulo_, CoverChoice(tipo, fonte.path), miniatura))
        opcoes.append(("Capa desenhada", CoverChoice("drawn"), None))
        return opcoes

    # -- pedaços que mudam -------------------------------------------------------------------------

    def _atualizar_aviso(self) -> None:
        if self._area_do_aviso is None:
            return
        limpar(self._area_do_aviso)
        a = self.ctx.session.aviso
        if a is not None:
            self._area_do_aviso.pack_start(
                aviso(a.texto, self.ctx.session.desfazer if a.desfazer else None,
                      a.rotulo_do_desfazer), False, False, 0)
        self._area_do_aviso.show_all()

    def _redesenhar_previa(self) -> None:
        area = self._area_da_previa
        limpar(area)
        area.pack_start(rotulo("Como vai ficar na estante", "moa-forte", centro=True),
                        False, False, 0)
        area.pack_start(self._capa_da_previa(210), False, False, 0)
        area.pack_start(rotulo(self.nome or "(sem nome)", "moa-grande", centro=True,
                               largura_maxima=18), False, False, 0)
        area.show_all()

    def _capa_da_previa(self, lado: int) -> Gtk.Widget:
        if not isinstance(self.disco, Album) or self.escolha is None:
            return capa_do_disco(self.ctx, self.disco, lado)
        miniatura = next((m for _r, c, m in self.opcoes if c == self.escolha), None)
        return Capa(self.disco, miniatura, lado)

    def _redesenhar_galeria(self) -> None:
        galeria = self._area_da_galeria
        if galeria is None:
            return
        for filho in galeria.get_children():
            galeria.remove(filho)
        for rotulo_, escolha, miniatura in self.opcoes:
            escolhida = self.escolha == escolha
            peca = caixa_v(6)
            peca.pack_start(Capa(self.disco, miniatura, 96), False, False, 0)
            peca.pack_start(rotulo(rotulo_ + ("\nEscolhida" if escolhida else ""),
                                   "moa-forte", centro=True, largura_maxima=14), False, False, 0)
            b = Gtk.Button()
            b.add(peca)
            b.get_style_context().add_class("moa-opcao")
            if escolhida:
                b.get_style_context().add_class("moa-escolhida")
            b.connect("clicked", lambda _b, e=escolha: self._escolher_capa(e))
            galeria.add(b)
        galeria.show_all()

    # -- ações -----------------------------------------------------------------------------------------

    def _ao_digitar_o_nome(self, campo: Gtk.Entry) -> None:
        self.nome = campo.get_text()
        self._redesenhar_previa()

    def _escolher_capa(self, escolha: CoverChoice) -> None:
        self.ctx.session.acao()
        self.escolha = escolha
        self._redesenhar_previa()
        self._redesenhar_galeria()

    def _voltar(self) -> None:
        self.ctx.session.voltar()

    def _cancelar(self) -> None:
        self.ctx.session.acao()
        self._voltar()

    def _guardar(self) -> None:
        ctx, disco = self.ctx, self.disco
        ctx.session.acao()
        try:
            box.guardar_edicao(ctx.banco, disco.id, self.nome, self.escolha)
        except sqlite3.Error:
            log.exception("não consegui guardar a edição do disco")
            ctx.session.mostrar_aviso(MSG_FALHA)
            return
        ctx.recarregar(capas=self.escolha is not None)
        novo = ctx.disco(disco.id)
        if ctx.radio.tem_disco and ctx.radio.disco.id == disco.id and novo is not None:
            ctx.radio.disco = novo                    # o rádio passa a mostrar o nome novo
        self._voltar()
        ctx.session.mostrar_aviso(
            f"Guardei. O disco agora se chama “{novo.title if novo else self.nome}”.",
            desfazer=lambda: self._como_era_antes(disco.id), rotulo_do_desfazer="Como era antes")

    def _como_era_antes(self, disco_id: str) -> None:
        box.como_era_antes(self.ctx.banco, disco_id)
        self.ctx.recarregar(capas=True)
        atual = self.ctx.disco(disco_id)
        if self.ctx.radio.tem_disco and self.ctx.radio.disco.id == disco_id and atual is not None:
            self.ctx.radio.disco = atual

    def _tirar(self) -> None:
        ctx, disco = self.ctx, self.disco
        ctx.session.acao()
        try:
            box.tirar_da_estante(ctx.banco, disco.id)
        except sqlite3.Error:
            log.exception("não consegui tirar o disco da estante")
            ctx.session.mostrar_aviso(MSG_FALHA)
            return
        if ctx.radio.tem_disco and ctx.radio.disco.id == disco.id:
            ctx.radio.guardar_o_disco_e_parar()       # o disco sai do rádio junto
        ctx.recarregar()
        ctx.session.ir_para(Tela.ESTANTE)

        def desfazer() -> None:
            box.colocar_de_volta(ctx.banco, disco.id)
            ctx.recarregar()

        ctx.session.mostrar_aviso(
            f"Tirei “{disco.title}” da estante. Ele está na Lixeira; as músicas continuam no computador.",
            desfazer)
