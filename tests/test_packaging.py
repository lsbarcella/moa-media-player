# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Confere o pacote .deb: o que entra, as dependências e se o comando `moa` funciona."""

import shutil
import subprocess
from pathlib import Path

import pytest

import moa

RAIZ = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(shutil.which("dpkg-deb") is None, reason="sem dpkg-deb")


@pytest.fixture(scope="module")
def deb(tmp_path_factory):
    saida = subprocess.run(["bash", str(RAIZ / "tools" / "build_deb.sh")], check=True,
                           capture_output=True, text=True, cwd=RAIZ).stdout
    arquivo = RAIZ / "dist" / f"moa-media-player_{moa.__version__}_all.deb"
    assert arquivo.exists(), saida
    return arquivo


def _dpkg(*args):
    return subprocess.run(["dpkg-deb", *args], check=True, capture_output=True, text=True).stdout


def test_controle_declara_as_dependencias_do_projeto(deb):
    controle = _dpkg("-f", str(deb))
    for pacote in ("python3 (>= 3.10)", "python3-gi", "gir1.2-gtk-3.0", "gir1.2-gstreamer-1.0",
                   "gstreamer1.0-plugins-base", "gstreamer1.0-plugins-good",
                   "python3-mutagen", "libcdparanoia0"):
        assert pacote in controle
    assert f"Version: {moa.__version__}" in controle
    assert "Architecture: all" in controle


def test_conteudo_tem_comando_atalho_icone_e_icones_das_telas(deb):
    arquivos = _dpkg("-c", str(deb))
    for esperado in ("./usr/bin/moa", "./usr/share/applications/br.tcc.Moa.desktop",
                     "./usr/share/icons/hicolor/scalable/apps/br.tcc.Moa.svg",
                     "./usr/lib/moa/moa/__main__.py", "./usr/lib/moa/moa/ui/icons/disco.svg"):
        assert esperado in arquivos
    assert "-rwxr-xr-x root/root" in next(l for l in arquivos.splitlines() if l.endswith("/usr/bin/moa"))


def test_nao_leva_testes_nem_bytecode(deb):
    arquivos = _dpkg("-c", str(deb))
    assert "__pycache__" not in arquivos and "/tests/" not in arquivos and ".pyc" not in arquivos


def test_o_atalho_aponta_para_o_comando_e_o_icone_do_pacote(deb):
    atalho = (RAIZ / "packaging" / "br.tcc.Moa.desktop").read_text(encoding="utf-8")
    assert "Exec=moa" in atalho and "Icon=br.tcc.Moa" in atalho and "Terminal=false" in atalho


def test_o_comando_instalado_importa_o_app_de_qualquer_pasta(deb, tmp_path):
    subprocess.run(["dpkg-deb", "-x", str(deb), str(tmp_path)], check=True)
    comando = (tmp_path / "usr" / "bin" / "moa").read_text(encoding="utf-8")
    assert "PYTHONPATH=/usr/lib/moa" in comando
    resultado = subprocess.run(
        ["python3", "-c", "import moa.app, moa.core.ripper; print(moa.__file__)"],
        cwd="/", capture_output=True, text=True, env={"PATH": "/usr/bin:/bin",
                                                       "PYTHONPATH": str(tmp_path / "usr/lib/moa")})
    assert resultado.returncode == 0, resultado.stderr
    assert str(tmp_path) in resultado.stdout
