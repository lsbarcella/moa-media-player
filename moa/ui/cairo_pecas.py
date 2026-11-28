# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Peças do aparelho desenhadas em Cairo (ADR-0024): parafuso, dobradiça, serrilha e lente.

Cada `desenhar_*` é uma função pura: recebe um contexto Cairo, o tamanho, a paleta e um estado, e
só desenha. É como uma função `(ctx, w, h, paleta, estado) => void` em TypeScript sobre um canvas.
Nada aqui importa GTK, então dá para testar sem tela.

O desenho de uma peça nunca muda para o mesmo (nome, tamanho, estado, paleta); por isso o
`CacheDeDesenho` guarda o resultado e o reaproveita, e a CPU antiga só desenha uma vez.
Sem animação contínua: a peça só é redesenhada quando o estado muda.
"""

import math
from collections import OrderedDict
from typing import NamedTuple

import cairo

from moa.ui import theme


def cor_rgb(paleta: str, token: str) -> tuple[float, float, float]:
    cor = theme.PALETAS[paleta][token].lstrip("#")
    return tuple(int(cor[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _contorno(paleta: str) -> bool:
    """No preto e branco a peça é só contorno e traço, sem tons (KTD3)."""
    return theme.relevo(paleta) == "contorno"


def desenhar_parafuso(cr: cairo.Context, w: int, h: int, paleta: str, estado: int = 0) -> None:
    """Parafuso de latão com fenda. `estado` gira a fenda (0, 1, 2, 3 = 45 graus cada)."""
    raio = min(w, h) / 2 - 1
    cx, cy = w / 2, h / 2
    cr.arc(cx, cy, raio, 0, 2 * math.pi)
    if _contorno(paleta):
        cr.set_source_rgb(*cor_rgb(paleta, "white"))
        cr.fill_preserve()
        cr.set_source_rgb(*cor_rgb(paleta, "dark"))
        cr.set_line_width(max(2.0, raio / 4))
        cr.stroke()
        fenda = cor_rgb(paleta, "dark")
    else:
        brilho = cairo.RadialGradient(cx - raio / 3, cy - raio / 3, raio / 6, cx, cy, raio)
        brilho.add_color_stop_rgb(0, *cor_rgb(paleta, "brass_hi"))
        brilho.add_color_stop_rgb(1, *cor_rgb(paleta, "brass_lo"))
        cr.set_source(brilho)
        cr.fill_preserve()
        cr.set_source_rgba(*cor_rgb(paleta, "dark"), 0.8)
        cr.set_line_width(1.2)
        cr.stroke()
        fenda = cor_rgb(paleta, "dark")
    cr.save()
    cr.translate(cx, cy)
    cr.rotate(math.radians(45 * (estado % 4) + 20))
    cr.set_source_rgb(*fenda)
    cr.set_line_width(max(1.5, raio / 4))
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.move_to(-raio * 0.65, 0)
    cr.line_to(raio * 0.65, 0)
    cr.stroke()
    cr.restore()


def desenhar_dobradica(cr: cairo.Context, w: int, h: int, paleta: str, estado: int = 0) -> None:
    """Dobradiça da lombada da caixa de CD: um cilindro de metal com um pino no meio."""
    cr.rectangle(0, 0, w, h)
    if _contorno(paleta):
        cr.set_source_rgb(*cor_rgb(paleta, "white"))
        cr.fill_preserve()
        cr.set_source_rgb(*cor_rgb(paleta, "dark"))
        cr.set_line_width(2)
        cr.stroke()
    else:
        cilindro = cairo.LinearGradient(0, 0, w, 0)
        cilindro.add_color_stop_rgb(0, *cor_rgb(paleta, "metal_lo"))
        cilindro.add_color_stop_rgb(0.4, *cor_rgb(paleta, "metal_hi"))
        cilindro.add_color_stop_rgb(1, *cor_rgb(paleta, "metal_lo"))
        cr.set_source(cilindro)
        cr.fill()
    cr.set_source_rgb(*cor_rgb(paleta, "dark"))
    cr.arc(w / 2, h / 2, max(1.5, min(w, h) / 6), 0, 2 * math.pi)
    cr.fill()


def desenhar_serrilha(cr: cairo.Context, w: int, h: int, paleta: str, estado: int = 0) -> None:
    """Borda serrilhada do botão de volume: `estado` é o ângulo em graus (o botão gira)."""
    raio = min(w, h) / 2 - 1
    cx, cy = w / 2, h / 2
    dentes = 24
    cr.save()
    cr.translate(cx, cy)
    cr.rotate(math.radians(estado))
    for i in range(dentes):
        ang = 2 * math.pi * i / dentes
        cr.move_to(math.cos(ang) * raio * 0.86, math.sin(ang) * raio * 0.86)
        cr.line_to(math.cos(ang) * raio, math.sin(ang) * raio)
    cr.set_source_rgb(*cor_rgb(paleta, "dark" if _contorno(paleta) else "metal_lo"))
    cr.set_line_width(max(1.5, raio / 14))
    cr.stroke()
    cr.arc(0, 0, raio * 0.86, 0, 2 * math.pi)
    if _contorno(paleta):
        cr.set_source_rgb(*cor_rgb(paleta, "white"))
        cr.fill_preserve()
        cr.set_source_rgb(*cor_rgb(paleta, "dark"))
        cr.set_line_width(3)
        cr.stroke()
    else:
        face = cairo.RadialGradient(-raio / 3, -raio / 3, raio / 8, 0, 0, raio)
        face.add_color_stop_rgb(0, *cor_rgb(paleta, "metal_hi"))
        face.add_color_stop_rgb(1, *cor_rgb(paleta, "metal_lo"))
        cr.set_source(face)
        cr.fill()
    # o traço indicador: mostra para onde o botão aponta
    cr.set_source_rgb(*cor_rgb(paleta, "dark"))
    cr.set_line_width(max(2.5, raio / 8))
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.move_to(0, -raio * 0.25)
    cr.line_to(0, -raio * 0.7)
    cr.stroke()
    cr.restore()


def desenhar_lente(cr: cairo.Context, w: int, h: int, paleta: str, estado: bool = False) -> None:
    """Lâmpada-piloto com lente: aro de metal, vidro (aceso ou apagado) e um reflexo no canto."""
    raio = min(w, h) / 2 - 1
    cx, cy = w / 2, h / 2
    cr.arc(cx, cy, raio, 0, 2 * math.pi)
    cr.set_source_rgb(*cor_rgb(paleta, "dark" if _contorno(paleta) else "metal_lo"))
    cr.fill()
    cr.arc(cx, cy, raio * 0.78, 0, 2 * math.pi)
    cr.set_source_rgb(*cor_rgb(paleta, "lampon" if estado else "lampoff"))
    cr.fill()
    if not _contorno(paleta):
        cr.arc(cx - raio * 0.25, cy - raio * 0.28, raio * 0.22, 0, 2 * math.pi)
        cr.set_source_rgba(1, 1, 1, 0.8 if estado else 0.45)
        cr.fill()


class GeometriaDaCaixa(NamedTuple):
    """Onde ficam as partes da caixa de CD, em pixels (como uma `interface` de TypeScript)."""
    quadro: int         # espessura da moldura de plástico
    lombada: int        # largura da lombada, à esquerda
    arte_x: int
    arte_y: int
    arte_lado: int      # a arte é um quadrado


def geometria_da_caixa(lado: int) -> GeometriaDaCaixa:
    """Divide um quadrado `lado` x `lado` em moldura, lombada e o quadrado da arte."""
    quadro = max(4, round(lado * 0.045))
    lombada = max(8, round(lado * 0.09))
    arte_lado = lado - lombada - 2 * quadro
    return GeometriaDaCaixa(quadro, lombada, lombada + quadro, (lado - arte_lado) // 2, arte_lado)


def desenhar_caixa_de_cd(cr: cairo.Context, w: int, h: int, paleta: str, estado: int = 0) -> None:
    """Moldura de plástico + lombada com duas dobradiças. O MIOLO FICA TRANSPARENTE.

    A arte do disco é pintada por quem chama, dentro do miolo. Como o reflexo só existe na
    moldura, ele nunca cobre a arte nem o texto da capa substituta (ADR-0024).
    """
    g = geometria_da_caixa(min(w, h))
    lado = min(w, h)
    contorno = _contorno(paleta)
    # moldura de plástico: retângulo arredondado com o miolo recortado (regra par-ímpar)
    cr.new_path()
    _retangulo_arredondado(cr, 0.5, 0.5, lado - 1, lado - 1, 6)
    cr.rectangle(g.arte_x, g.arte_y, g.arte_lado, g.arte_lado)
    cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    if contorno:
        cr.set_source_rgb(*cor_rgb(paleta, "white"))
    else:
        plastico = cairo.LinearGradient(0, 0, lado, lado)
        plastico.add_color_stop_rgb(0, *cor_rgb(paleta, "metal_hi"))
        plastico.add_color_stop_rgb(1, *cor_rgb(paleta, "metal_lo"))
        cr.set_source(plastico)
    cr.fill()
    cr.set_fill_rule(cairo.FILL_RULE_WINDING)
    # contorno só por fora (riscar o miolo sujaria a borda da arte)
    cr.new_path()
    _retangulo_arredondado(cr, 0.5, 0.5, lado - 1, lado - 1, 6)
    cr.set_source_rgb(*cor_rgb(paleta, "dark"))
    cr.set_line_width(3 if contorno else 1.5)
    cr.stroke()
    # lombada: faixa escura na esquerda (cinza-escuro, decisão em aberto do autor)
    cr.rectangle(g.quadro, g.quadro, g.lombada, lado - 2 * g.quadro)
    cr.set_source_rgb(*cor_rgb(paleta, "dark"))
    cr.fill()
    # duas dobradiças na lombada, em cima e embaixo
    dobradica = max(6, g.lombada - 2)
    for y in (g.quadro + 2, lado - g.quadro - 2 - dobradica):
        cr.save()
        cr.translate(g.quadro + (g.lombada - dobradica) / 2, y)
        desenhar_dobradica(cr, dobradica, dobradica, paleta)
        cr.restore()
    # reflexo: um fio claro só no alto da moldura e na borda esquerda da lombada
    if not contorno:
        cr.set_source_rgba(1, 1, 1, 0.75)
        cr.set_line_width(1.5)
        cr.move_to(8, 1.5)
        cr.line_to(lado - 8, 1.5)
        cr.move_to(1.5, 8)
        cr.line_to(1.5, lado - 8)
        cr.stroke()


def _retangulo_arredondado(cr: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
    cr.move_to(x + r, y)
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


class CacheDeDesenho:
    """Guarda o desenho pronto de cada peça por (nome, tamanho, estado, paleta).

    Parecido com um `Map<string, ImageBitmap>` em TypeScript, só que com limite: ao passar dele,
    sai o mais antigo (`OrderedDict` lembra a ordem de entrada). Assim a RAM não cresce à toa.
    """

    def __init__(self, limite: int = 64) -> None:
        self._limite = limite
        self._itens: OrderedDict = OrderedDict()

    def __len__(self) -> int:
        return len(self._itens)

    def chaves(self) -> list:
        return list(self._itens)

    def limpar(self) -> None:
        self._itens.clear()

    def obter(self, nome: str, w: int, h: int, paleta: str, estado, desenhar) -> cairo.ImageSurface:
        chave = (nome, w, h, estado, paleta)
        if chave in self._itens:
            self._itens.move_to_end(chave)
            return self._itens[chave]
        superficie = cairo.ImageSurface(cairo.FORMAT_ARGB32, max(1, w), max(1, h))
        desenhar(cairo.Context(superficie), w, h, paleta, estado)
        self._itens[chave] = superficie
        if len(self._itens) > self._limite:
            self._itens.popitem(last=False)
        return superficie


CACHE = CacheDeDesenho()
