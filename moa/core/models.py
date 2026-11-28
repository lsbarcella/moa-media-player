# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Modelos de dados da biblioteca: uma faixa e um disco.

Sem GTK. São só dados e regras de ordenação, fáceis de testar.
"""

from dataclasses import dataclass
from pathlib import Path

from moa.core.textutil import natural_key

# Nome usado para coletâneas, em que as faixas são de artistas diferentes.
VARIOS_ARTISTAS = "Vários artistas"


@dataclass(frozen=True)
class Track:
    """Uma música: um arquivo de áudio dentro de um disco.

    Em TypeScript isto seria uma `interface` com campos `readonly`. O
    `frozen=True` faz o mesmo: depois de criada, a faixa não muda.

    A identidade da faixa é o caminho do arquivo. A mesma música em dois CDs
    são duas faixas diferentes, cada uma no seu disco.
    """

    path: Path
    title: str
    number: int | None = None   # número da faixa no disco, se a tag existir
    artist: str | None = None   # artista da faixa, se a tag existir
    album: str | None = None    # nome do álbum segundo a tag, se existir
    album_artist: str | None = None   # artista do álbum segundo a tag, se existir
    year: int | None = None     # ano de lançamento segundo a tag de data, se existir
    mtime: float = 0.0          # data de modificação do arquivo (para o cache)
    size: int = 0               # tamanho do arquivo em bytes (para o cache)

    @property
    def sort_key(self):
        """Ordem das faixas dentro do disco.

        Primeiro as que têm número, pelo número. Depois as que não têm,
        pela ordem natural do nome do arquivo ("Faixa 2" antes de "Faixa 10").
        """
        return (self.number is None, self.number or 0, natural_key(self.path.name))


@dataclass(frozen=True)
class Album:
    """Um disco: uma pasta com arquivos de áudio.

    Na tela o idoso vê "disco", e aqui no código usamos `Album`, que é o
    nome do ecossistema de música.
    """

    folder: Path
    title: str
    artist: str | None = None   # None quando nenhuma tag de artista foi encontrada
    tracks: tuple[Track, ...] = ()   # uma tupla é como um array `readonly`
    year: int | None = None     # ano do disco: o das tags (ou, sem tag, o do MusicBrainz)

    @property
    def id(self) -> str:
        """Identificador estável do disco: o caminho da pasta."""
        return str(self.folder)

    @property
    def sort_key(self):
        """Ordem dos discos na estante: por artista e depois por álbum.

        Sem artista, o disco é ordenado pelo próprio nome (que vem da pasta
        quando a tag falta). Coletâneas ficam em "Vários artistas".
        """
        return (natural_key(self.artist or self.title), natural_key(self.title))


@dataclass(frozen=True)
class MixDisc:
    """Um disco montado pelo usuário: referências a faixas de outros discos (KTD9).

    É VIRTUAL: guarda só os caminhos das faixas, nunca copia arquivos. Tem a mesma
    "cara" de um `Album` para a estante, o rádio e a busca (id, título, artista,
    faixas, ordem), mas não tem pasta.
    """

    id: str
    title: str
    tracks: tuple[Track, ...] = ()
    artist: str | None = None
    year: int | None = None     # uma playlist não tem ano (mas tem a mesma "cara" de um Album)

    @property
    def sort_key(self):
        return (natural_key(self.title), natural_key(self.title))

    @property
    def eh_montado(self) -> bool:
        return True
