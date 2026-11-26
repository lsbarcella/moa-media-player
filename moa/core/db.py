"""Banco de dados SQLite do Moa (ADR-0008). Sem GTK.

Hoje guarda só o cache da biblioteca (faixas e capas). Nos próximos marcos
entram os discos montados, a Caixa, os recentes e onde o idoso parou, como
novas migrações.

Princípios:
- O banco NUNCA vira mensagem técnica para o idoso (restrição 5). Se o arquivo
  estiver corrompido, ele é guardado ao lado com outro nome e um banco novo é
  criado. O cache se refaz sozinho varrendo as pastas.
- As gravações acontecem dentro de transações: ou entra tudo, ou nada. Isso
  importa num notebook antigo que pode ser desligado de repente.
- Só usamos o `sqlite3` que já vem no Python (sem dependência nova).
"""

import logging
import os
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from moa.core.covers import CoverSource
from moa.core.models import Track

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Migrações: a lista cresce, nunca se edita uma migração que já foi entregue.
# O número da versão fica gravado dentro do próprio arquivo (PRAGMA user_version).
# É como as migrações de banco de um app web, só que sem ferramenta externa.
# ---------------------------------------------------------------------------

def _migracao_1(conexao: sqlite3.Connection) -> None:
    conexao.execute("""
        CREATE TABLE tracks (
            path         TEXT PRIMARY KEY,   -- identidade da faixa: o caminho do arquivo
            mtime        REAL NOT NULL,      -- data de modificação (para saber se mudou)
            size         INTEGER NOT NULL,   -- tamanho em bytes (idem)
            title        TEXT NOT NULL,
            number       INTEGER,
            artist       TEXT,
            album        TEXT,
            album_artist TEXT
        )""")
    conexao.execute("""
        CREATE TABLE covers (
            folder    TEXT PRIMARY KEY,      -- pasta do disco
            signature TEXT NOT NULL,         -- muda quando o disco muda
            kind      TEXT,                  -- 'embedded', 'file' ou NULL (sem capa)
            path      TEXT,                  -- de onde vem a capa
            thumbnail TEXT                   -- miniatura pronta, ou NULL
        )""")


MIGRACOES = [_migracao_1]


class EsquemaMaisNovoQueOApp(Exception):
    """O arquivo foi criado por uma versão mais nova do app."""


@dataclass(frozen=True)
class CoverRecord:
    """O que o cache sabe sobre a capa de um disco."""

    signature: str
    source: CoverSource | None      # None: o disco não tem capa (usa a substituta)
    thumbnail: Path | None          # None: não há miniatura (usa a substituta)


