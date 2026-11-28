# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes de "não deixar o notebook dormir enquanto toca" (M5)."""

from moa.ui.inibidor import Inibidor


class AppFalso:
    def __init__(self):
        self.pedidos, self.liberados = [], []

    def inhibit(self, janela, flags, motivo):
        self.pedidos.append(motivo)
        return len(self.pedidos)

    def uninhibit(self, cookie):
        self.liberados.append(cookie)


class RadioFalso:
    def __init__(self):
        self.tocando = False
        self._ouvintes = []

    def ao_mudar(self, f):
        self._ouvintes.append(f)

    def mudar(self, tocando):
        self.tocando = tocando
        for f in self._ouvintes:
            f()


def test_pede_ao_tocar_e_libera_ao_pausar():
    app, radio = AppFalso(), RadioFalso()
    inibidor = Inibidor(app, None, radio)
    radio.mudar(True)
    assert app.pedidos == ["Tocando música"] and inibidor.ativo
    radio.mudar(False)
    assert app.liberados == [1] and not inibidor.ativo


def test_nao_pede_duas_vezes_enquanto_toca():
    app, radio = AppFalso(), RadioFalso()
    Inibidor(app, None, radio)
    radio.mudar(True)
    radio.mudar(True)
    assert len(app.pedidos) == 1


def test_soltar_ao_fechar_so_libera_se_havia_pedido():
    app, radio = AppFalso(), RadioFalso()
    inibidor = Inibidor(app, None, radio)
    inibidor.soltar()
    assert app.liberados == []
    radio.mudar(True)
    inibidor.soltar()
    assert app.liberados == [1]


def test_se_o_sistema_recusar_o_app_segue_sem_erro():
    class AppQuebrado(AppFalso):
        def inhibit(self, *a):
            raise RuntimeError("sem gerenciador de sessão")

    radio = RadioFalso()
    inibidor = Inibidor(AppQuebrado(), None, radio)
    radio.mudar(True)
    assert not inibidor.ativo
