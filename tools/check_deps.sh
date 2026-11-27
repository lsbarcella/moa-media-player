#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.
# Verifica se a máquina tem tudo que o Moa Media Player precisa.
falhou=0

checa() {
    if python3 -c "$2" 2>/dev/null; then
        echo "OK      $1"
    else
        echo "FALTA   $1   (sudo apt install $3)"
        falhou=1
    fi
}

echo "Python: $(python3 --version 2>&1)"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' \
    || { echo "FALTA   Python 3.10 ou mais novo"; falhou=1; }

checa "GTK 3 (PyGObject)" \
    "import gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk" \
    "python3-gi gir1.2-gtk-3.0"
checa "GStreamer" \
    "import gi; gi.require_version('Gst','1.0'); from gi.repository import Gst; Gst.init(None); assert Gst.ElementFactory.find('playbin')" \
    "gir1.2-gstreamer-1.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good"
checa "Copiar CD: leitura (cdparanoiasrc)" \
    "import gi; gi.require_version('Gst','1.0'); from gi.repository import Gst; Gst.init(None); assert Gst.ElementFactory.find('cdparanoiasrc')" \
    "gstreamer1.0-plugins-base libcdparanoia0"
checa "Copiar CD: codificador FLAC (flacenc)" \
    "import gi; gi.require_version('Gst','1.0'); from gi.repository import Gst; Gst.init(None); assert Gst.ElementFactory.find('flacenc')" \
    "gstreamer1.0-plugins-good"
checa "mutagen" "import mutagen" "python3-mutagen"
# Só para desenvolvimento (rodar os testes): se faltar, avisa, mas não é erro.
if python3 -c "import pytest" 2>/dev/null; then
    echo "OK      pytest (só desenvolvimento)"
else
    echo "AVISO   pytest não instalado; só é preciso para rodar os testes (sudo apt install python3-pytest)"
fi

exit $falhou
