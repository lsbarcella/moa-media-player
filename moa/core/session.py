# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Estado da sessão: em que tela o idoso está e qual aviso ele está vendo. Sem GTK.

As telas só desenham o que a sessão diz e chamam as ações dela (KTD7). Isso deixa
as regras de navegação e de aviso testáveis sem abrir janela.

Regra de ouro (R15, decisão do autor): um aviso fica na tela até a PRÓXIMA ação
do usuário. Ele não some sozinho, porque cada pessoa lê num ritmo diferente.
A única ação que não apaga o aviso é o "Desfazer" do próprio aviso.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class Tela(Enum):
    ESTANTE = "estante"
    RADIO = "radio"
    PLAYLIST = "playlist"
    CAIXA = "caixa"
    EDITAR = "editar"
    APARELHO_DE_CD = "aparelho_de_cd"
    CONFIGURACOES = "configuracoes"


TITULOS = {
    Tela.ESTANTE: "Minha estante",
    Tela.RADIO: "Tocando agora",
    Tela.PLAYLIST: "Montando um disco novo",
    Tela.CAIXA: "A Caixa",
    Tela.EDITAR: "Mexendo no disco",
    Tela.APARELHO_DE_CD: "Aparelho de CD",
    Tela.CONFIGURACOES: "Configurações",
}


@dataclass(frozen=True)
class Aviso:
    texto: str
    desfazer: Callable[[], None] | None = None   # se existir, o aviso mostra "Desfazer"
    ancora: str | None = None                    # se existir, o aviso aparece na linha dessa faixa
    rotulo_do_desfazer: str = "Desfazer"         # texto do botão ("Como era antes", por exemplo)


class Session:
    def __init__(self) -> None:
        self.tela = Tela.ESTANTE
        self.anterior = Tela.ESTANTE
        self.aviso: Aviso | None = None
        self.falha: str | None = None                # frase calma de uma falha inesperada (M5)
        self.disco_aberto_id: str | None = None      # disco que a tela de editar está mexendo
        self.faixa_do_painel = None                  # faixa cujo painel "+" está aberto (ou None)
        self._ouvintes: list[Callable[[], None]] = []

    # -- quem quer saber quando algo mudou -----------------------------------------

    def ao_mudar(self, funcao: Callable[[], None]) -> None:
        self._ouvintes.append(funcao)

    def _avisar_que_mudou(self) -> None:
        for funcao in list(self._ouvintes):
            funcao()

    # -- navegação -----------------------------------------------------------------

    def ir_para(self, tela: Tela) -> None:
        """Muda de tela. É uma ação do usuário, então apaga o aviso."""
        self.aviso = None
        self.falha = None
        self.faixa_do_painel = None
        if tela != self.tela:
            self.anterior = self.tela
            self.tela = tela
        self._avisar_que_mudou()

    def voltar_para_a_estante(self) -> None:
        self.ir_para(Tela.ESTANTE)

    def voltar(self) -> None:
        """"Voltar para onde eu estava": usado pela tela de Configurações."""
        self.aviso = None
        self.falha = None
        self.tela, self.anterior = self.anterior, Tela.ESTANTE
        self._avisar_que_mudou()

    # -- avisos ----------------------------------------------------------------------

    def acao(self) -> None:
        """Toda ação do usuário chama isto primeiro: o aviso anterior sai."""
        if self.aviso is not None or self.falha is not None:
            self.aviso = None
            self.falha = None
            self._avisar_que_mudou()

    def mostrar_falha(self, texto: str) -> None:
        """Uma falha inesperada: frase calma em qualquer tela, até a próxima ação."""
        self.falha = texto
        self._avisar_que_mudou()

    def mostrar_aviso(self, texto: str, desfazer: Callable[[], None] | None = None,
                      ancora: str | None = None, rotulo_do_desfazer: str = "Desfazer") -> None:
        self.aviso = Aviso(texto, desfazer, ancora, rotulo_do_desfazer)
        self._avisar_que_mudou()

    # -- painel "Colocar em outro disco" (o "+" de cada música) -------------------------

    def abrir_painel_mais(self, faixa) -> None:
        self.aviso = None
        self.faixa_do_painel = faixa
        self._avisar_que_mudou()

    def fechar_painel_mais(self) -> None:
        self.faixa_do_painel = None
        self._avisar_que_mudou()

    def desfazer(self) -> None:
        """Executa o "Desfazer" do aviso atual. Não passa por `acao()` de propósito."""
        aviso, self.aviso = self.aviso, None
        if aviso is not None and aviso.desfazer is not None:
            aviso.desfazer()
        self._avisar_que_mudou()

    # -- o que o cabeçalho mostra ------------------------------------------------------

    @property
    def titulo(self) -> str:
        return TITULOS[self.tela]

    @property
    def texto_de_voltar(self) -> str | None:
        """Texto do botão de voltar; None na Estante (não há para onde voltar)."""
        if self.tela == Tela.ESTANTE:
            return None
        if self.tela == Tela.CONFIGURACOES:
            return "Voltar para onde eu estava"
        return "Voltar para a estante"

    @property
    def mostra_botao_configuracoes(self) -> bool:
        return self.tela != Tela.CONFIGURACOES
