# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tocador de áudio do Moa, em cima do GStreamer (ADR-0010). Sem GTK.

O `Player` toca a fila de faixas de UM disco, de ponta a ponta. Não existe
aleatório nem repetir (CLAUDE.md, seção 9). Quando o disco acaba, ele para.

Como funciona, em linguagem de TypeScript:
- O GStreamer manda mensagens (fim da faixa, erro...) por um "barramento", que
  é como um EventEmitter. Aqui escutamos esse barramento com `add_signal_watch`,
  e as mensagens chegam quando o laço de eventos do GLib roda (no app, é o laço
  do GTK; nos testes, um laço que giramos na mão).
- Quem usa o `Player` registra funções de retorno (callbacks), como
  `player.on_state = lambda estado: ...`.

A cadeia de áudio fica no `audio-filter` do `playbin`:
    rgvolume (ReplayGain) -> equalizer-3bands ("Voz mais clara") -> volume (degrau)
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Callable, Sequence

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

log = logging.getLogger(__name__)

Gst.init(None)

# --- Volume (ADR-0010) -------------------------------------------------------
# 11 posições: 0 (mudo) a 10 (100%). O ganho nunca passa de 1.0: o app não
# amplifica, só abaixa (o volume do sistema é ajustado uma vez na instalação).
DEGRAU_MAXIMO = 10
DEGRAU_PADRAO = 6


def ganho_do_degrau(degrau: int) -> float:
    """Converte o degrau (0 a 10) no ganho do GStreamer, com curva cúbica.

    O ouvido percebe volume de forma logarítmica; a curva cúbica faz cada
    degrau soar como um passo parecido. Valor provisório (ADR-0010).
    """
    degrau = max(0, min(DEGRAU_MAXIMO, degrau))
    return (degrau / DEGRAU_MAXIMO) ** 3


# --- "Voz mais clara" (ADR-0004 / ADR-0010) --------------------------------------
# Ganhos em dB para as bandas do `equalizer-3bands` (100 Hz, 1100 Hz, 11 kHz).
# Valores PROVISÓRIOS, ainda a ouvir com o usuário.
GANHOS_VOZ_MAIS_CLARA = (-3.0, 3.0, 6.0)
GANHOS_NEUTROS = (0.0, 0.0, 0.0)

# Bandas do equalizador, na ordem dos ganhos acima.
_PROPRIEDADES_BANDAS = ("band0", "band1", "band2")

# Flag do playbin: só áudio (o app não toca vídeo no MVP).
_FLAG_SO_AUDIO = 2


def _criar_elemento(nome: str) -> Gst.Element | None:
    """Cria um elemento do GStreamer, ou None se o plugin não existir.

    Fica numa função à parte para os testes poderem simular um plugin ausente.
    """
    return Gst.ElementFactory.make(nome)


class Estado(Enum):
    PARADO = "parado"
    TOCANDO = "tocando"
    PAUSADO = "pausado"