class Database:
    def __init__(self, caminho: Path | str, timeout: float = 5.0):
        # isolation_level=None: nós mesmos abrimos e fechamos as transações
        # (ver `_transacao`), em vez de deixar o Python decidir quando.
        # timeout: quanto esperar se outro processo estiver usando o banco.
        self._conexao = sqlite3.connect(str(caminho), timeout=timeout, isolation_level=None)
        try:
            self._migrar()
        except BaseException:
            self._conexao.close()
            raise

    @classmethod
    def open(cls, caminho: Path | str, timeout: float = 5.0) -> "Database":
        """Abre o banco, recuperando-se sozinho de um arquivo corrompido.

        Um arquivo ilegível não é apagado: vai para `<nome>.problema-<hora>`,
        caso valha a pena examiná-lo depois. Já um banco apenas "ocupado"
        (outro processo usando) não é tratado como corrompido.
        """
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        try:
            return cls(caminho, timeout)
        except sqlite3.OperationalError:
            raise                       # ocupado, sem permissão etc.: não é corrupção
        except (sqlite3.DatabaseError, EsquemaMaisNovoQueOApp) as erro:
            guardado = caminho.with_name(f"{caminho.name}.problema-{int(time.time())}")
            log.error("banco ilegível (%s); guardei em %s e vou criar um novo", erro, guardado)
            os.replace(caminho, guardado)
            return cls(caminho, timeout)

    def close(self) -> None:
        self._conexao.close()

    # -- infraestrutura ------------------------------------------------------

    @contextmanager
    def _transacao(self):
        """Tudo o que acontecer dentro do `with` entra junto ou não entra."""
        self._conexao.execute("BEGIN")
        try:
            yield
        except BaseException:
            self._conexao.execute("ROLLBACK")
            raise
        else:
            self._conexao.execute("COMMIT")

    def _migrar(self) -> None:
        versao = self._conexao.execute("PRAGMA user_version").fetchone()[0]
        if versao > len(MIGRACOES):
            raise EsquemaMaisNovoQueOApp(f"versão {versao}, o app conhece até {len(MIGRACOES)}")
        for n in range(versao, len(MIGRACOES)):
            with self._transacao():
                MIGRACOES[n](self._conexao)
                self._conexao.execute(f"PRAGMA user_version = {n + 1}")

    def schema_version(self) -> int:
        return self._conexao.execute("PRAGMA user_version").fetchone()[0]

    def _apagar_exceto(self, tabela: str, coluna: str, valores: Iterable[str]) -> None:
        """Apaga as linhas cuja `coluna` não está em `valores`.

        Usa uma tabela temporária porque o SQLite limita quantos valores cabem
        numa única consulta. (Os nomes de tabela e coluna vêm só do nosso código.)
        """
        with self._transacao():
            self._conexao.execute("CREATE TEMP TABLE IF NOT EXISTS manter(chave TEXT PRIMARY KEY)")
            self._conexao.execute("DELETE FROM manter")
            self._conexao.executemany("INSERT OR IGNORE INTO manter VALUES (?)", ((v,) for v in valores))
            self._conexao.execute(f"DELETE FROM {tabela} WHERE {coluna} NOT IN (SELECT chave FROM manter)")

    # -- cache das faixas ----------------------------------------------------

    def load_tracks(self) -> dict[str, Track]:
        """Todas as faixas do cache, pelo caminho. Para 800 faixas leva ~1 ms."""
        linhas = self._conexao.execute(
            "SELECT path, mtime, size, title, number, artist, album, album_artist FROM tracks")
        return {
            caminho: Track(path=Path(caminho), mtime=mtime, size=tamanho, title=titulo,
                           number=numero, artist=artista, album=album, album_artist=artista_album)
            for caminho, mtime, tamanho, titulo, numero, artista, album, artista_album in linhas
        }

    def save_tracks(self, faixas: Iterable[Track]) -> None:
        """Grava as faixas (as que já existem são substituídas), numa transação."""
        with self._transacao():
            self._conexao.executemany(
                "INSERT OR REPLACE INTO tracks VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ((str(t.path), t.mtime, t.size, t.title, t.number, t.artist, t.album, t.album_artist)
                 for t in faixas))

    def delete_tracks_except(self, caminhos: Iterable[str]) -> None:
        """Esquece as faixas que não estão mais na pasta de música."""
        self._apagar_exceto("tracks", "path", caminhos)

    # -- cache das capas -----------------------------------------------------

    def get_cover(self, pasta: str) -> CoverRecord | None:
        linha = self._conexao.execute(
            "SELECT signature, kind, path, thumbnail FROM covers WHERE folder = ?", (pasta,)).fetchone()
        if linha is None:
            return None
        assinatura, tipo, caminho, miniatura = linha
        fonte = CoverSource(tipo, Path(caminho)) if tipo else None
        return CoverRecord(assinatura, fonte, Path(miniatura) if miniatura else None)

    def save_cover(self, pasta: str, assinatura: str, fonte: CoverSource | None,
                   miniatura: Path | None) -> None:
        with self._transacao():
            self._conexao.execute(
                "INSERT OR REPLACE INTO covers VALUES (?, ?, ?, ?, ?)",
                (pasta, assinatura, fonte.kind if fonte else None,
                 str(fonte.path) if fonte else None, str(miniatura) if miniatura else None))

    def delete_covers_except(self, pastas: Iterable[str]) -> None:
        self._apagar_exceto("covers", "folder", pastas)
