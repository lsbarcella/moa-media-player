# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes do Player (M2). Usam `fakesink` no lugar da placa de som."""

import logging
import time

import gi
import pytest

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst  # noqa: E402

import moa.core.player as player_mod  # noqa: E402
from moa.core.player import (  # noqa: E402
    DEGRAU_MAXIMO, DEGRAU_PADRAO, GANHOS_NEUTROS, GANHOS_VOZ_MAIS_CLARA,
    Estado, Player, ganho_do_degrau,
)


def _sink_rapido():
    """Toca o mais rápido possível (não espera o relógio): bom para avançar faixas."""
    sink = Gst.ElementFactory.make("fakesink")
    sink.set_property("sync", False)
    return sink


def _sink_no_relogio():
    """Toca em tempo real: necessário para pausar e medir a posição."""
    sink = Gst.ElementFactory.make("fakesink")
    sink.set_property("sync", True)
    return sink


def esperar(condicao, limite=8.0):
    """Gira o laço de eventos do GLib até a condição valer (ou o tempo acabar).

    O GStreamer só entrega as mensagens (fim da faixa, erro...) quando esse laço
    roda. No app é o laço do GTK; nos testes giramos na mão.
    """
    contexto = GLib.MainContext.default()
    fim = time.monotonic() + limite
    while time.monotonic() < fim:
        while contexto.iteration(False):
            pass
        if condicao():
            return True
        time.sleep(0.01)
    return False


class Registro:
    """Anota tudo o que o player avisa, para os testes conferirem."""

    def __init__(self, p: Player):
        self.estados, self.faixas, self.fins, self.erros = [], [], [], []
        p.on_state = self.estados.append
        p.on_track = self.faixas.append
        p.on_disc_end = lambda: self.fins.append(True)
        p.on_track_error = self.erros.append


@pytest.fixture
def disco(make_track, tmp_path):
    return [make_track(tmp_path / "cd", f"{n:02d}.mp3", title=f"Faixa {n}") for n in (1, 2, 3)]


@pytest.fixture
def player_rapido():
    p = Player(sink_factory=_sink_rapido)
    yield p
    p.encerrar()


@pytest.fixture
def player_relogio():
    p = Player(sink_factory=_sink_no_relogio)
    yield p
    p.encerrar()


# -- máquina de estados --------------------------------------------------------

def test_comeca_parado_e_voz_mais_clara_desligada(player_rapido):
    assert player_rapido.estado == Estado.PARADO
    assert player_rapido.voz_mais_clara is False
    assert player_rapido.degrau_de_volume == DEGRAU_PADRAO == 6


def test_toca_o_disco_inteiro_e_termina_uma_vez(player_rapido, disco):
    registro = Registro(player_rapido)
    player_rapido.carregar(disco)
    assert esperar(lambda: registro.fins)
    assert registro.faixas == [0, 1, 2]
    assert registro.fins == [True]
    assert player_rapido.estado == Estado.PARADO
    assert registro.estados[0] == Estado.TOCANDO and registro.estados[-1] == Estado.PARADO


def test_proxima_na_ultima_faixa_para_sem_quebrar(player_rapido, disco):
    registro = Registro(player_rapido)
    player_rapido.carregar(disco, indice=2, tocar=False)
    player_rapido.proxima()
    assert player_rapido.estado == Estado.PARADO
    assert registro.fins == [True]


def test_tocar_depois_do_fim_recomeca_na_faixa_1(player_rapido, disco):
    registro = Registro(player_rapido)
    player_rapido.carregar(disco)
    assert esperar(lambda: registro.fins)
    player_rapido.tocar()
    assert player_rapido.estado == Estado.TOCANDO
    assert player_rapido.indice == 0


def test_anterior_na_primeira_faixa_reinicia_a_faixa(player_rapido, disco):
    registro = Registro(player_rapido)
    player_rapido.carregar(disco, tocar=False)
    player_rapido.anterior()
    assert player_rapido.indice == 0
    assert registro.faixas == [0, 0]       # abriu de novo a mesma faixa


def test_anterior_volta_uma_faixa(player_rapido, disco):
    player_rapido.carregar(disco, indice=2, tocar=False)
    player_rapido.anterior()
    assert player_rapido.indice == 1


def test_ir_para_faixa_fora_do_intervalo_e_ignorado(player_rapido, disco):
    registro = Registro(player_rapido)
    player_rapido.carregar(disco, tocar=False)
    player_rapido.ir_para(7)
    player_rapido.ir_para(-1)
    assert player_rapido.indice == 0
    assert registro.faixas == [0]


def test_disco_vazio_nao_quebra(player_rapido):
    player_rapido.carregar([])
    player_rapido.tocar()
    player_rapido.proxima()
    player_rapido.anterior()
    assert player_rapido.estado == Estado.PARADO


# -- pausa e posição -------------------------------------------------------------

def test_pausar_e_tocar_mantem_a_posicao(player_relogio, faixa_longa):
    player_relogio.carregar([faixa_longa])
    assert esperar(lambda: (player_relogio.posicao() or 0) > 0.4)
    player_relogio.pausar()
    assert player_relogio.estado == Estado.PAUSADO
    # Dá tempo de o GStreamer assentar e mede duas vezes: pausado, a posição não anda.
    esperar(lambda: False, limite=0.3)
    antes = player_relogio.posicao()
    esperar(lambda: False, limite=0.5)
    assert player_relogio.posicao() == pytest.approx(antes, abs=0.05)
    player_relogio.tocar()
    assert player_relogio.estado == Estado.TOCANDO
    assert esperar(lambda: (player_relogio.posicao() or 0) > antes + 0.3)


