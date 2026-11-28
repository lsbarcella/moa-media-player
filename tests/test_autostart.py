# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes da abertura automática (M5)."""

from moa.core import autostart


def test_primeira_execucao_cria_o_atalho_com_o_exec_certo(tmp_path):
    config, dados = tmp_path / "config", tmp_path / "dados"
    assert autostart.garantir(config, dados, comando="/usr/bin/moa") is True
    atalho = config / "autostart" / "br.tcc.Moa.desktop"
    texto = atalho.read_text(encoding="utf-8")
    assert "Exec=/usr/bin/moa\n" in texto
    assert "Type=Application" in texto


def test_se_o_usuario_apagar_o_atalho_o_app_nao_o_recria(tmp_path):
    config, dados = tmp_path / "config", tmp_path / "dados"
    autostart.garantir(config, dados, comando="/usr/bin/moa")
    (config / "autostart" / "br.tcc.Moa.desktop").unlink()
    assert autostart.garantir(config, dados, comando="/usr/bin/moa") is False
    assert not (config / "autostart" / "br.tcc.Moa.desktop").exists()


def test_nao_sobrescreve_um_atalho_que_ja_existe(tmp_path):
    config, dados = tmp_path / "config", tmp_path / "dados"
    atalho = config / "autostart" / "br.tcc.Moa.desktop"
    atalho.parent.mkdir(parents=True)
    atalho.write_text("do usuário")
    autostart.garantir(config, dados, comando="/usr/bin/moa")
    assert atalho.read_text() == "do usuário"


def test_sem_o_comando_instalado_nada_e_criado(tmp_path, monkeypatch):
    monkeypatch.setattr(autostart.shutil, "which", lambda _nome: None)
    config, dados = tmp_path / "config", tmp_path / "dados"
    assert autostart.garantir(config, dados) is False
    assert not (config / "autostart").exists()
    assert not (dados / "autostart-criado").exists()   # tenta de novo quando instalarem


def test_falha_de_gravacao_nao_levanta_erro(tmp_path):
    bloqueio = tmp_path / "config"
    bloqueio.write_text("sou um arquivo, não uma pasta")
    assert autostart.garantir(bloqueio, tmp_path / "dados", comando="/usr/bin/moa") is False
