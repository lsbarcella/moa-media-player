#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Gera imagens PNG das telas do Moa, para conferir a aparência (ADR-0024).

Uso (de qualquer pasta):  python3 tools/telas.py DESTINO [--paletas ...] [--letras ...]

Desenha as seis telas (Estante, Tocando agora, Aparelho de CD, Lixeira, Configurações e Criar uma
playlist) nas quatro paletas e nas três escalas de letra: 6 x 4 x 3 = 72 imagens. Usa uma
coleção sintética pequena e uma janela fora da tela, então roda sem música de verdade.

Para o autor (vem de TypeScript): é como um script de "screenshot testing" (Playwright): abre cada
tela com cada combinação de tema e grava uma foto, para olhar com os próprios olhos.
"""

import argparse
import importlib.util
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst, Gtk  # noqa: E402

from moa.core.config import Preferencias  # noqa: E402
from moa.core.contexto import Contexto  # noqa: E402
from moa.core.db import Database  # noqa: E402
from moa.core.library import scan  # noqa: E402
from moa.core.session import Tela  # noqa: E402
from moa.ui import theme  # noqa: E402
from moa.ui.window import Conteudo  # noqa: E402

TELAS = {
    "estante": Tela.ESTANTE,
    "radio": Tela.RADIO,
    "aparelho-de-cd": Tela.APARELHO_DE_CD,
    "lixeira": Tela.CAIXA,
    "configuracoes": Tela.CONFIGURACOES,
    "playlist": Tela.PLAYLIST,
}
LARGURA, ALTURA = 1100, 800


def _medidor():
    """Reaproveita a geração de coleção sintética de tools/measure.py (é um script, não um pacote)."""
    spec = importlib.util.spec_from_file_location("measure", RAIZ / "tools" / "measure.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _sem_som() -> Gst.Element:
    destino = Gst.ElementFactory.make("fakesink", None)
    destino.set_property("sync", False)
    return destino


def _girar(segundos: float) -> None:
    laco = GLib.MainContext.default()
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        while laco.iteration(False):
            pass
        time.sleep(0.01)


def gerar(destino: Path, paletas=None, letras=None, telas=None) -> list[Path]:
    """Grava uma imagem por (tela, paleta, letra) e devolve os caminhos."""
    paletas = list(paletas or theme.PALETAS)
    letras = list(letras or theme.ESCALAS)
    telas = list(telas or TELAS)
    destino.mkdir(parents=True, exist_ok=True)
    Gst.init(None)
    medidor = _medidor()
    with tempfile.TemporaryDirectory() as temporaria:
        base = Path(temporaria)
        musica = base / "musica"
        musica.mkdir()
        audio = medidor.gerar_audio_base(base, 4, "base")
        medidor.gerar_colecao(musica, audio, 6, 8, "Artista de Exemplo")
        prefs = Preferencias(base / "config.json")
        theme.aplicar(prefs.config.paleta, prefs.config.letra)
        ctx = Contexto(Database(base / "moa.db"), prefs, musica, sink_factory=_sem_som,
                       pasta_miniaturas=base / "miniaturas")
        conteudo = Conteudo(ctx)
        janela = Gtk.OffscreenWindow()
        janela.set_size_request(LARGURA, ALTURA)
        janela.add(conteudo.raiz)
        janela.show_all()
        ctx.definir_colecao(scan(musica), {})
        ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
        gravadas = []
        for paleta in paletas:
            for letra in letras:
                prefs.mudar(paleta=paleta, letra=letra)
                theme.aplicar(paleta, letra)
                for nome in telas:
                    ctx.session.ir_para(TELAS[nome])
                    _girar(0.35)
                    arquivo = destino / f"{nome}__{paleta}__{letra}.png"
                    janela.get_pixbuf().savev(str(arquivo), "png", [], [])
                    gravadas.append(arquivo)
        janela.destroy()
    return gravadas


def main() -> int:
    ap = argparse.ArgumentParser(description="Gera imagens das telas do Moa.")
    ap.add_argument("destino", type=Path)
    ap.add_argument("--paletas", nargs="*", choices=list(theme.PALETAS))
    ap.add_argument("--letras", nargs="*", choices=list(theme.ESCALAS))
    ap.add_argument("--telas", nargs="*", choices=list(TELAS))
    args = ap.parse_args()
    arquivos = gerar(args.destino, args.paletas, args.letras, args.telas)
    print(f"{len(arquivos)} imagens em {args.destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