def test_retomar_de_onde_parou_fica_pausado_no_ponto(player_relogio, faixa_longa):
    player_relogio.carregar([faixa_longa], indice=0, posicao=2.0, tocar=False)
    assert player_relogio.estado == Estado.PAUSADO
    assert esperar(lambda: (player_relogio.posicao() or 0) >= 1.8)
    assert player_relogio.posicao() == pytest.approx(2.0, abs=0.3)
    assert player_relogio.duracao() == pytest.approx(4.6, abs=0.3)


# -- volume ----------------------------------------------------------------------

def test_degraus_de_volume():
    ganhos = [ganho_do_degrau(n) for n in range(DEGRAU_MAXIMO + 1)]
    assert ganhos[0] == 0.0                      # degrau 0 silencia
    assert ganhos[10] == 1.0                     # degrau 10 é o máximo
    assert max(ganhos) <= 1.0                    # nunca amplifica
    assert all(a < b for a, b in zip(ganhos, ganhos[1:]))   # estritamente crescentes
    assert ganho_do_degrau(99) == 1.0 and ganho_do_degrau(-5) == 0.0


def test_o_elemento_volume_recebe_o_ganho_e_nunca_passa_de_1(player_rapido):
    for degrau, esperado in ((0, 0.0), (6, 0.216), (10, 1.0), (50, 1.0), (-3, 0.0)):
        player_rapido.definir_degrau_de_volume(degrau)
        assert player_rapido._volume.get_property("volume") == pytest.approx(esperado)
        assert player_rapido._volume.get_property("volume") <= 1.0


# -- "Voz mais clara" --------------------------------------------------------------

def test_voz_mais_clara_muda_os_ganhos_do_equalizador(player_rapido):
    equalizador = player_rapido._equalizador
    leitura = lambda: tuple(equalizador.get_property(b) for b in ("band0", "band1", "band2"))
    assert leitura() == GANHOS_NEUTROS
    player_rapido.definir_voz_mais_clara(True)
    assert leitura() == GANHOS_VOZ_MAIS_CLARA
    player_rapido.definir_voz_mais_clara(False)
    assert leitura() == GANHOS_NEUTROS


def test_sem_o_plugin_do_equalizador_toca_e_registra_no_log(monkeypatch, caplog, disco):
    original = player_mod._criar_elemento
    monkeypatch.setattr(player_mod, "_criar_elemento",
                        lambda nome: None if nome == "equalizer-3bands" else original(nome))
    with caplog.at_level(logging.WARNING):
        p = Player(sink_factory=_sink_rapido)
    try:
        registro = Registro(p)
        p.definir_voz_mais_clara(True)          # sem equalizador: não pode quebrar
        p.carregar(disco)
        assert esperar(lambda: registro.fins)
        assert "equalizer-3bands" in caplog.text
    finally:
        p.encerrar()


# -- erros -----------------------------------------------------------------------

def test_faixa_corrompida_no_meio_pula_para_a_proxima(player_rapido, disco):
    disco[1].write_bytes(b"isto nao e audio")
    registro = Registro(player_rapido)
    player_rapido.carregar(disco)
    assert esperar(lambda: registro.fins)
    assert registro.erros == [1]
    assert registro.faixas == [0, 1, 2]          # a faixa 3 tocou mesmo assim


def test_ultima_faixa_corrompida_para_sem_excecao(player_rapido, disco):
    disco[2].write_bytes(b"isto nao e audio")
    registro = Registro(player_rapido)
    player_rapido.carregar(disco)
    assert esperar(lambda: registro.fins)
    assert registro.erros == [2]
    assert player_rapido.estado == Estado.PARADO


# -- buscar um ponto da faixa (barra de progresso clicável) --------------------------------

def test_buscar_leva_a_posicao_para_o_ponto_pedido(player_relogio, faixa_longa):
    player_relogio.carregar([faixa_longa])
    assert esperar(lambda: (player_relogio.duracao() or 0) > 1)
    player_relogio.buscar(2.5)
    assert esperar(lambda: (player_relogio.posicao() or 0) >= 2.4)
    assert player_relogio.posicao() == pytest.approx(2.6, abs=0.6)
    assert player_relogio.estado == Estado.TOCANDO              # buscar não pausa nem para


def test_buscar_com_a_faixa_pausada_continua_pausada(player_relogio, faixa_longa):
    player_relogio.carregar([faixa_longa], tocar=False)
    assert esperar(lambda: (player_relogio.duracao() or 0) > 1)
    player_relogio.buscar(3.0)
    assert esperar(lambda: abs((player_relogio.posicao() or 0) - 3.0) < 0.4)
    assert player_relogio.estado == Estado.PAUSADO


def test_buscar_alem_do_fim_ou_antes_do_inicio_fica_dentro_da_faixa(player_relogio, faixa_longa):
    player_relogio.carregar([faixa_longa], tocar=False)
    assert esperar(lambda: (player_relogio.duracao() or 0) > 1)
    player_relogio.buscar(999)
    assert esperar(lambda: (player_relogio.posicao() or 0) > 3.5)
    player_relogio.buscar(-5)
    assert esperar(lambda: (player_relogio.posicao() if player_relogio.posicao() is not None else 99) < 0.4)


def test_buscar_sem_disco_nao_quebra(player_relogio):
    player_relogio.buscar(3.0)                                  # nada carregado: ignora em silêncio
    assert player_relogio.estado == Estado.PARADO
