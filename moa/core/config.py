# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Preferências do próprio usuário, em JSON (ADR-0006 e ADR-0008). Sem GTK.

O JSON guarda só o que é legível e pequeno: tamanho da letra, paleta de cores,
"Voz mais clara" e o degrau do volume. Todo o resto mora no SQLite.

A gravação é atômica: escrevemos num arquivo temporário e depois trocamos pelo
definitivo. Se a energia cair no meio, o arquivo antigo continua inteiro.
Um JSON ausente ou corrompido volta aos padrões, sem erro para o idoso.
"""

import json
import logging
import os
import tempfile
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from gi.repository import GLib

from moa.core.player import DEGRAU_MAXIMO, DEGRAU_PADRAO

log = logging.getLogger(__name__)

LETRAS = ("normal", "grande", "maior")
PALETAS = ("normal", "vermelho-verde", "azul-amarelo", "preto-e-branco")


@dataclass(frozen=True)
class Config:
    letra: str = "normal"
    paleta: str = "normal"
    voz_mais_clara: bool = False        # ADR-0004: começa desligada
    volume: int = DEGRAU_PADRAO         # degrau de 0 a 10

    def com(self, **mudancas) -> "Config":
        return replace(self, **mudancas)


def caminho_padrao() -> Path:
    return Path(GLib.get_user_config_dir()) / "moa" / "config.json"


def _validar(bruto: dict) -> Config:
    """Aproveita cada valor válido e troca os inválidos pelo padrão do campo."""
    padrao = Config()
    letra = bruto.get("letra")
    paleta = bruto.get("paleta")
    voz = bruto.get("voz_mais_clara")
    volume = bruto.get("volume")
    return Config(
        letra=letra if letra in LETRAS else padrao.letra,
        paleta=paleta if paleta in PALETAS else padrao.paleta,
        voz_mais_clara=voz if isinstance(voz, bool) else padrao.voz_mais_clara,
        volume=(volume if isinstance(volume, int) and not isinstance(volume, bool)
                and 0 <= volume <= DEGRAU_MAXIMO else padrao.volume),
    )


def carregar(caminho: Path | None = None) -> Config:
    caminho = caminho or caminho_padrao()
    try:
        texto = caminho.read_text(encoding="utf-8")
    except FileNotFoundError:
        return Config()
    except OSError as erro:
        log.warning("não consegui ler %s: %s", caminho, erro)
        return Config()
    try:
        bruto = json.loads(texto)
        if not isinstance(bruto, dict):
            raise ValueError("o JSON não é um objeto")
    except ValueError as erro:
        guardado = caminho.with_name(f"{caminho.name}.problema-{int(time.time())}")
        log.error("configuração ilegível (%s); guardei em %s e voltei aos padrões", erro, guardado)
        try:
            os.replace(caminho, guardado)
        except OSError as erro_ao_mover:
            log.warning("não consegui guardar o arquivo ruim: %s", erro_ao_mover)
        return Config()
    return _validar(bruto)


def salvar(config: Config, caminho: Path | None = None) -> None:
    """Grava com troca atômica. Se falhar, o arquivo antigo fica como estava."""
    caminho = caminho or caminho_padrao()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    descritor, temporario = tempfile.mkstemp(dir=caminho.parent, prefix=".config-", suffix=".tmp")
    try:
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            json.dump(asdict(config), arquivo, ensure_ascii=False, indent=2)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
    except BaseException:
        try:
            os.unlink(temporario)
        except OSError:
            pass
        raise


class Preferencias:
    """A configuração atual + onde ela mora. Quem muda uma opção chama `mudar`.

    Grava na hora (troca atômica) e avisa quem quer saber (por exemplo, a janela,
    que troca o tema). Se a gravação falhar, o app segue com o valor na memória.
    """

    def __init__(self, caminho: Path | None = None):
        self._caminho = caminho or caminho_padrao()
        self.config = carregar(self._caminho)
        self._ouvintes = []

    def ao_mudar(self, funcao) -> None:
        self._ouvintes.append(funcao)

    def mudar(self, **mudancas) -> None:
        self.config = _validar({**asdict(self.config), **mudancas})
        try:
            salvar(self.config, self._caminho)
        except OSError as erro:
            log.warning("não consegui gravar as preferências: %s", erro)
        for funcao in list(self._ouvintes):
            funcao()
