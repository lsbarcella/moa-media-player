# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tela "Montando um disco novo": o botão grande "Criar uma playlist" (forma a).

O usuário marca músicas de outros discos e elas formam um disco novo na estante.
Começar a digitar manda o texto direto para a busca, sem clicar nela antes. As
marcações ficam guardadas no rascunho, então filtrar não desmarca nada.
Desenho aprovado em `docs/preview/moa-preview.html` (ideia I2).
"""

import logging
import sqlite3

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core import custom_albums  # noqa: E402
from moa.core.contexto import Contexto  # noqa: E402
from moa.core.models import MixDisc  # noqa: E402
from moa.core.session import Tela  # noqa: E402
from moa.ui.widgets import aviso, botao, capa_do_disco, caixa_h, caixa_v, limpar, rotulo  # noqa: E402

log = logging.getLogger(__name__)

MAXIMO_NA_LISTA = 150          # mais que isso pesa no notebook antigo; o filtro resolve
TEXTO_DA_BUSCA = "Procurar música (é só começar a digitar)"


def _caixinha(marcada: bool) -> Gtk.Widget:
    """O quadradinho de marcar: um "✓" dentro de uma borda grossa (texto, não só cor)."""
    caixa = Gtk.Box()
    caixa.get_style_context().add_class("moa-caixinha")
    caixa.set_size_request(40, 40)
    etiqueta = rotulo("✓" if marcada else " ", "moa-forte", quebrar=False, centro=True)
    caixa.pack_start(etiqueta, True, True, 0)
    return caixa


class PlaylistView:
    def __init__(self, contexto: Contexto):
        self.ctx = contexto
        self.raiz = caixa_v(0)
        self.raiz.set_border_width(24)
        self._construido = False
        self.campo_de_busca: Gtk.Entry | None = None
        self.campo_do_nome: Gtk.Entry | None = None
        self._area_do_aviso: Gtk.Box | None = None
        self._area_das_pecas: Gtk.Box | None = None
        self._area_da_lista: Gtk.Box | None = None
        self._area_do_cartao: Gtk.Box | None = None
        self._botoes_de_filtro: dict[str, Gtk.Button] = {}
        self.atualizar()

    # -- ciclo de vida -------------------------------------------------------------------

    def ao_entrar(self) -> None:
        """A tela voltou a ser mostrada: reconstrói a moldura (as marcações ficam no rascunho)."""
        self._construido = False

    def atualizar(self) -> None:
        if self.ctx.rascunho is None:
            self.ctx.novo_rascunho()
        if not self._construido:
            self._construir()
        self._atualizar_aviso()

    def foco_inicial(self) -> Gtk.Widget | None:
        return self.campo_de_busca

    # -- construção -------------------------------------------------------------------------

    def _construir(self) -> None:
        rascunho = self.ctx.rascunho
        limpar(self.raiz)
        self._botoes_de_filtro = {}
        self._area_do_aviso = caixa_v(0)
        self.raiz.pack_start(self._area_do_aviso, False, False, 0)

        quadro = Gtk.Box(orientation=Gtk.Orientation.VERTICAL
                         if self.ctx.preferencias.config.letra != "normal"
                         else Gtk.Orientation.HORIZONTAL, spacing=22)
        esquerda = caixa_v(10)
        esquerda.pack_start(rotulo(TEXTO_DA_BUSCA, "moa-forte"), False, False, 0)
        self.campo_de_busca = Gtk.Entry()
        self.campo_de_busca.set_placeholder_text("Digite parte do nome da música")
        self.campo_de_busca.set_text(rascunho.busca)
        self.campo_de_busca.connect("changed", self._ao_digitar)
        esquerda.pack_start(self.campo_de_busca, False, False, 0)
        esquerda.pack_start(rotulo("Também dá para escolher sem digitar: clique em um disco "
                                   "abaixo e marque as músicas.", "moa-nota"), False, False, 0)

        filtros = Gtk.FlowBox()
        filtros.set_selection_mode(Gtk.SelectionMode.NONE)
        filtros.set_activate_on_single_click(True)
        filtros.set_row_spacing(8)
        filtros.set_column_spacing(8)
        pares = [(custom_albums.RascunhoDePlaylist.TODOS, "Todos os discos")]
        pares += [(d.id, d.title) for d in self.ctx.discos[:6]]
        for chave, texto in pares:
            b = botao(texto, ao_clicar=lambda c=chave: self._escolher_disco(c))
            self._botoes_de_filtro[chave] = b
            filtros.add(b)
        esquerda.pack_start(filtros, False, False, 0)

        self._area_da_lista = caixa_v(8)
        esquerda.pack_start(self._area_da_lista, False, False, 0)
        quadro.pack_start(esquerda, True, True, 0)

        cartao = caixa_v(12)
        cartao.get_style_context().add_class("moa-cartao")
        cartao.set_size_request(360, -1)
        self._area_do_cartao = cartao
        quadro.pack_start(cartao, False, False, 0)
        self.raiz.pack_start(quadro, True, True, 0)
        self._construido = True
        self.raiz.show_all()
        self._redesenhar_filtros()
        self._redesenhar_lista()
        self._redesenhar_cartao()

    # -- pedaços que mudam ----------------------------------------------------------------------

    def _atualizar_aviso(self) -> None:
        limpar(self._area_do_aviso)
        a = self.ctx.session.aviso
        if a is not None:
            self._area_do_aviso.pack_start(
                aviso(a.texto, self.ctx.session.desfazer if a.desfazer else None, a.rotulo_do_desfazer), False, False, 0)
        self._area_do_aviso.show_all()

    def _redesenhar_filtros(self) -> None:
        escolhido = self.ctx.rascunho.disco_do_filtro
        for chave, b in self._botoes_de_filtro.items():
            contexto = b.get_style_context()
            if chave == escolhido:
                contexto.add_class("moa-escolhida")
            else:
                contexto.remove_class("moa-escolhida")

    def _redesenhar_lista(self) -> None:
        rascunho = self.ctx.rascunho
        limpar(self._area_da_lista)
        achados = rascunho.filtrar(self.ctx.discos)
        if not achados:
            cartao = caixa_v(0)
            cartao.get_style_context().add_class("moa-cartao")
            cartao.pack_start(rotulo("Nenhuma música encontrada. Apague uma letra ou escolha "
                                     "“Todos os discos”."), False, False, 0)
            self._area_da_lista.pack_start(cartao, False, False, 0)
        for disco, faixa in achados[:MAXIMO_NA_LISTA]:
            self._area_da_lista.pack_start(self._linha(disco, faixa), False, False, 0)
        if len(achados) > MAXIMO_NA_LISTA:
            self._area_da_lista.pack_start(
                rotulo(f"Mostrando as primeiras {MAXIMO_NA_LISTA} músicas. Digite ou escolha um "
                       "disco para achar as outras.", "moa-nota"), False, False, 0)
        self._area_da_lista.show_all()

    def _linha(self, disco, faixa) -> Gtk.Button:
        marcada = self.ctx.rascunho.esta_marcada(str(faixa.path))
        conteudo = caixa_h(14)
        conteudo.pack_start(_caixinha(marcada), False, False, 0)
        textos = caixa_v(0)
        textos.pack_start(rotulo(faixa.title, "moa-forte"), False, False, 0)
        textos.pack_start(rotulo(disco.title, "moa-nota"), False, False, 0)
        conteudo.pack_start(textos, True, True, 0)
        conteudo.pack_end(rotulo("Marcada" if marcada else "", "moa-forte", quebrar=False),
                          False, False, 0)
        b = Gtk.Button()
        b.add(conteudo)
        b.get_style_context().add_class("moa-marca")
        if marcada:
            b.get_style_context().add_class("moa-marcada")
        b.connect("clicked", lambda _b, c=str(faixa.path): self._alternar(c))
        return b

    def _redesenhar_cartao(self) -> None:
        ctx, rascunho = self.ctx, self.ctx.rascunho
        cartao = self._area_do_cartao
        limpar(cartao)
        escolhidas = [ctx.faixas_por_caminho[c] for c in rascunho.marcadas
                      if c in ctx.faixas_por_caminho]
        n = len(escolhidas)
        cartao.pack_start(rotulo("Disco novo", "moa-grande"), False, False, 0)
        mix = MixDisc(id="rascunho", title=rascunho.nome, tracks=tuple(escolhidas))
        cartao.pack_start(capa_do_disco(ctx, mix, 200), False, False, 0)
        if rascunho.renomeando:
            cartao.pack_start(rotulo("Nome do disco", "moa-forte"), False, False, 0)
            self.campo_do_nome = Gtk.Entry()
            self.campo_do_nome.set_text(rascunho.nome)
            self.campo_do_nome.connect("changed", self._ao_digitar_o_nome)
            cartao.pack_start(self.campo_do_nome, False, False, 0)
        else:
            cartao.pack_start(rotulo(rascunho.nome, "moa-grande"), False, False, 0)
        quantas = ("Nenhuma música escolhida" if n == 0 else
                   "1 música escolhida" if n == 1 else f"{n} músicas escolhidas")
        cartao.pack_start(rotulo(quantas, "moa-forte"), False, False, 0)
        for i, faixa in enumerate(escolhidas[:20], 1):
            cartao.pack_start(rotulo(f"{i}. {faixa.title}"), False, False, 0)
        if n > 20:
            cartao.pack_start(rotulo(f"... e mais {n - 20}", "moa-nota"), False, False, 0)
        if n:
            cartao.pack_start(botao("Guardar na estante", "moa-pri", "moa-grande",
                                    ao_clicar=self._guardar), False, False, 0)
        else:
            cartao.pack_start(botao("Marque pelo menos uma música", "moa-grande", "moa-inativo"),
                              False, False, 0)
        cartao.pack_start(
            botao("Pronto, este nome" if rascunho.renomeando else "Mudar o nome",
                  ao_clicar=self._mudar_o_nome), False, False, 0)
        cartao.show_all()

    # -- ações ----------------------------------------------------------------------------------------

    def _ao_digitar(self, campo: Gtk.Entry) -> None:
        self.ctx.rascunho.busca = campo.get_text()
        self._redesenhar_lista()

    def _ao_digitar_o_nome(self, campo: Gtk.Entry) -> None:
        self.ctx.rascunho.nome = campo.get_text()

    def digitar(self, caractere: str) -> None:
        """Uma letra digitada com o foco fora do campo: vai para a busca, sem clicar antes."""
        self.campo_de_busca.grab_focus()
        self.campo_de_busca.set_text(self.campo_de_busca.get_text() + caractere)
        self.campo_de_busca.set_position(-1)

    def _escolher_disco(self, chave: str) -> None:
        self.ctx.session.acao()
        self.ctx.rascunho.disco_do_filtro = chave
        self._redesenhar_filtros()
        self._redesenhar_lista()

    def _alternar(self, caminho: str) -> None:
        self.ctx.session.acao()
        self.ctx.rascunho.alternar(caminho)
        self._redesenhar_lista()
        self._redesenhar_cartao()

    def _mudar_o_nome(self) -> None:
        self.ctx.session.acao()
        rascunho = self.ctx.rascunho
        rascunho.renomeando = not rascunho.renomeando
        if not rascunho.renomeando and not rascunho.nome.strip():
            rascunho.nome = custom_albums.sugerir_nome(
                [d.title for d in self.ctx.montados + self.ctx.caixa])
        self._redesenhar_cartao()
        if rascunho.renomeando:
            self.campo_do_nome.grab_focus()

    def _guardar(self) -> None:
        ctx, rascunho = self.ctx, self.ctx.rascunho
        ctx.session.acao()
        nome = rascunho.nome.strip() or custom_albums.sugerir_nome([])
        try:
            custom_albums.criar(ctx.banco, nome, list(rascunho.marcadas))
        except sqlite3.Error:
            log.exception("não consegui guardar o disco montado")
            ctx.session.mostrar_aviso("Não consegui guardar o disco. Suas músicas continuam "
                                      "marcadas; tente de novo.")
            return
        ctx.rascunho = None
        ctx.recarregar()
        ctx.session.ir_para(Tela.ESTANTE)
        ctx.session.mostrar_aviso(f"Pronto! O disco “{nome}” está na estante.")
