"""Ferramentas de teste: gera arquivos de áudio curtos com o GStreamer.

Os arquivos são criados uma vez por sessão de testes e depois copiados e
etiquetados com o mutagen, para os testes ficarem rápidos.
"""

from pathlib import Path

import gi
import mutagen
import pytest

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

Gst.init(None)

# Formato -> trecho do pipeline que codifica o áudio.
_CODIFICADORES = {
    ".mp3": "lamemp3enc",
    ".flac": "flacenc",
    ".ogg": "vorbisenc ! oggmux",
    ".wav": "wavenc",
}


def _gerar_audio(destino: Path) -> None:
    codificador = _CODIFICADORES[destino.suffix]
    pipeline = Gst.parse_launch(
        "audiotestsrc num-buffers=4 samplesperbuffer=1024 ! audioconvert ! "
        f'audioresample ! {codificador} ! filesink location="{destino}"'
    )
    pipeline.set_state(Gst.State.PLAYING)
    mensagem = pipeline.get_bus().timed_pop_filtered(
        10 * Gst.SECOND, Gst.MessageType.EOS | Gst.MessageType.ERROR
    )
    pipeline.set_state(Gst.State.NULL)
    if mensagem is None or mensagem.type == Gst.MessageType.ERROR:
        raise RuntimeError(f"não consegui gerar o áudio de teste {destino.name}")


@pytest.fixture(scope="session")
def audio_base(tmp_path_factory):
    """Bytes de um arquivo de áudio válido para cada formato."""
    pasta = tmp_path_factory.mktemp("audio_base")
    modelos = {}
    for extensao in _CODIFICADORES:
        arquivo = pasta / f"base{extensao}"
        _gerar_audio(arquivo)
        modelos[extensao] = arquivo.read_bytes()
    return modelos


@pytest.fixture
def make_track(audio_base):
    """Cria um arquivo de música de verdade, com as tags que você passar.

    Uso: make_track(pasta, "01.mp3", title="Samba", artist="Zeca").
    Os nomes das tags são os do modo "easy" do mutagen (title, artist, album,
    albumartist, tracknumber).
    """

    def _criar(pasta: Path, nome: str, **tags) -> Path:
        pasta.mkdir(parents=True, exist_ok=True)
        destino = pasta / nome
        destino.write_bytes(audio_base[destino.suffix.lower()])
        if tags:
            arquivo = mutagen.File(destino, easy=True)
            if arquivo.tags is None:
                arquivo.add_tags()
            for chave, valor in tags.items():
                arquivo[chave] = valor
            arquivo.save()
        return destino

    return _criar
