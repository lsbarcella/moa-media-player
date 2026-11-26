# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Janela principal: cabeçalho fixo, a tela atual e o mini-rádio.

O conteúdo (`Conteudo`) é separado da janela (`MainWindow`) de propósito: uma
janela de topo não cabe dentro de outra, e os testes precisam colocar o conteúdo
num `Gtk.OffscreenWindow` para desenhá-lo sem abrir nada na tela (KTD15).

Regras que moram aqui (CLAUDE.md, seção 9):
- cabeçalho fixo, com um caminho de volta sempre visível fora da Estante;
- o botão "Configurações" aparece em toda tela, menos na própria;
- atalhos de teclado são comodidade, nunca o único caminho: espaço toca/pausa,
  setas esquerda e direita trocam de faixa, cima e baixo mudam o volume.
"""

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

from moa.core.contexto import Contexto  # noqa: E402
from moa.core.session import Tela  # noqa: E402
from moa.ui import theme  # noqa: E402
from moa.ui.box_view import BoxView  # noqa: E402
from moa.ui.edit_view import EditView  # noqa: E402
from moa.ui.playlist_view import PlaylistView  # noqa: E402
from moa.ui.plus_panel import PlusPanel  # noqa: E402
from moa.ui.radio_view import RadioView  # noqa: E402
from moa.ui.settings_view import SettingsView  # noqa: E402
from moa.ui.shelf_view import ShelfView  # noqa: E402
from moa.ui.widgets import botao, caixa_h, caixa_v, limpar, rotulo  # noqa: E402

SEGUNDOS_ENTRE_GRAVACOES = 5


class Conteudo:
    """O que aparece dentro da janela. Não é uma janela."""

    def __init__(self, contexto: Contexto):
        self.ctx = contexto
        self.raiz = caixa_v(0)
        self.raiz.get_style_context().add_class("moa-fundo")

        self.cabecalho = caixa_h(16)
        self.cabecalho.get_style_context().add_class("moa-cabecalho")
        self.raiz.pack_start(self.cabecalho, False, False, 0)

        self.pilha = Gtk.Stack()
        self.pilha.set_transition_type(Gtk.StackTransitionType.NONE)
        # O painel do "+" fica POR CIMA da tela (dentro da janela, nunca uma janela nova).
        self.sobreposicao = Gtk.Overlay()
        self.sobreposicao.add(self.pilha)
        self.plus = PlusPanel(contexto)
        self.sobreposicao.add_overlay(self.plus.raiz)
        self.raiz.pack_start(self.sobreposicao, True, True, 0)

        self.mini = caixa_h(14)
        self.mini.get_style_context().add_class("moa-mini")
        self.raiz.pack_start(self.mini, False, False, 0)

        self.telas: dict[Tela, object] = {}
        self.registrar(Tela.ESTANTE, ShelfView(contexto))
        self.registrar(Tela.RADIO, RadioView(contexto))
        self.registrar(Tela.CONFIGURACOES, SettingsView(contexto))
        self.registrar(Tela.PLAYLIST, PlaylistView(contexto))
        self.registrar(Tela.CAIXA, BoxView(contexto))
        self.registrar(Tela.EDITAR, EditView(contexto))
        self._ultima_tela = None

        contexto.session.ao_mudar(self.redesenhar)
        contexto.radio.ao_mudar(self.redesenhar)
        contexto.ao_mudar_a_colecao(self.redesenhar)
        contexto.preferencias.ao_mudar(self._ao_mudar_preferencia)
        self.redesenhar()

    def registrar(self, tela: Tela, visao) -> None:
        """Põe uma tela na pilha. Cada tela rola sozinha se não couber."""
        rolagem = Gtk.ScrolledWindow()
        rolagem.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        rolagem.add(visao.raiz)
        self.pilha.add_named(rolagem, tela.value)
        self.telas[tela] = visao

    def _ao_mudar_preferencia(self) -> None:
        config = self.ctx.preferencias.config
        theme.aplicar(config.paleta, config.letra)
        self.redesenhar()

    # -- desenho ---------------------------------------------------------------------------

    def redesenhar(self) -> None:
        sessao = self.ctx.session
        self._desenhar_cabecalho()
        visao = self.telas.get(sessao.tela, self.telas[Tela.ESTANTE])
        if sessao.tela != self._ultima_tela and hasattr(visao, "ao_entrar"):
            visao.ao_entrar()
        self._ultima_tela = sessao.tela
        visao.atualizar()
        self.plus.atualizar()
        self.pilha.set_visible_child_name(
            sessao.tela.value if sessao.tela in self.telas else Tela.ESTANTE.value)
        self._desenhar_mini()
        self.raiz.show_all()
        alvo = self.plus.primeiro_botao if sessao.faixa_do_painel is not None else visao.foco_inicial()
        if alvo is not None:
            alvo.grab_focus()

    def _desenhar_cabecalho(self) -> None:
        sessao = self.ctx.session
        limpar(self.cabecalho)
        esquerda = caixa_h(8)
        esquerda.set_size_request(280, -1)
        texto = sessao.texto_de_voltar
        if texto is not None:
            acao = sessao.voltar if sessao.tela == Tela.CONFIGURACOES else sessao.voltar_para_a_estante
            esquerda.pack_start(botao(texto, ao_clicar=acao, icone_nome="voltar"), False, False, 0)
        direita = caixa_h(8)
        direita.set_size_request(280, -1)
        direita.set_halign(Gtk.Align.END)
        if sessao.mostra_botao_configuracoes and Tela.CONFIGURACOES in self.telas:
            direita.pack_end(botao("Configurações", icone_nome="engrenagem",
                                   ao_clicar=lambda: sessao.ir_para(Tela.CONFIGURACOES)),
                             False, False, 0)
        self.cabecalho.pack_start(esquerda, False, False, 0)
        self.cabecalho.pack_start(rotulo(sessao.titulo, "moa-titulo", centro=True,
                                         quebrar=False), True, True, 0)
        self.cabecalho.pack_end(direita, False, False, 0)

    def _desenhar_mini(self) -> None:
        radio = self.ctx.radio
        limpar(self.mini)
        visor = radio.visor()
        if visor is None or self.ctx.session.tela == Tela.RADIO:
            self.mini.hide()
            self.mini.set_no_show_all(True)
            return
        self.mini.set_no_show_all(False)
        self.mini.pack_start(
            rotulo(f"Tocando agora: {visor.titulo} ({visor.disco})", "moa-forte"), True, True, 0)
        self.mini.pack_start(
            botao("Pausar" if radio.tocando else "Tocar", ao_clicar=self._alternar_do_mini,
                  icone_nome="pausar" if radio.tocando else "tocar"),
            False, False, 0)
        self.mini.pack_start(
            botao("Abrir o rádio", ao_clicar=lambda: self.ctx.session.ir_para(Tela.RADIO)),
            False, False, 0)
        self.mini.show_all()

    def _alternar_do_mini(self) -> None:
        self.ctx.session.acao()
        self.ctx.radio.alternar()

    # -- teclado -----------------------------------------------------------------------------

    def tratar_tecla(self, evento: Gdk.EventKey, foco: Gtk.Widget | None) -> bool:
        """Atalhos no nível da janela. Devolve True se a tecla foi usada.

        Rodam ANTES dos botões, para o espaço não "apertar" de novo o botão que
        está com foco. Quando o idoso digita (busca, nome do disco), as teclas
        pertencem ao campo de texto.
        """
        if isinstance(foco, Gtk.Editable):
            return False
        if evento.state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK):
            return False
        if self.ctx.session.faixa_do_painel is not None and evento.keyval == Gdk.KEY_Escape:
            self.ctx.session.fechar_painel_mais()
            return True
        if self.ctx.session.tela == Tela.PLAYLIST:
            codigo = Gdk.keyval_to_unicode(evento.keyval)
            if codigo and chr(codigo).isprintable():
                # Quem digita na tela de montar disco quer procurar: a letra vai direto para a busca.
                self.telas[Tela.PLAYLIST].digitar(chr(codigo))
                return True
        radio = self.ctx.radio
        if not radio.tem_disco:
            return False
        acoes = {
            Gdk.KEY_space: radio.alternar,
            Gdk.KEY_Left: radio.anterior,
            Gdk.KEY_Right: radio.proxima,
            Gdk.KEY_Up: radio.volume_mais,
            Gdk.KEY_Down: radio.volume_menos,
        }
        acao = acoes.get(evento.keyval)
        if acao is None:
            return False
        self.ctx.session.acao()
        acao()
        return True

    # -- relógio (chamado a cada meio segundo) -------------------------------------------------

    def tique(self, contador: int) -> None:
        if not self.ctx.radio.tocando:
            return
        if self.ctx.session.tela == Tela.RADIO:
            self.telas[Tela.RADIO].atualizar_tempo()
        if contador % (SEGUNDOS_ENTRE_GRAVACOES * 2) == 0:
            self.ctx.radio.guardar_posicao()


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, contexto: Contexto, **kwargs) -> None:
        super().__init__(title="Moa Media Player", **kwargs)
        self.ctx = contexto
        config = contexto.preferencias.config
        theme.aplicar(config.paleta, config.letra)
        self.get_style_context().add_class("moa")
        self.conteudo = Conteudo(contexto)
        self.add(self.conteudo.raiz)
        # Janela normal de programa, com barra de título e X do sistema (ADR-0002).
        self.set_default_size(1100, 760)
        self._contador = 0
        self.connect("key-press-event", self._ao_apertar_tecla)
        self.connect("delete-event", self._ao_fechar)
        GLib.timeout_add(500, self._tique)
        self.show_all()

    def _ao_apertar_tecla(self, _janela, evento) -> bool:
        return self.conteudo.tratar_tecla(evento, self.get_focus())

    def _tique(self) -> bool:
        self._contador += 1
        self.conteudo.tique(self._contador)
        return True

    def _ao_fechar(self, _janela, _evento) -> bool:
        """Fechar pelo X salva o estado e encerra (não há botão de desligar)."""
        self.ctx.encerrar()
        return False
