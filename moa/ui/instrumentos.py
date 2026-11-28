# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Instrumentos do rádio desenhados em Cairo: o botão de volume e a escala do visor (ADR-0024).

Os dois são `Gtk.DrawingArea`, que é como um `<canvas>`: o GTK chama `_ao_desenhar` quando precisa
pintar. Nenhum dos dois reage a clique, arraste ou foco (regra do projeto: nada de botão giratório
que exija arrastar). Quem mexe neles é o programa: `definir_degrau` e `definir` só pedem um novo
desenho quando o valor mudou. As peças vêm do `CACHE`, então pintar não custa quase nada.
O texto ("Volume: N de 10", "Faixa X de Y") continua nos rótulos de sempre: aqui só há traços e luzes.
"""

import math

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.ui import cairo_pecas, theme  # noqa: E402

VARREDURA_GRAUS = 270            # o botão vai de -135 graus (mínimo) a +135 (máximo)
MAXIMO_DE_TRACOS = 24            # a escala nunca desenha mais traços que isto (discos de 371 faixas)
LADO_DO_BOTAO_PX = 132


def angulo_do_botao(degrau: int, maximo: int) -> float:
    """Ângulo, em graus, para onde o botão aponta: 0 no meio, negativo à esquerda."""
    degrau = max(0, min(maximo, degrau))
    return -VARREDURA_GRAUS / 2 + VARREDURA_GRAUS * degrau / maximo


def posicoes_dos_tracos(total: int) -> list[float]:
    """Onde ficam os traços da escala, de 0 (início) a 1 (fim). Com muitas faixas, agrupa."""
    if total <= 0:
        return []
    if total == 1:
        return [0.0]
    quantos = min(total, MAXIMO_DE_TRACOS)
    return [k / (quantos - 1) for k in range(quantos)]


def posicao_do_marcador(faixa: int, total: int) -> float:
    """Onde fica o marcador da faixa atual (faixa 1 = início, última = fim)."""
    if total <= 1:
        return 0.0
    return (max(1, min(total, faixa)) - 1) / (total - 1)


def _rgb(paleta: str, token: str) -> tuple[float, float, float]:
    cor = theme.PALETAS[paleta][token].lstrip("#")
    return tuple(int(cor[i:i + 2], 16) / 255 for i in (0, 2, 4))


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
        cr.set_source_rgb(*_rgb(paleta, "white"))
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


class EscalaDoVisor(Gtk.DrawingArea):
    """Régua gravada embaixo do visor, com um marcador na faixa que está tocando."""

    ALTURA_PX = 26

    def __init__(self) -> None:
        super().__init__()
        self.faixa = 0
        self.total = 0
        self.set_size_request(-1, self.ALTURA_PX)
        self.set_can_focus(False)
        self.connect("draw", self._ao_desenhar)

    def definir(self, faixa: int, total: int) -> bool:
        """Move o marcador. Devolve se mudou (e portanto se pediu um desenho novo)."""
        if (faixa, total) == (self.faixa, self.total):
            return False
        self.faixa, self.total = faixa, total
        self.queue_draw()
        return True

    def _ao_desenhar(self, _widget, cr) -> bool:
        if self.total <= 0:
            return False
        paleta = theme.paleta_atual()
        w, h = self.get_allocated_width(), self.get_allocated_height()
        margem = 10
        largura_util = max(1, w - 2 * margem)
        cr.set_source_rgb(*_rgb(paleta, "ink"))
        cr.set_line_width(2)
        cr.move_to(margem, h - 6)                   # a linha da régua
        cr.line_to(w - margem, h - 6)
        for pos in posicoes_dos_tracos(self.total):  # os traços gravados
            x = margem + pos * largura_util
            cr.move_to(x, h - 6)
            cr.line_to(x, h - 14)
        cr.stroke()
        x = margem + posicao_do_marcador(self.faixa, self.total) * largura_util
        cr.move_to(x, h - 3)                        # marcador: triângulo cheio apontando para a régua
        cr.line_to(x - 7, 2)
        cr.line_to(x + 7, 2)
        cr.close_path()
        cr.set_source_rgb(*_rgb(paleta, "danger" if theme.relevo(paleta) == "tons" else "ink"))
        cr.fill_preserve()
        cr.set_source_rgb(*_rgb(paleta, "ink"))
        cr.set_line_width(1.5)
        cr.stroke()
        return False
