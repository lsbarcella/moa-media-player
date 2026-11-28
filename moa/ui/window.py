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
from moa.ui.cd_view import CDView  # noqa: E402
from moa.ui import ornamentos  # noqa: E402
from moa.ui.instrumentos import BarraDeProgresso, LinhaDeProgresso  # noqa: E402
from moa.ui.inibidor import Inibidor  # noqa: E402
from moa.ui.edit_view import EditView  # noqa: E402
from moa.ui.playlist_view import PlaylistView  # noqa: E402
from moa.ui.plus_panel import PlusPanel  # noqa: E402
from moa.ui.radio_view import RadioView  # noqa: E402
from moa.ui.settings_view import SettingsView  # noqa: E402
from moa.ui.shelf_view import ShelfView  # noqa: E402
from moa.ui.widgets import aviso, botao, caixa_h, caixa_v, classe, limpar, rotulo, texto_de  # noqa: E402

SEGUNDOS_ENTRE_GRAVACOES = 5


class Conteudo:
    """O que aparece dentro da janela. Não é uma janela."""

    def __init__(self, contexto: Contexto):
        self.ctx = contexto
        config = contexto.preferencias.config
        self._tema_aplicado = (config.paleta, config.letra)
        self.raiz = caixa_v(0)
        self.raiz.get_style_context().add_class("moa-fundo")

        self.cabecalho = caixa_h(16)
        self.cabecalho.get_style_context().add_class("moa-cabecalho")
        self.raiz.pack_start(self.cabecalho, False, False, 0)

        # Faixa de falha inesperada (M5): aparece em qualquer tela, logo abaixo do cabeçalho.
        self.area_da_falha = caixa_v(0)
        self.raiz.pack_start(self.area_da_falha, False, False, 0)

        self.pilha = Gtk.Stack()
        self.pilha.set_transition_type(Gtk.StackTransitionType.NONE)
        # O painel do "+" fica POR CIMA da tela (dentro da janela, nunca uma janela nova).
        self.sobreposicao = Gtk.Overlay()
        self.sobreposicao.add(self.pilha)
        self.plus = PlusPanel(contexto)
        self.sobreposicao.add_overlay(self.plus.raiz)
        self.raiz.pack_start(self.sobreposicao, True, True, 0)

        self.mini = caixa_v(4)                       # a barra do rádio (ADR-0026)
        self.mini.get_style_context().add_class("moa-mini")
        ornamentos.instalar_parafusos(self.mini, diametro=12, margem=6)
        self.barra_do_radio: BarraDeProgresso | None = None
        self._progresso_do_mini: LinhaDeProgresso | None = None
        self.raiz.pack_start(self.mini, False, False, 0)

        self.telas: dict[Tela, object] = {}
        self.registrar(Tela.ESTANTE, ShelfView(contexto))
        self.registrar(Tela.RADIO, RadioView(contexto))
        self.registrar(Tela.CONFIGURACOES, SettingsView(contexto))
        self.registrar(Tela.PLAYLIST, PlaylistView(contexto))
        self.registrar(Tela.CAIXA, BoxView(contexto))
        self.registrar(Tela.EDITAR, EditView(contexto))
        self.registrar(Tela.APARELHO_DE_CD, CDView(contexto))
        self._ultima_tela = None
        self._chave_do_cabecalho: tuple | None = None
        self._falha_desenhada: str | None = None
        self._chave_do_mini: object = "inicial"       # diferente de tudo: a 1ª vez sempre desenha

        contexto.session.ao_mudar(self.redesenhar)
        contexto.aparelho.ao_mudar(self.redesenhar)
        contexto.ao_progredir_a_leitura(self._ao_progredir_a_leitura)
        contexto.atualizacao.ao_mudar(self.redesenhar)     # ATUALIZACAO_DE_TESTE
        contexto.radio.ao_mudar(self.redesenhar)
        contexto.ao_mudar_a_colecao(self.redesenhar)
        contexto.preferencias.ao_mudar(self._ao_mudar_preferencia)
        self.redesenhar()
        self.raiz.show_all()        # uma vez, na montagem; depois cada parte se mostra sozinha

    def _ao_progredir_a_leitura(self) -> None:
        if self.ctx.session.tela == Tela.ESTANTE:
            self.telas[Tela.ESTANTE].atualizar_progresso()

    def registrar(self, tela: Tela, visao) -> None:
        """Põe uma tela na pilha. Cada tela rola sozinha se não couber."""
        rolagem = Gtk.ScrolledWindow()
        rolagem.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        rolagem.set_overlay_scrolling(False)      # a barra fica sempre à vista (nada de aparecer só com o mouse)
        rolagem.add(visao.raiz)
        self.pilha.add_named(rolagem, tela.value)
        self.telas[tela] = visao

    def _ao_mudar_preferencia(self) -> None:
        config = self.ctx.preferencias.config
        # Volume e "Voz mais clara" também são preferências. Reaplicar o tema faz o GTK recalcular
        # o estilo de TODOS os widgets (centenas, numa lista grande), então só se a aparência mudou.
        if (config.paleta, config.letra) != self._tema_aplicado:
            theme.aplicar(config.paleta, config.letra)
            self._tema_aplicado = (config.paleta, config.letra)
        self.redesenhar()

    # -- desenho ---------------------------------------------------------------------------

    def redesenhar(self) -> None:
        sessao = self.ctx.session
        self._desenhar_cabecalho()
        self._desenhar_falha()
        visao = self.telas.get(sessao.tela, self.telas[Tela.ESTANTE])
        if sessao.tela != self._ultima_tela and hasattr(visao, "ao_entrar"):
            visao.ao_entrar()
        self._ultima_tela = sessao.tela
        visao.atualizar()
        self.plus.atualizar()
        self.pilha.set_visible_child_name(
            sessao.tela.value if sessao.tela in self.telas else Tela.ESTANTE.value)
        self._desenhar_mini()
        alvo = self.plus.primeiro_botao if sessao.faixa_do_painel is not None else visao.foco_inicial()
        if alvo is not None:
            alvo.grab_focus()

    def _desenhar_cabecalho(self) -> None:
        sessao = self.ctx.session
        chave = (sessao.tela, sessao.texto_de_voltar, sessao.titulo, sessao.mostra_botao_configuracoes)
        if chave == self._chave_do_cabecalho:
            return                  # igual ao que já está na tela
        self._chave_do_cabecalho = chave
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
        self.cabecalho.show_all()

    def _desenhar_falha(self) -> None:
        texto = self.ctx.session.falha
        if texto == self._falha_desenhada:
            return
        self._falha_desenhada = texto
        limpar(self.area_da_falha)
        if texto is None:
            return
        self.area_da_falha.pack_start(aviso(texto), False, False, 0)
        self.area_da_falha.show_all()

    def _desenhar_mini(self) -> None:
        """A barra do rádio no pé das outras telas: visor, teclas, "Abrir o rádio" e a barra de progresso.

        Só é refeita quando muda o que ela mostra (música, faixa, tocando ou pausado). O andamento
        da música é atualizado no lugar, uma vez por segundo, por `atualizar_progresso_do_mini`.
        """
        radio = self.ctx.radio
        visor = radio.visor()
        escondido = visor is None or self.ctx.session.tela == Tela.RADIO
        chave = None if escondido else (visor.titulo, visor.disco, visor.faixa, radio.tocando)
        if chave == self._chave_do_mini:
            return
        self._chave_do_mini = chave
        limpar(self.mini)
        self.barra_do_radio, self._progresso_do_mini = None, None
        if escondido:
            self.mini.hide()
            self.mini.set_no_show_all(True)
            return
        self.mini.set_no_show_all(False)

        # linha de cima: visor, as três teclas na bandeja preta e "Abrir o rádio"
        linha = Gtk.FlowBox()
        linha.set_selection_mode(Gtk.SelectionMode.NONE)
        linha.set_homogeneous(False)
        linha.set_min_children_per_line(1)
        linha.set_max_children_per_line(3)
        linha.set_column_spacing(14)
        linha.set_row_spacing(10)
        vidro = caixa_v(2)
        vidro.get_style_context().add_class("moa-visor")
        vidro.set_size_request(260, -1)
        vidro.set_hexpand(True)
        estado = caixa_h(10)                      # lâmpada, estado e música numa só linha: a barra fica baixa
        lampada = Gtk.Box()
        lampada.get_style_context().add_class("moa-lampada")
        lampada.set_valign(Gtk.Align.CENTER)
        classe(lampada, "moa-acesa", visor.luz_acesa)
        estado.pack_start(lampada, False, False, 0)
        estado.pack_start(rotulo(visor.palavra, "moa-forte", quebrar=False), False, False, 0)
        estado.pack_start(rotulo(visor.titulo, "moa-grande", quebrar=False), False, False, 0)
        vidro.pack_start(estado, False, False, 0)
        vidro.pack_start(rotulo(f"{visor.faixa} · {visor.disco}", quebrar=False), False, False, 0)
        bandeja = caixa_h(6)
        bandeja.get_style_context().add_class("moa-bandeja")
        bandeja.pack_start(botao("Anterior", ao_clicar=self._anterior_do_mini, icone_nome="anterior"), False, False, 0)
        if radio.tocando:
            bandeja.pack_start(botao("Pausar", "moa-pausar", ao_clicar=self._alternar_do_mini, icone_nome="pausar"),
                               False, False, 0)
        else:
            bandeja.pack_start(botao("Tocar", "moa-pri", ao_clicar=self._alternar_do_mini, icone_nome="tocar"),
                               False, False, 0)
        bandeja.pack_start(botao("Próxima", ao_clicar=self._proxima_do_mini, icone_nome="proxima"), False, False, 0)
        abrir = botao("Abrir o rádio", ao_clicar=lambda: self.ctx.session.ir_para(Tela.RADIO))
        for peca in (vidro, bandeja, abrir):
            linha.add(peca)
        for filha in linha.get_children():
            filha.set_can_focus(False)                # só os botões recebem o foco, não a "caixinha" do FlowBox
        self.mini.pack_start(linha, False, False, 0)

        # barra de progresso comum, com o tempo nas pontas; um clique vai ao ponto
        self._progresso_do_mini = LinhaDeProgresso(self._buscar_do_mini)
        self.barra_do_radio = self._progresso_do_mini.barra
        self.mini.pack_start(self._progresso_do_mini, False, False, 0)
        self.mini.show_all()
        self.atualizar_progresso_do_mini()

    def atualizar_progresso_do_mini(self) -> None:
        """Move a barra de progresso e os tempos, só mexendo no que mudou."""
        if self._progresso_do_mini is not None:
            self._progresso_do_mini.atualizar_do_radio(self.ctx.radio)

    def _buscar_do_mini(self, fracao: float) -> None:
        self.ctx.session.acao()
        self.ctx.radio.buscar_fracao(fracao)

    def _anterior_do_mini(self) -> None:
        self.ctx.session.acao()
        self.ctx.radio.anterior()

    def _proxima_do_mini(self) -> None:
        self.ctx.session.acao()
        self.ctx.radio.proxima()

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
        if self.ctx.carregando and self.ctx.session.tela == Tela.ESTANTE:
            self.telas[Tela.ESTANTE].atualizar_progresso()      # o aviso de demora aparece com o tempo
        if not self.ctx.radio.tocando:
            return
        if self.ctx.session.tela == Tela.RADIO:
            self.telas[Tela.RADIO].atualizar_tempo()
        else:
            self.atualizar_progresso_do_mini()
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
        # Enquanto toca, o notebook não dorme nem apaga a tela (precisa da aplicação).
        aplicacao = self.get_application()
        self.inibidor = Inibidor(aplicacao, self, contexto.radio) if aplicacao else None
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
        if self.inibidor is not None:
            self.inibidor.soltar()
        self.ctx.encerrar()
        return False
