# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Instrumentos do rádio: o botão de volume (Cairo) e a barra de progresso clicável (ADR-0024, ADR-0026).

Os dois são `Gtk.DrawingArea`, que é como um `<canvas>`: o GTK chama `_ao_desenhar` quando precisa
pintar. Nenhum dos dois reage a clique, arraste ou foco (regra do projeto: nada de botão giratório
que exija arrastar). Quem mexe neles é o programa: `definir_degrau` e `definir` só pedem um novo
desenho quando o valor mudou. As peças vêm do `CACHE`, então pintar não custa quase nada.
O texto ("Volume: N de 10") continua no rótulo de sempre: no botão só há luzes e serrilha.
"""

import math

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from moa.core.radio import formatar_tempo  # noqa: E402
from moa.ui import cairo_pecas, theme  # noqa: E402
from moa.ui.widgets import caixa_h, rotulo, texto_de  # noqa: E402

VARREDURA_GRAUS = 270            # o botão vai de -135 graus (mínimo) a +135 (máximo)
LADO_DO_BOTAO_PX = 104


def angulo_do_botao(degrau: int, maximo: int) -> float:
    """Ângulo, em graus, para onde o botão aponta: 0 no meio, negativo à esquerda."""
    degrau = max(0, min(maximo, degrau))
    return -VARREDURA_GRAUS / 2 + VARREDURA_GRAUS * degrau / maximo


class BotaoDeVolume(Gtk.DrawingArea):
    """Botão de volume: coroa de lâmpadas com lente em volta de um botão serrilhado que gira."""

    def __init__(self, maximo: int) -> None:
        super().__init__()
        self.maximo = maximo
        self.degrau = 0
        self.set_size_request(LADO_DO_BOTAO_PX, LADO_DO_BOTAO_PX)
        self.set_can_focus(False)               # não é um controle: só mostra
        self.connect("draw", self._ao_desenhar)

    def definir_degrau(self, degrau: int) -> bool:
        """Gira o botão. Devolve se mudou (e portanto se pediu um desenho novo)."""
        degrau = max(0, min(self.maximo, degrau))
        if degrau == self.degrau:
            return False
        self.degrau = degrau
        self.queue_draw()
        return True

    def _ao_desenhar(self, _widget, cr) -> bool:
        paleta = theme.paleta_atual()
        lado = min(self.get_allocated_width(), self.get_allocated_height())
        cx, cy = self.get_allocated_width() / 2, self.get_allocated_height() / 2
        raio_da_coroa = lado / 2 - 9
        lente = 16
        # coroa: uma lâmpada com lente para cada degrau, acesa até o degrau atual
        for k in range(self.maximo):
            ang = math.radians(angulo_do_botao(k, self.maximo - 1) - 90)
            x = cx + math.cos(ang) * raio_da_coroa - lente / 2
            y = cy + math.sin(ang) * raio_da_coroa - lente / 2
            peca = cairo_pecas.CACHE.obter("lente", lente, lente, paleta, k < self.degrau,
                                           cairo_pecas.desenhar_lente)
            cr.set_source_surface(peca, round(x), round(y))
            cr.paint()
        # escala gravada: 11 traços finos (0 a 10) logo dentro da coroa
        cr.set_source_rgb(*cairo_pecas.cor_rgb(paleta, "white"))
        cr.set_line_width(2)
        for k in range(self.maximo + 1):
            ang = math.radians(angulo_do_botao(k, self.maximo) - 90)
            cr.move_to(cx + math.cos(ang) * (raio_da_coroa - 14), cy + math.sin(ang) * (raio_da_coroa - 14))
            cr.line_to(cx + math.cos(ang) * (raio_da_coroa - 20), cy + math.sin(ang) * (raio_da_coroa - 20))
        cr.stroke()
        # o botão serrilhado, num ângulo por degrau (só 11 desenhos possíveis, guardados no cache)
        lado_do_botao = round(raio_da_coroa * 1.25)
        peca = cairo_pecas.CACHE.obter("serrilha", lado_do_botao, lado_do_botao, paleta,
                                       round(angulo_do_botao(self.degrau, self.maximo)),
                                       cairo_pecas.desenhar_serrilha)
        cr.set_source_surface(peca, round(cx - lado_do_botao / 2), round(cy - lado_do_botao / 2))
        cr.paint()
        return False


class BarraDeProgresso(Gtk.EventBox):
    """A barra de progresso comum de qualquer aplicativo: um clique vai ao ponto clicado.

    É um `Gtk.ProgressBar` dentro de uma `EventBox` (que recebe o clique). A área clicável tem
    64 px de altura, bem mais alta que o desenho da barra. Só um clique: nada de arrastar. Não
    recebe o foco do teclado, porque as setas esquerda e direita já são Anterior e Próxima.
    `ao_escolher(fracao)` é chamado com um número de 0.0 (início) a 1.0 (fim).
    """

    ALTURA_DO_ALVO_PX = 64

    def __init__(self, ao_escolher) -> None:
        super().__init__()
        self._ao_escolher = ao_escolher
        self._fracao = 0.0
        self._barra = Gtk.ProgressBar()
        self._barra.get_style_context().add_class("moa-barra")
        self._barra.set_valign(Gtk.Align.CENTER)
        self.add(self._barra)
        self.set_tooltip_text("Clique para ir a outro ponto da música")
        self.set_size_request(-1, self.ALTURA_DO_ALVO_PX)
        self.set_can_focus(False)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("button-press-event", self._ao_clicar)

    @property
    def fracao(self) -> float:
        return self._fracao

    def definir_fracao(self, fracao: float) -> bool:
        """Mostra o ponto `fracao` (0 a 1). Devolve se mudou (e portanto se redesenhou)."""
        fracao = max(0.0, min(1.0, fracao))
        if round(fracao, 3) == round(self._fracao, 3):
            return False
        self._fracao = fracao
        self._barra.set_fraction(fracao)
        return True

    def escolher_em(self, x: float) -> None:
        """O clique caiu em `x` pixels da ponta esquerda: vira uma fração e avisa quem escuta."""
        largura = max(1, self._barra.get_allocated_width())
        fracao = max(0.0, min(1.0, (x - self._barra.get_allocation().x) / largura))
        self.definir_fracao(fracao)             # a barra responde na hora, antes do som alcançar
        self._ao_escolher(fracao)

    def _ao_clicar(self, _widget, evento) -> bool:
        if evento.button != 1:
            return False
        self.escolher_em(evento.x)
        return True


class LinhaDeProgresso(Gtk.Box):
    """O tempo decorrido, a barra de progresso clicável e a duração total, lado a lado.

    É usada na barra do pé das outras telas e no visor do rádio. `atualizar_do_radio` mexe só no
    que mudou (a fração da barra e os dois tempos), então pode ser chamada uma vez por segundo.
    """

    def __init__(self, ao_escolher) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        self.rotulo_atual = rotulo("0:00", "moa-forte", quebrar=False)
        self.rotulo_total = rotulo("", "moa-forte", quebrar=False)
        self.barra = BarraDeProgresso(ao_escolher)
        self.barra.set_hexpand(True)
        self.pack_start(self.rotulo_atual, False, False, 0)
        self.pack_start(self.barra, True, True, 0)
        self.pack_start(self.rotulo_total, False, False, 0)

    def atualizar_do_radio(self, radio) -> None:
        fracao = radio.progresso()
        self.barra.definir_fracao(fracao if fracao is not None else 0.0)
        texto_de(self.rotulo_atual, formatar_tempo(radio.player.posicao()) or "0:00")
        texto_de(self.rotulo_total, formatar_tempo(radio.player.duracao()))
