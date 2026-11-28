# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes do rádio (M3): as frases do visor e as regras, sem janela."""

import pytest

from moa.core.config import Config, Preferencias, carregar
from moa.core.db import Database
from moa.core.library import scan
from moa.core.models import Album, Track
from moa.core.player import Player
from moa.core.radio import MSG_ERRO_NA_FAIXA, MSG_FIM_DO_DISCO, Radio, formatar_tempo
from moa.core.state import Memoria
from tests.test_player import _sink_no_relogio, _sink_rapido, esperar


@pytest.fixture
def disco(make_track, tmp_path):
    pasta = tmp_path / "musica" / "Boleros"
    for n in (1, 2, 3):
        make_track(pasta, f"{n:02d}.mp3", title=f"Música {n}", album="Boleros", tracknumber=str(n))
    return scan(tmp_path / "musica")[0]


@pytest.fixture
def radio(tmp_path):
    banco = Database(tmp_path / "moa.db")
    prefs = Preferencias(tmp_path / "config.json")
    r = Radio(Player(sink_factory=_sink_rapido), Memoria(banco), prefs)
    yield r
    r.player.encerrar()
    banco.close()


def test_formatar_tempo():
    assert formatar_tempo(None) == "" and formatar_tempo(83.9) == "1:23" and formatar_tempo(5) == "0:05"


def test_sem_disco_nao_ha_visor(radio):
    assert radio.visor() is None


def test_visor_diz_o_estado_em_palavras(radio, disco):
    radio.abrir_disco(disco, indice=1, tocar=False)
    v = radio.visor()
    assert v.palavra == "PAUSADO" and v.linha_de_estado == "PAUSADO. Aperte Tocar para continuar"
    assert (v.titulo, v.disco, v.faixa) == ("Música 2", "Boleros", "Faixa 2 de 3")
    assert not v.luz_acesa
    radio.alternar()
    v = radio.visor()
    assert v.palavra == "TOCANDO" and v.linha_de_estado == "TOCANDO: Faixa 2 de 3" and v.luz_acesa


def test_volume_no_maximo_avisa_sem_mudar_e_no_minimo_tambem(radio, disco):
    radio.abrir_disco(disco, tocar=False)
    radio.player.definir_degrau_de_volume(10)
    radio.volume_mais()
    assert radio.nota == "O volume já está no máximo." and radio.player.degrau_de_volume == 10
    radio.player.definir_degrau_de_volume(0)
    radio.volume_menos()
    assert radio.nota == "O volume já está no mínimo." and radio.player.degrau_de_volume == 0


def test_volume_mostra_a_ultima_acao_e_e_lembrado(radio, disco):
    radio.abrir_disco(disco, tocar=False)
    radio.volume_mais()
    assert radio.nota == "Volume mais alto (7 de 10)"
    radio.volume_menos()
    radio.volume_menos()
    assert radio.nota == "Volume mais baixo (5 de 10)"
    assert carregar(radio.preferencias._caminho).volume == 5


def test_voz_mais_clara_comeca_desligada_diz_o_estado_e_e_lembrada(radio, disco, tmp_path):
    radio.abrir_disco(disco, tocar=False)
    assert radio.player.voz_mais_clara is False
    radio.alternar_voz_mais_clara()
    assert radio.nota == "Voz mais clara ligada." and radio.player.voz_mais_clara
    # Reabre o "app": um rádio novo lê a preferência gravada.
    outro = Radio(Player(sink_factory=_sink_rapido), radio.memoria, Preferencias(tmp_path / "config.json"))
    try:
        assert outro.player.voz_mais_clara is True
    finally:
        outro.player.encerrar()


def test_a_mensagem_do_visor_fica_ate_a_proxima_acao(radio, disco):
    radio.abrir_disco(disco, tocar=False)
    radio.volume_mais()
    esperar(lambda: False, limite=0.3)          # o tempo passa, nada acontece
    assert radio.visor().nota == "Volume mais alto (7 de 10)"
    radio.alternar()                              # próxima ação
    assert radio.visor().nota is None


def test_faixa_corrompida_mostra_a_frase_calma_e_toca_a_proxima(radio, disco):
    disco.tracks[1].path.write_bytes(b"nao e audio")
    radio.abrir_disco(disco)
    assert esperar(lambda: radio.nota == MSG_FIM_DO_DISCO)
    assert radio.player.estado.value == "parado"


def test_erro_na_faixa_vira_a_mensagem_calma(radio, disco):
    disco.tracks[0].path.write_bytes(b"nao e audio")
    radio.abrir_disco(disco, tocar=False)
    radio.player.ir_para(0)
    assert esperar(lambda: radio.nota == MSG_ERRO_NA_FAIXA or radio.player.indice > 0)


def test_fim_do_disco_para_diz_a_frase_e_tocar_recomeca(radio, disco):
    radio.abrir_disco(disco)
    assert esperar(lambda: radio.nota == MSG_FIM_DO_DISCO)
    assert radio.visor().palavra == "PARADO"
    radio.alternar()                              # "Tocar" recomeça o disco
    v = radio.visor()
    assert v.linha_de_estado == "TOCANDO: Faixa 1 de 3" and radio.nota is None


def test_abrir_disco_registra_recente_e_guarda_onde_parou(radio, disco):
    radio.abrir_disco(disco, indice=2, tocar=False)
    radio.guardar_posicao()
    onde = radio.memoria.onde_parou({disco.id})
    assert onde is not None and onde.indice == 2
    assert radio.memoria.recentes({disco.id}) == []          # só tocar conta como "ouvido"
    radio.alternar()
    assert radio.memoria.recentes({disco.id}) == [disco.id]


def test_guardar_o_disco_e_parar_esvazia_o_radio(radio, disco):
    radio.abrir_disco(disco)
    radio.guardar_o_disco_e_parar()
    assert radio.visor() is None and not radio.tocando


def test_progresso_e_zero_a_um_e_vazio_sem_disco(radio, disco):
    assert radio.progresso() is None
    radio.abrir_disco(disco, tocar=False)
    assert esperar(lambda: radio.progresso() is not None)
    assert 0.0 <= radio.progresso() <= 1.0


def test_buscar_fracao_move_o_ponto_e_fracao_fora_da_faixa_e_corrigida(tmp_path, faixa_longa):
    """Com um player no relógio e uma faixa de 4,6 s: 0.5 vai para o meio; 7 e -1 ficam dentro da faixa."""
    radio = Radio(Player(sink_factory=_sink_no_relogio), Memoria(Database(tmp_path / "m.db")),
                  Preferencias(tmp_path / "c.json"))
    try:
        d = Album(folder=faixa_longa.parent, title="L", artist=None,
                  tracks=(Track(path=faixa_longa, title="longa", number=1),))
        radio.abrir_disco(d, tocar=False)
        assert esperar(lambda: (radio.player.duracao() or 0) > 1)
        radio.buscar_fracao(0.5)
        assert esperar(lambda: abs((radio.progresso() or 0) - 0.5) < 0.1)
        radio.buscar_fracao(7)
        assert esperar(lambda: (radio.progresso() or 0) > 0.9)
        radio.buscar_fracao(-1)
        assert esperar(lambda: (radio.progresso() if radio.progresso() is not None else 1) < 0.1)
    finally:
        radio.player.encerrar()


def test_buscar_fracao_sem_disco_nao_quebra(radio):
    radio.buscar_fracao(0.5)
    assert radio.progresso() is None
