# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Instância única (M5): abrir o app de novo não abre uma segunda janela.

Sobe um barramento D-Bus de sessão próprio (`dbus-run-session`), para o teste não
mexer no do usuário nem depender dele. O segundo processo precisa terminar logo
(ele só pede ao primeiro para trazer a janela à frente) e o primeiro segue vivo.
"""

import os
import shutil
import sys
import textwrap
from pathlib import Path

import pytest
import subprocess

from tests.ui_ajuda import tem_display

pytestmark = [
    pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)"),
    pytest.mark.skipif(shutil.which("dbus-run-session") is None, reason="sem dbus-run-session"),
]

RAIZ = Path(__file__).resolve().parent.parent

ROTEIRO = textwrap.dedent("""
    import os, subprocess, sys, time
    from pathlib import Path
    cmd = [sys.executable, "-m", "moa"]
    primeiro = subprocess.Popen(cmd)
    # Espera o primeiro terminar de abrir (o log diz "iniciado"). Num barramento novo isso
    # pode levar vários segundos, porque o GTK tenta ativar serviços que não existem.
    log = Path(os.environ["XDG_DATA_HOME"]) / "moa" / "moa.log"
    limite = time.time() + 40
    while time.time() < limite and not (log.exists() and "iniciado" in log.read_text()):
        assert primeiro.poll() is None, "o primeiro processo morreu"
        time.sleep(0.2)
    time.sleep(1)
    segundo = subprocess.Popen(cmd)
    try:
        codigo = segundo.wait(timeout=20)
    except subprocess.TimeoutExpired:
        segundo.kill(); primeiro.kill()
        print("SEGUNDO_NAO_TERMINOU"); sys.exit(1)
    vivo = primeiro.poll() is None
    primeiro.terminate(); primeiro.wait(timeout=10)
    print(f"SEGUNDO={codigo} PRIMEIRO_VIVO={vivo}")
""")


def test_segunda_abertura_termina_e_a_primeira_continua(tmp_path):
    musica = tmp_path / "musica"
    musica.mkdir()
    ambiente = dict(os.environ, MOA_PASTA_DE_MUSICA=str(musica),
                    XDG_DATA_HOME=str(tmp_path / "dados"), XDG_CONFIG_HOME=str(tmp_path / "config"),
                    PYTHONPATH=str(RAIZ))
    ambiente.pop("DBUS_SESSION_BUS_ADDRESS", None)
    r = subprocess.run(["dbus-run-session", "--", sys.executable, "-c", ROTEIRO],
                       cwd=RAIZ, env=ambiente, capture_output=True, text=True, timeout=90)
    assert "SEGUNDO=0 PRIMEIRO_VIVO=True" in r.stdout, r.stdout + r.stderr
