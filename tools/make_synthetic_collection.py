#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Gera uma coleção de música SINTÉTICA para verificar o app sem usar a coleção real.

Uso: python3 tools/make_synthetic_collection.py DESTINO [--discos 80] [--faixas 10]

Cria `discos` pastas, cada uma com `faixas` arquivos .mp3 curtos (áudio de teste
gerado pelo GStreamer). A mistura imita o acervo descrito no CLAUDE.md:
- cerca de 80% dos discos com tags completas (artista, álbum, número, título);
- o resto com nomes como "Faixa 01" ou só o título, sem tag de álbum;
- capas: embutida, `folder.jpg` ou nenhuma (a interface desenha a substituta);
- algumas coletâneas ("Vários artistas") e músicas repetidas em discos diferentes.
O resultado é sempre o mesmo para a mesma semente.
"""

import argparse
import random
import shutil
import sys
import tempfile
from pathlib import Path

import gi
import mutagen
from mutagen.id3 import APIC, ID3

gi.require_version("Gst", "1.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, Gst  # noqa: E402

Gst.init(None)

ARTISTAS = [
    "Zeca Pagodinho", "Elis Regina", "Roberto Carlos", "Dalva de Oliveira", "Nelson Gonçalves",
    "Cartola", "Clara Nunes", "Altemar Dutra", "Agnaldo Timóteo", "Maria Bethânia",
    "Luiz Gonzaga", "Dorival Caymmi", "Ângela Maria", "Tom Jobim", "Jair Rodrigues",
    "Trio Parada Dura", "Orquestra Tabajara", "Vicente Celestino", "Francisco Alves", "Gal Costa",
]
PALAVRAS = ["Saudade", "Domingo", "Chuva", "Violão", "Estrela", "Cartas", "Seresta", "Laranjeira",
            "Bolero", "Samba", "Ponteio", "Lua", "Retrato", "Acácias", "Colheita", "Maria",
            "Verão", "Viola", "Tarde", "Mesa", "Terreiro", "Baile", "Vela", "Caminho"]
CORES = [0x8A2D12FF, 0x1F4D6BFF, 0x6B1F4DFF, 0x1F5A2EFF, 0x5A3A12FF, 0x3B2D6BFF]


def _gerar_audio_base(destino: Path) -> None:
    pipeline = Gst.parse_launch(
        "audiotestsrc num-buffers=4 samplesperbuffer=1024 ! audioconvert ! audioresample ! "
        f'lamemp3enc ! filesink location="{destino}"')
    pipeline.set_state(Gst.State.PLAYING)
    pipeline.get_bus().timed_pop_filtered(10 * Gst.SECOND, Gst.MessageType.EOS | Gst.MessageType.ERROR)
    pipeline.set_state(Gst.State.NULL)


def _imagem_jpeg(cor: int) -> bytes:
    pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 200, 200)
    pixbuf.fill(cor)
    with tempfile.TemporaryDirectory() as pasta:
        arquivo = Path(pasta) / "capa.jpg"
        pixbuf.savev(str(arquivo), "jpeg", [], [])
        return arquivo.read_bytes()


def _titulo(aleatorio: random.Random) -> str:
    return f"{aleatorio.choice(PALAVRAS)} {aleatorio.choice(PALAVRAS).lower()}"


def gerar(destino: Path, discos: int = 80, faixas: int = 10, semente: int = 1) -> int:
    """Cria a coleção em `destino` e devolve quantos arquivos de áudio foram criados."""
    aleatorio = random.Random(semente)
    destino.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporaria:
        base = Path(temporaria) / "base.mp3"
        _gerar_audio_base(base)
        total = 0
        for n in range(discos):
            artista = aleatorio.choice(ARTISTAS)
            nome_do_disco = f"{aleatorio.choice(PALAVRAS)} e {aleatorio.choice(PALAVRAS)} {n + 1}"
            coletanea = n % 9 == 8
            sem_tags = n % 5 == 4                      # ~20% sem tags completas
            pasta = destino / (f"CD {n + 1:02d}" if sem_tags else f"{artista} - {nome_do_disco}")
            pasta.mkdir(parents=True, exist_ok=True)
            capa = n % 10 in (0, 1, 2, 3)              # 40% com capa embutida
            capa_na_pasta = n % 10 in (4, 5, 6)        # 30% com folder.jpg; 30% sem capa
            jpeg = _imagem_jpeg(CORES[n % len(CORES)])
            for k in range(1, faixas + 1):
                titulo = _titulo(aleatorio) if k % 4 else f"Saudade {k}"     # repete títulos
                arquivo = pasta / (f"Faixa {k:02d}.mp3" if sem_tags else f"{k:02d} - {titulo}.mp3")
                shutil.copyfile(base, arquivo)
                if not sem_tags:
                    tags = mutagen.File(arquivo, easy=True)
                    tags.add_tags()
                    tags["title"] = titulo
                    tags["album"] = nome_do_disco
                    tags["tracknumber"] = str(k)
                    tags["artist"] = aleatorio.choice(ARTISTAS) if coletanea else artista
                    tags["albumartist"] = "Vários artistas" if coletanea else artista
                    tags.save()
                    if capa:
                        id3 = ID3(arquivo)
                        id3.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Capa", data=jpeg))
                        id3.save()
                total += 1
            if capa_na_pasta:
                (pasta / "folder.jpg").write_bytes(jpeg)
    return total


def main(argumentos: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analisador.add_argument("destino", type=Path)
    analisador.add_argument("--discos", type=int, default=80)
    analisador.add_argument("--faixas", type=int, default=10)
    analisador.add_argument("--semente", type=int, default=1)
    args = analisador.parse_args(argumentos)
    total = gerar(args.destino, args.discos, args.faixas, args.semente)
    print(f"{total} faixas em {args.discos} discos, em {args.destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
