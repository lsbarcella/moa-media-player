# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tela "Minha estante": os discos à vista, um clique para pegar um disco.

Desenho aprovado em `docs/preview/moa-preview.html`. A estante lembra
(decisão do autor): "Continuar a ouvir", "Ouvidos há pouco" e o lugar vazio
"Em uso no rádio" quando o disco está no rádio.
"""

import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.contexto import Contexto  # noqa: E402
from moa.core.session import Tela  # noqa: E402
from moa.ui.cartao_de_atualizacao import cartao_de_atualizacao, deve_aparecer_na_estante  # noqa: E402     # ATUALIZACAO_DE_TESTE
from moa.ui.widgets import EmPedacos, texto_de, aviso, botao, capa_do_disco, caixa_h, caixa_v, limpar, rotulo  # noqa: E402

log = logging.getLogger(__name__)

TEXTO_CARREGANDO = "Estou procurando os seus discos..."
SEGUNDOS_ATE_AVISAR_DA_DEMORA = 5
TEXTO_DA_DEMORA = ("Isso pode demorar um pouco na primeira vez. Pode esperar: está tudo certo "
                   "e não precisa fazer nada.")
TEXTO_VAZIO = ("Ainda não há discos aqui. Quando houver músicas na pasta de música, "
               "os discos aparecem na estante.")


class ShelfView:
    def __init__(self, contexto: Contexto):
        self.ctx = contexto
        self.raiz = caixa_v(18)
        self.raiz.set_border_width(24)
        self.raiz.set_halign(Gtk.Align.FILL)
        self.botao_principal: Gtk.Widget | None = None
        self._chave_desenhada: tuple | None = None
        self._foco_pendente = False
        self._construtores: list[EmPedacos] = []
        contexto.ao_mudar_a_colecao(self._esquecer_o_desenho)
        self.atualizar()

    # -- desenho ---------------------------------------------------------------------

    def _esquecer_o_desenho(self) -> None:
        """A coleção mudou (disco novo, nome, capa, Caixa): na próxima vez a estante é refeita."""
        self._chave_desenhada = None

    def _chave(self) -> tuple:
        """Tudo o que a estante mostra além da coleção. Se for igual, não há por que refazê-la:
        com 80 discos isso custava ~220 ms no notebook do usuário a cada aviso ou toque."""
        ctx = self.ctx
        radio = ctx.radio
        ids = ctx.ids_dos_discos
        onde = None if radio.tem_disco else ctx.memoria.onde_parou(ids)
        a = ctx.atualizacao
        return (
            ctx.carregando, bool(ctx.discos or ctx.montados),
            radio.disco.id if radio.tem_disco else None,
            tuple(ctx.memoria.recentes(ids)),
            (onde.album_id, onde.indice) if onde else None,
            ctx.session.aviso, ctx.aparelho.copiando,
            (a.habilitada, a.momento, a.commit_remoto, a.tem_versao_anterior),    # ATUALIZACAO_DE_TESTE
        )

    def ao_entrar(self) -> None:
        self._foco_pendente = True

    def atualizar(self) -> None:
        ctx = self.ctx
        chave = self._chave()
        if chave == self._chave_desenhada:
            return                  # nada que a estante mostra mudou
        self._chave_desenhada = None        # só vale depois de o desenho terminar sem erro
        try:
            self._refazer()
        except Exception:
            log.exception("não consegui desenhar a estante; tento de novo no próximo toque")
            raise
        self._chave_desenhada = chave

    def _refazer(self) -> None:
        ctx = self.ctx
        self._foco_pendente = True
        for construtor in self._construtores:
            construtor.cancelar()
        self._construtores = []
        limpar(self.raiz)
        self.botao_principal = None
        if ctx.session.aviso is not None:
            a = ctx.session.aviso
            self.raiz.pack_start(aviso(a.texto, ctx.session.desfazer if a.desfazer else None, a.rotulo_do_desfazer),
                                 False, False, 0)

        if deve_aparecer_na_estante(ctx):                                 # ATUALIZACAO_DE_TESTE
            self.raiz.pack_start(cartao_de_atualizacao(ctx), False, False, 0)

        self._detalhe = self._demora = None
        if not ctx.discos and not ctx.montados:
            cartao = caixa_v(8)
            cartao.get_style_context().add_class("moa-cartao")
            if ctx.carregando:
                self._desenhar_carregando(cartao)
            else:
                cartao.pack_start(rotulo(TEXTO_VAZIO), False, False, 0)
            self.raiz.pack_start(cartao, False, False, 0)
            if not ctx.carregando:      # com a estante vazia é por aqui que o primeiro disco entra
                linha = caixa_h(14)
                linha.pack_start(self._botao_colocar_disco(), False, False, 0)
                self.botao_principal = linha.get_children()[0]
                self.raiz.pack_start(linha, False, False, 0)
            self.raiz.show_all()
            return

        self._desenhar_acoes()
        self._desenhar_continuar()
        recentes = [d for d in (ctx.disco(i) for i in ctx.memoria.recentes(ctx.ids_dos_discos)) if d]
        self._desenhar_prateleira("Ouvidos há pouco", recentes)
        self._desenhar_prateleira("Meus discos", ctx.discos)
        self._desenhar_prateleira("Discos que montei", ctx.montados)
        self.raiz.show_all()

    # -- "carregando": a primeira leitura pode levar vários segundos num notebook antigo ---------

    def _desenhar_carregando(self, cartao: Gtk.Box) -> None:
        linha = caixa_h(14)
        movimento = Gtk.Spinner()
        movimento.set_size_request(48, 48)
        movimento.start()
        linha.pack_start(movimento, False, False, 0)
        linha.pack_start(rotulo(TEXTO_CARREGANDO, "moa-forte"), True, True, 0)
        cartao.pack_start(linha, False, False, 0)
        self._detalhe = rotulo("")
        self._demora = rotulo("", "moa-nota")
        cartao.pack_start(self._detalhe, False, False, 0)
        cartao.pack_start(self._demora, False, False, 0)
        self.atualizar_progresso()

    def texto_do_progresso(self) -> str:
        p = self.ctx.progresso_da_leitura
        if p is None:
            return ""
        etapa, feitos, total = p
        if etapa == "capas":
            return f"Preparando as capas: {feitos} de {total}."
        return "Já olhei 1 música." if feitos == 1 else f"Já olhei {feitos} músicas."

    def atualizar_progresso(self) -> None:
        """Atualiza só o andamento e o aviso de demora, sem redesenhar a estante."""
        if self._detalhe is None:
            return
        texto_de(self._detalhe, self.texto_do_progresso())
        demorou = self.ctx.segundos_de_leitura() >= SEGUNDOS_ATE_AVISAR_DA_DEMORA
        texto_de(self._demora, TEXTO_DA_DEMORA if demorou else "")

    def _desenhar_acoes(self) -> None:
        linha = caixa_h(14)
        criar = botao("Criar uma playlist", "moa-pri", "moa-grande", icone_nome="mais",
                      ao_clicar=self._criar_playlist)
        linha.pack_start(criar, False, False, 0)
        linha.pack_start(self._botao_colocar_disco(), False, False, 0)
        n = len(self.ctx.caixa)
        linha.pack_start(botao(f"A Caixa ({n} {'disco' if n == 1 else 'discos'})", "moa-grande",
                               icone_nome="caixa", ao_clicar=self._abrir_a_caixa), False, False, 0)
        self.botao_principal = criar
        self.raiz.pack_start(linha, False, False, 0)

    def _botao_colocar_disco(self) -> Gtk.Widget:
        copiando = self.ctx.aparelho.copiando
        return botao("Ver a cópia do disco" if copiando else "Colocar um disco", "moa-grande",
                     icone_nome="disco", ao_clicar=self._abrir_o_aparelho)

    def _abrir_o_aparelho(self) -> None:
        self.ctx.session.ir_para(Tela.APARELHO_DE_CD)

    def _abrir_a_caixa(self) -> None:
        self.ctx.session.ir_para(Tela.CAIXA)

    def _criar_playlist(self) -> None:
        self.ctx.session.acao()
        self.ctx.novo_rascunho()
        self.ctx.session.ir_para(Tela.PLAYLIST)

    def _desenhar_continuar(self) -> None:
        ctx = self.ctx
        if ctx.radio.tem_disco:
            return
        onde = ctx.memoria.onde_parou(ctx.ids_dos_discos)
        if onde is None:
            return
        disco = ctx.disco(onde.album_id)
        if disco is None or onde.indice >= len(disco.tracks):
            return
        cartao = caixa_h(16)
        cartao.get_style_context().add_class("moa-cartao")
        cartao.get_style_context().add_class("moa-continuar")
        cartao.pack_start(
            rotulo(f"Você parou em {disco.title}, faixa {onde.indice + 1}."), True, True, 0)
        b = botao("Continuar a ouvir", "moa-pri", "moa-grande",
                  ao_clicar=lambda: self._continuar(disco, onde))
        cartao.pack_start(b, False, False, 0)
        self.botao_principal = b
        self.raiz.pack_start(cartao, False, False, 0)

    def _desenhar_prateleira(self, titulo: str, discos) -> None:
        if not discos:
            return
        secao = caixa_v(12)
        placa = Gtk.Box()
        placa.get_style_context().add_class("moa-placa")
        placa.pack_start(rotulo(titulo, quebrar=False), False, False, 0)
        placa.set_halign(Gtk.Align.START)
        secao.pack_start(placa, False, False, 0)

        grade = Gtk.FlowBox()
        grade.set_selection_mode(Gtk.SelectionMode.NONE)
        grade.set_activate_on_single_click(True)       # um clique ativa (CLAUDE.md, seção 9)
        grade.set_homogeneous(True)
        grade.set_min_children_per_line(1)
        grade.set_max_children_per_line(8)
        grade.set_column_spacing(18)
        grade.set_row_spacing(20)
        def acrescentar(disco) -> None:
            peca = self._peca(disco)
            grade.add(peca)
            peca.show_all()
            peca.get_parent().show()            # a caixinha que o FlowBox põe em volta

        # Estantes grandes aparecem em pedaços: os primeiros discos já na hora.
        self._construtores.append(EmPedacos(discos, acrescentar, minimo=24).iniciar())
        moldura = caixa_v(0)
        moldura.get_style_context().add_class("moa-tabua")
        moldura.pack_start(grade, False, False, 0)
        secao.pack_start(moldura, False, False, 0)
        self.raiz.pack_start(secao, False, False, 0)
        if self.botao_principal is None:
            self.botao_principal = grade.get_child_at_index(0).get_child()

    def _peca(self, disco) -> Gtk.Widget:
        ctx = self.ctx
        peca = caixa_v(8)
        if ctx.radio.tem_disco and ctx.radio.disco.id == disco.id:
            vazio = Gtk.Box()
            vazio.get_style_context().add_class("moa-vazio")
            vazio.set_size_request(150, 150)
            vazio.pack_start(rotulo("Em uso no rádio", centro=True), True, True, 8)
            peca.pack_start(vazio, False, False, 0)
            peca.pack_start(rotulo("Ir ao rádio", "moa-forte", centro=True), False, False, 0)
            clique = lambda: ctx.session.ir_para(Tela.RADIO)
        else:
            peca.pack_start(capa_do_disco(ctx, disco), False, False, 0)
            peca.pack_start(rotulo(disco.title, "moa-forte", centro=True, largura_maxima=14), False, False, 0)
            clique = lambda d=disco: self._pegar(d)
        b = Gtk.Button()
        b.add(peca)
        b.get_style_context().add_class("moa-disco")
        b.connect("clicked", lambda _b: clique())
        return b

    # -- ações ---------------------------------------------------------------------------

    def _pegar(self, disco) -> None:
        self.ctx.session.acao()
        self.ctx.radio.abrir_disco(disco)
        self.ctx.session.ir_para(Tela.RADIO)

    def _continuar(self, disco, onde) -> None:
        self.ctx.session.acao()
        self.ctx.radio.abrir_disco(disco, indice=onde.indice, posicao=onde.segundos, tocar=True)
        self.ctx.session.ir_para(Tela.RADIO)

    def foco_inicial(self) -> Gtk.Widget | None:
        if not self._foco_pendente:
            return None             # a estante não mudou: o foco fica onde o usuário o deixou
        self._foco_pendente = False
        return self.botao_principal
