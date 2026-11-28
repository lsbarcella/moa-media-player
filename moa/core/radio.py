# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""O "rádio": junta o Player, a memória e as preferências. Sem GTK.

É aqui que moram os TEXTOS do visor ("TOCANDO: Faixa 3 de 8", "Volume mais alto
(7 de 10)"...). A tela só desenha o que o `Visor` diz. Assim as frases que o idoso
lê ficam testáveis sem abrir janela (KTD7).

Regra do autor: a mensagem do visor fica até a próxima ação do usuário.
"""

from dataclasses import dataclass
from typing import Callable

from moa.core.config import Preferencias
from moa.core.player import DEGRAU_MAXIMO, Estado, Player
from moa.core.state import Memoria

MSG_ERRO_NA_FAIXA = "Não consegui tocar esta música. Vou tocar a próxima."
MSG_FIM_DO_DISCO = "Este é o fim do disco."


@dataclass(frozen=True)
class Visor:
    luz_acesa: bool
    palavra: str            # TOCANDO, PAUSADO ou PARADO
    linha_de_estado: str    # frase completa do estado
    titulo: str             # nome da música
    disco: str
    faixa: str              # "Faixa 3 de 8"
    nota: str | None        # última ação ou aviso calmo
    tempo: str              # "1:23 de 3:45" (vazio se ainda não se sabe)
    artista: str | None = None   # artista do disco (tags ou MusicBrainz), se se sabe
    ano: int | None = None       # ano do disco (tags ou MusicBrainz), se se sabe

    @property
    def sobre_o_disco(self) -> str:
        """"Artista · Álbum · Ano", só com o que existe. Artista igual ao álbum não se repete."""
        partes = []
        if self.artista and self.artista.strip().casefold() != self.disco.strip().casefold():
            partes.append(self.artista)
        partes.append(self.disco)
        if self.ano:
            partes.append(str(self.ano))
        return " · ".join(partes)


def formatar_tempo(segundos: float | None) -> str:
    if segundos is None:
        return ""
    total = int(segundos)
    return f"{total // 60}:{total % 60:02d}"


class Radio:
    def __init__(self, player: Player, memoria: Memoria, preferencias: Preferencias):
        self.player = player
        self.memoria = memoria
        self.preferencias = preferencias
        self.disco = None               # Album (ou disco montado) que está no rádio
        self.nota: str | None = None
        self._ouvintes: list[Callable[[], None]] = []

        player.definir_degrau_de_volume(preferencias.config.volume)
        player.definir_voz_mais_clara(preferencias.config.voz_mais_clara)
        player.on_state = lambda _estado: self._mudou()
        player.on_track = lambda _indice: self._mudou()
        player.on_disc_end = self._ao_fim_do_disco
        player.on_track_error = self._ao_erro_na_faixa

    # -- avisos para a tela ----------------------------------------------------------

    def ao_mudar(self, funcao: Callable[[], None]) -> None:
        self._ouvintes.append(funcao)

    def _mudou(self) -> None:
        for funcao in list(self._ouvintes):
            funcao()

    def _ao_fim_do_disco(self) -> None:
        self.nota = MSG_FIM_DO_DISCO
        self.guardar_posicao(inicio=True)
        self._mudou()

    def _ao_erro_na_faixa(self, _indice: int) -> None:
        self.nota = MSG_ERRO_NA_FAIXA
        self._mudou()

    # -- o que a tela desenha -----------------------------------------------------------

    @property
    def tem_disco(self) -> bool:
        return self.disco is not None

    @property
    def tocando(self) -> bool:
        return self.player.estado == Estado.TOCANDO

    def visor(self) -> Visor | None:
        if self.disco is None:
            return None
        total = self.player.total_de_faixas
        i = self.player.indice
        faixa = f"Faixa {i + 1} de {total}"
        estado = self.player.estado
        if estado == Estado.TOCANDO:
            palavra, linha = "TOCANDO", f"TOCANDO: {faixa}"
        elif estado == Estado.PAUSADO:
            palavra, linha = "PAUSADO", "PAUSADO. Aperte Tocar para continuar"
        else:
            palavra, linha = "PARADO", "PARADO. Aperte Tocar para ouvir o disco de novo"
        musica = self.disco.tracks[i]
        return Visor(estado == Estado.TOCANDO, palavra, linha, musica.title, self.disco.title,
                     faixa, self.nota, self.texto_do_tempo(), self.disco.artist, self.disco.year)

    def texto_do_tempo(self) -> str:
        if self.disco is None or self.player.estado == Estado.PARADO:
            return ""
        duracao = formatar_tempo(self.player.duracao())
        if not duracao:
            return ""
        return f"{formatar_tempo(self.player.posicao())} de {duracao}"

    # -- ações do usuário ---------------------------------------------------------------

    def progresso(self) -> float | None:
        """Quanto da faixa atual já tocou, de 0.0 a 1.0 (None se ainda não se sabe)."""
        if not self.tem_disco:
            return None
        posicao, duracao = self.player.posicao(), self.player.duracao()
        if posicao is None or not duracao:
            return None
        return max(0.0, min(1.0, posicao / duracao))

    def buscar_fracao(self, fracao: float) -> None:
        """Vai ao ponto `fracao` (0.0 a 1.0) da faixa atual: o clique na barra de progresso."""
        duracao = self.player.duracao()
        if not self.tem_disco or not duracao:
            return
        self.player.buscar(max(0.0, min(1.0, fracao)) * duracao)

    def abrir_disco(self, disco, indice: int = 0, posicao: float = 0.0, tocar: bool = True) -> None:
        """Põe o disco no rádio. Com `tocar=False`, fica pausado no ponto indicado."""
        self.nota = None
        self.disco = disco
        self.player.carregar([t.path for t in disco.tracks], indice, posicao, tocar)
        if tocar:
            self.memoria.registrar_recente(disco.id)
        self.guardar_posicao()
        self._mudou()

    def alternar(self) -> None:
        """Tocar/Pausar: o mesmo botão, trocando de palavra e de forma."""
        self.nota = None
        if self.player.estado == Estado.TOCANDO:
            self.player.pausar()
            self.guardar_posicao()
        else:
            self.player.tocar()
            self._registrar_recente()
        self._mudou()

    def tocar_faixa(self, indice: int) -> None:
        self.nota = None
        self.player.ir_para(indice)
        self._registrar_recente()
        self.guardar_posicao()
        self._mudou()

    def proxima(self) -> None:
        self.nota = None
        self.player.proxima()
        self.guardar_posicao()
        self._mudou()

    def anterior(self) -> None:
        self.nota = None
        self.player.anterior()
        self.guardar_posicao()
        self._mudou()

    def volume_mais(self) -> None:
        degrau = self.player.degrau_de_volume
        if degrau >= DEGRAU_MAXIMO:
            self.nota = "O volume já está no máximo."
        else:
            self._definir_volume(degrau + 1, "Volume mais alto")
        self._mudou()

    def volume_menos(self) -> None:
        degrau = self.player.degrau_de_volume
        if degrau <= 0:
            self.nota = "O volume já está no mínimo."
        else:
            self._definir_volume(degrau - 1, "Volume mais baixo")
        self._mudou()

    def _definir_volume(self, degrau: int, frase: str) -> None:
        self.player.definir_degrau_de_volume(degrau)
        self.preferencias.mudar(volume=degrau)
        self.nota = f"{frase} ({degrau} de {DEGRAU_MAXIMO})"

    def alternar_voz_mais_clara(self) -> None:
        ligada = not self.player.voz_mais_clara
        self.player.definir_voz_mais_clara(ligada)
        self.preferencias.mudar(voz_mais_clara=ligada)
        self.nota = f"Voz mais clara {'ligada' if ligada else 'desligada'}."
        self._mudou()

    def _registrar_recente(self) -> None:
        if self.disco is not None:
            self.memoria.registrar_recente(self.disco.id)

    def guardar_o_disco_e_parar(self) -> None:
        """"Guardar o disco na estante": para a música e esvazia o rádio."""
        self.nota = None
        self.guardar_posicao()
        self.player.parar()
        self.disco = None
        self._mudou()

    # -- memória ----------------------------------------------------------------------------

    def guardar_posicao(self, inicio: bool = False) -> None:
        """Grava disco, faixa e segundo. Chamado de tempos em tempos e ao fechar."""
        if self.disco is None:
            return
        indice = 0 if inicio else self.player.indice
        segundos = 0.0 if inicio else (self.player.posicao() or 0.0)
        self.memoria.guardar_onde_parou(self.disco.id, indice, segundos)