class Player:
    """Toca uma fila de faixas com o `playbin` do GStreamer."""

    def __init__(self, sink_factory: Callable[[], Gst.Element] | None = None):
        """`sink_factory` cria o destino do som. Nos testes, um `fakesink`."""
        self.on_state: Callable[[Estado], None] | None = None
        self.on_track: Callable[[int], None] | None = None
        self.on_disc_end: Callable[[], None] | None = None
        self.on_track_error: Callable[[int], None] | None = None

        self._faixas: list[Path] = []
        self._indice = 0
        self._estado = Estado.PARADO
        self._degrau = DEGRAU_PADRAO
        self._voz_mais_clara = False
        self._seek_pendente: float | None = None
        self._iniciar_tocando = True

        self._playbin = Gst.ElementFactory.make("playbin", "moa-playbin")
        self._playbin.set_property("flags", _FLAG_SO_AUDIO)
        if sink_factory is not None:
            self._playbin.set_property("audio-sink", sink_factory())

        self._volume = None
        self._equalizador = None
        filtro = self._montar_cadeia()
        if filtro is not None:
            self._playbin.set_property("audio-filter", filtro)
        self._aplicar_volume()
        self._aplicar_voz_mais_clara()

        barramento = self._playbin.get_bus()
        barramento.add_signal_watch()
        barramento.connect("message", self._ao_receber_mensagem)

    # -- cadeia de áudio -------------------------------------------------------

    def _montar_cadeia(self) -> Gst.Bin | None:
        """Monta rgvolume -> equalizador -> volume; pula o que não existir.

        Se faltar um plugin, o app toca sem ele e só registra no log: nunca
        quebra (restrição 5).
        """
        elementos = []
        for nome in ("rgvolume", "equalizer-3bands", "volume"):
            elemento = _criar_elemento(nome)
            if elemento is None:
                log.warning("plugin %s não encontrado; vou tocar sem ele", nome)
                continue
            elementos.append(elemento)
            if nome == "rgvolume":
                elemento.set_property("album-mode", True)   # um disco inteiro: ganho do álbum
            elif nome == "equalizer-3bands":
                self._equalizador = elemento
            else:
                self._volume = elemento
        if not elementos:
            return None
        caixa = Gst.Bin.new("moa-cadeia")
        for elemento in elementos:
            caixa.add(elemento)
        for anterior, seguinte in zip(elementos, elementos[1:]):
            anterior.link(seguinte)
        caixa.add_pad(Gst.GhostPad.new("sink", elementos[0].get_static_pad("sink")))
        caixa.add_pad(Gst.GhostPad.new("src", elementos[-1].get_static_pad("src")))
        return caixa

    def _aplicar_volume(self) -> None:
        if self._volume is not None:
            self._volume.set_property("volume", ganho_do_degrau(self._degrau))

    def _aplicar_voz_mais_clara(self) -> None:
        if self._equalizador is None:
            return
        ganhos = GANHOS_VOZ_MAIS_CLARA if self._voz_mais_clara else GANHOS_NEUTROS
        for propriedade, ganho in zip(_PROPRIEDADES_BANDAS, ganhos):
            self._equalizador.set_property(propriedade, ganho)

    # -- o que a interface pode perguntar ---------------------------------------

    @property
    def estado(self) -> Estado:
        return self._estado

    @property
    def indice(self) -> int:
        """Posição (a partir de 0) da faixa atual na fila."""
        return self._indice

    @property
    def total_de_faixas(self) -> int:
        return len(self._faixas)

    @property
    def degrau_de_volume(self) -> int:
        return self._degrau

    @property
    def voz_mais_clara(self) -> bool:
        return self._voz_mais_clara

    def posicao(self) -> float | None:
        """Segundos já tocados da faixa atual, ou None se ainda não se sabe."""
        ok, valor = self._playbin.query_position(Gst.Format.TIME)
        return valor / Gst.SECOND if ok else None

    def duracao(self) -> float | None:
        """Duração da faixa atual em segundos, ou None se ainda não se sabe."""
        ok, valor = self._playbin.query_duration(Gst.Format.TIME)
        return valor / Gst.SECOND if ok else None

    # -- comandos ---------------------------------------------------------------

    def carregar(self, faixas: Sequence[Path], indice: int = 0, posicao: float = 0.0,
                 tocar: bool = True) -> None:
        """Escolhe o disco (a fila) e a faixa em que começar.

        Com `tocar=False` o disco fica pausado no ponto indicado: é assim que o
        app "retoma de onde parou" sem começar a tocar sozinho.
        """
        self._parar_motor()
        self._faixas = [Path(f) for f in faixas]
        if not self._faixas:
            self._definir_estado(Estado.PARADO)
            return
        self._abrir_faixa(max(0, min(indice, len(self._faixas) - 1)), posicao, tocar)

    def tocar(self) -> None:
        """Toca. Pausado: continua. Parado: começa o disco (do início se acabou)."""
        if not self._faixas:
            return
        if self._estado == Estado.PAUSADO:
            self._playbin.set_state(Gst.State.PLAYING)
            self._definir_estado(Estado.TOCANDO)
        elif self._estado == Estado.PARADO:
            self._abrir_faixa(0, 0.0, True)

    def pausar(self) -> None:
        if self._estado == Estado.TOCANDO:
            self._playbin.set_state(Gst.State.PAUSED)
            self._definir_estado(Estado.PAUSADO)

    def parar(self) -> None:
        self._parar_motor()
        self._definir_estado(Estado.PARADO)

    def ir_para(self, indice: int) -> None:
        """Toca a faixa `indice` (a partir de 0). Fora do intervalo, ignora."""
        if 0 <= indice < len(self._faixas):
            self._abrir_faixa(indice, 0.0, True)

    def proxima(self) -> None:
        """Vai para a próxima faixa; na última, o disco acaba."""
        if not self._faixas:
            return
        if self._indice + 1 < len(self._faixas):
            self._abrir_faixa(self._indice + 1, 0.0, True)
        else:
            self._terminar_disco()

    def anterior(self) -> None:
        """Volta uma faixa; na primeira, reinicia a faixa."""
        if not self._faixas:
            return
        self._abrir_faixa(max(0, self._indice - 1), 0.0, True)

    def definir_degrau_de_volume(self, degrau: int) -> None:
        self._degrau = max(0, min(DEGRAU_MAXIMO, degrau))
        self._aplicar_volume()

    def definir_voz_mais_clara(self, ligada: bool) -> None:
        self._voz_mais_clara = bool(ligada)
        self._aplicar_voz_mais_clara()

    def encerrar(self) -> None:
        """Libera o GStreamer. Chamar ao fechar o app."""
        self._parar_motor()
        self._playbin.get_bus().remove_signal_watch()

    # -- por dentro --------------------------------------------------------------

    def _definir_estado(self, novo: Estado) -> None:
        if novo != self._estado:
            self._estado = novo
            if self.on_state:
                self.on_state(novo)

    def _parar_motor(self) -> None:
        self._seek_pendente = None
        self._playbin.set_state(Gst.State.NULL)

    def _abrir_faixa(self, indice: int, posicao: float, tocar: bool) -> None:
        """Carrega a faixa `indice` e começa (ou deixa pausada)."""
        self._parar_motor()
        self._indice = indice
        self._playbin.set_property("uri", self._faixas[indice].resolve().as_uri())
        self._seek_pendente = posicao if posicao > 0 else None
        self._iniciar_tocando = tocar
        self._playbin.set_state(Gst.State.PLAYING if tocar else Gst.State.PAUSED)
        self._definir_estado(Estado.TOCANDO if tocar else Estado.PAUSADO)
        if self.on_track:
            self.on_track(indice)

    def _terminar_disco(self) -> None:
        self._parar_motor()
        self._definir_estado(Estado.PARADO)
        if self.on_disc_end:
            self.on_disc_end()

    def _ao_receber_mensagem(self, _barramento, mensagem: Gst.Message) -> None:
        tipo = mensagem.type
        if tipo == Gst.MessageType.EOS:
            self.proxima()
        elif tipo == Gst.MessageType.ERROR:
            erro, detalhe = mensagem.parse_error()
            log.error("erro ao tocar %s: %s (%s)", self._faixas[self._indice], erro, detalhe)
            if self.on_track_error:
                self.on_track_error(self._indice)
            self.proxima()
        elif tipo == Gst.MessageType.ASYNC_DONE and self._seek_pendente is not None:
            # A faixa já está pronta para andar: agora o salto funciona.
            segundos, self._seek_pendente = self._seek_pendente, None
            self._playbin.seek_simple(
                Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                int(segundos * Gst.SECOND))
