# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Varre a pasta de música e monta discos e faixas, com os fallbacks do projeto.

Sem GTK. Este módulo nunca levanta erro por causa de um arquivo estranho:
o idoso não pode ver uma mensagem técnica (restrição 5). Problemas vão para o
log, e o arquivo problemático cai nos fallbacks.

Ordem de preferência para cada informação (CLAUDE.md, seção 8):
1. tags do arquivo, lidas com mutagen;
2. estrutura de pastas: pasta = disco, e o nome da pasta vira o nome do álbum
   quando a tag falta;
3. nome do arquivo: "Faixa 01" vira "Faixa 1"; "05 - Título" vira "Título".
"""

import logging
import os
import re
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import mutagen

from moa.core.models import VARIOS_ARTISTAS, Album, Track
from moa.core.textutil import fold

if TYPE_CHECKING:       # só para o editor entender o tipo; evita importação circular
    from moa.core.db import Database

log = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {".mp3", ".flac", ".ogg", ".oga", ".m4a", ".wav"}

_SO_NUMERO = re.compile(r"^0*(\d+)$")
_FAIXA_N = re.compile(r"^faixa\s*0*(\d+)$", re.IGNORECASE)
_NUMERO_E_TITULO = re.compile(r"^0*(\d+)\s*[-._)]+\s*(.+)$")
_PRIMEIRO_NUMERO = re.compile(r"\d+")

# Formas comuns de escrever "coletânea" nas tags (já sem acento nem caixa).
_NOMES_DE_COLETANEA = {
    "various artists", "varios artistas", "artistas diversos", "diversos", "va", "v.a.",
}


# ---------------------------------------------------------------------------
# Fallbacks a partir do nome do arquivo
# ---------------------------------------------------------------------------

def title_from_filename(stem: str) -> tuple[str, int | None]:
    """Tira título e número do nome do arquivo (sem a extensão).

    "Faixa 01"          -> ("Faixa 1", 1)
    "01"                -> ("Faixa 1", 1)
    "05 - Samba Bom"    -> ("Samba Bom", 5)
    "Samba Bom"         -> ("Samba Bom", None)
    """
    stem = stem.strip()
    for padrao in (_FAIXA_N, _SO_NUMERO):
        achou = padrao.match(stem)
        if achou:
            numero = int(achou.group(1))
            return f"Faixa {numero}", numero
    achou = _NUMERO_E_TITULO.match(stem)
    if achou:
        return achou.group(2).strip(), int(achou.group(1))
    return stem.replace("_", " ").strip() or stem, None


def _parse_number(valor: str | None) -> int | None:
    """"3", "03" e "3/12" viram 3. Qualquer outra coisa vira None."""
    if not valor:
        return None
    achou = _PRIMEIRO_NUMERO.search(valor)
    return int(achou.group()) if achou else None


# ---------------------------------------------------------------------------
# Leitura das tags
# ---------------------------------------------------------------------------

def _open_tags(path: Path):
    """Abre as tags do arquivo, ou devolve None se não der."""
    try:
        arquivo = mutagen.File(path, easy=True)
    except Exception as erro:  # o mutagen pode levantar vários tipos de erro
        log.warning("não consegui ler as tags de %s: %s", path, erro)
        return None
    return None if arquivo is None else arquivo.tags


def _tag(tags, *chaves: str) -> str | None:
    """Primeiro valor não vazio entre as chaves, ou None.

    Cada formato usa nomes diferentes: o modo "easy" do mutagen usa "title",
    mas um .wav traz quadros ID3 como "TIT2". Tentamos os dois.
    """
    if not tags:
        return None
    for chave in chaves:
        try:
            valor = tags[chave]
        except (KeyError, ValueError):
            continue
        if hasattr(valor, "text"):        # quadro ID3
            valor = valor.text
        if isinstance(valor, (list, tuple)):
            valor = valor[0] if valor else None
        if valor is None:
            continue
        valor = str(valor).strip()
        if valor:
            return valor
    return None


def read_track(path: Path) -> Track:
    """Lê uma faixa: tags primeiro, nome do arquivo quando a tag falta."""
    estado = path.stat()
    tags = _open_tags(path)

    titulo_do_nome, numero_do_nome = title_from_filename(path.stem)
    numero = _parse_number(_tag(tags, "tracknumber", "TRCK"))

    return Track(
        path=path,
        title=_tag(tags, "title", "TIT2") or titulo_do_nome,
        number=numero if numero is not None else numero_do_nome,
        artist=_tag(tags, "artist", "TPE1"),
        album=_tag(tags, "album", "TALB"),
        album_artist=_tag(tags, "albumartist", "TPE2"),
        mtime=estado.st_mtime,
        size=estado.st_size,
    )


# ---------------------------------------------------------------------------
# Montagem do disco
# ---------------------------------------------------------------------------

def _mais_comum(valores: list[str]) -> str | None:
    """O valor que mais se repete (ignorando acento e caixa), ou None."""
    if not valores:
        return None
    contagem = Counter(fold(v) for v in valores)
    escolhido, _ = contagem.most_common(1)[0]
    return next(v for v in valores if fold(v) == escolhido)


def _artista_do_album(faixas: tuple[Track, ...]) -> str | None:
    """Artista do disco.

    1. A tag "artista do álbum", se existir.
    2. Senão, o artista que aparece em mais da metade das faixas (um convidado
       em uma música não transforma o disco em coletânea).
    3. Se nenhum artista passa da metade, é uma coletânea: "Vários artistas".
    4. Sem nenhuma tag de artista: None (a estante usa o nome do disco).
    """
    do_album = _mais_comum([t.album_artist for t in faixas if t.album_artist])
    if do_album:
        return VARIOS_ARTISTAS if fold(do_album) in _NOMES_DE_COLETANEA else do_album

    artistas = [t.artist for t in faixas if t.artist]
    if not artistas:
        return None
    principal = _mais_comum(artistas)
    if sum(1 for a in artistas if fold(a) == fold(principal)) * 2 > len(faixas):
        return VARIOS_ARTISTAS if fold(principal) in _NOMES_DE_COLETANEA else principal
    return VARIOS_ARTISTAS


def _montar_disco(pasta: Path, faixas: tuple[Track, ...]) -> Album:
    titulo = _mais_comum([t.album for t in faixas if t.album]) or pasta.name
    return Album(folder=pasta, title=titulo, artist=_artista_do_album(faixas), tracks=faixas)


def refresh_library(raiz: Path, db: "Database") -> list[Album]:
    """Varre a pasta de música relendo só o que mudou desde a última vez.

    Para cada arquivo, compara a data de modificação e o tamanho com o que o
    banco guardou. Se são iguais, usa a faixa do cache e NÃO abre o arquivo
    (abrir arquivos é o que custa caro num HD mecânico). Faixas novas ou
    alteradas são lidas e gravadas; faixas que sumiram são esquecidas.

    O resultado é idêntico ao de `scan`, só mais rápido.
    """
    guardadas = db.load_tracks()
    novas: list[Track] = []

    def ler(caminho: Path) -> Track:
        estado = caminho.stat()
        antiga = guardadas.get(str(caminho))
        if antiga is not None and antiga.mtime == estado.st_mtime and antiga.size == estado.st_size:
            return antiga
        faixa = read_track(caminho)
        novas.append(faixa)
        return faixa

    discos = scan(raiz, read=ler)
    db.save_tracks(novas)
    db.delete_tracks_except(str(t.path) for d in discos for t in d.tracks)
    return discos


def scan(raiz: Path, read: Callable[[Path], Track] = read_track) -> list[Album]:
    """Varre a pasta de música e devolve os discos, na ordem da estante.

    Toda pasta que contém arquivos de áudio é um disco, em qualquer
    profundidade (serve para `Música/CD` e para `Música/Artista/Álbum`).
    Pastas sem áudio são ignoradas. Arquivos `.cda` não têm áudio: são
    ignorados e só vão para o log.

    O parâmetro `read` permite trocar o leitor de faixas. A parte 4 do M1 usa
    isso para ler do cache quando o arquivo não mudou.
    """
    raiz = Path(raiz)
    if not raiz.is_dir():
        log.warning("a pasta de música não existe: %s", raiz)
        return []

    discos: list[Album] = []
    for pasta, subpastas, arquivos in os.walk(raiz):
        subpastas[:] = sorted(p for p in subpastas if not p.startswith("."))
        caminhos = []
        for nome in sorted(arquivos):
            if nome.startswith("."):          # arquivos escondidos e lixo de outros sistemas
                continue
            caminho = Path(pasta) / nome
            extensao = caminho.suffix.lower()
            if extensao in AUDIO_EXTENSIONS:
                caminhos.append(caminho)
            elif extensao == ".cda":
                log.info("arquivo .cda ignorado (não contém áudio): %s", caminho)
        if not caminhos:
            continue
        faixas = tuple(sorted((read(c) for c in caminhos), key=lambda t: t.sort_key))
        discos.append(_montar_disco(Path(pasta), faixas))

    return sorted(discos, key=lambda d: d.sort_key)
