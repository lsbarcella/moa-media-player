# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Garante que todo arquivo-fonte traz o aviso de licença (ADR-0009).

Se este teste falhar, o arquivo novo precisa destas duas linhas no começo
(depois da linha `#!`, se houver):

    # SPDX-License-Identifier: GPL-3.0-or-later
    # Copyright (C) 2026 Leonardo dos Santos Barcella
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTAS = ("moa", "tests", "tools")
EXTENSOES = {".py", ".sh"}
ESPERADO = (
    "SPDX-License-Identifier: GPL-3.0-or-later",
    "Copyright (C) 2026 Leonardo dos Santos Barcella",
)


def _arquivos_fonte():
    for pasta in PASTAS:
        for caminho in sorted((RAIZ / pasta).rglob("*")):
            if caminho.suffix in EXTENSOES and "__pycache__" not in caminho.parts:
                yield caminho


def test_todo_arquivo_fonte_tem_o_aviso_de_licenca():
    sem_aviso = []
    for caminho in _arquivos_fonte():
        comeco = "\n".join(caminho.read_text(encoding="utf-8").splitlines()[:6])
        if not all(trecho in comeco for trecho in ESPERADO):
            sem_aviso.append(str(caminho.relative_to(RAIZ)))
    assert not sem_aviso, f"arquivos sem o aviso de licença: {sem_aviso}"


def test_o_arquivo_de_licenca_e_o_texto_oficial_da_gpl_v3():
    texto = (RAIZ / "LICENSE").read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in texto and "Version 3, 29 June 2007" in texto
