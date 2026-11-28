#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.
# Mede o desempenho do Moa e grava um CSV em medicoes/ (veja tools/measure.py e o ADR-0021).
#
# Uso:   bash tools/measure.sh               (medição completa, ~3 minutos)
#        bash tools/measure.sh --rapido      (coleções pequenas: só para ver se funciona)
#        bash tools/measure.sh --sem-audio   (pula a CPU tocando, se não há placa de som)
#        bash tools/measure.sh --frio        (esvazia o cache do sistema antes; usa sudo)
# Feche o Moa antes. Durante a medição janelas do app abrem e fecham sozinhas.
set -euo pipefail
raiz="$(cd "$(dirname "$0")/.." && pwd)"

if [ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
    echo "Rode isto dentro da sessão gráfica (precisa de tela)." >&2
    exit 1
fi
bash "$raiz/tools/check_deps.sh" >/dev/null || {
    echo "Faltam dependências. Rode: bash tools/check_deps.sh" >&2
    exit 1
}
exec python3 "$raiz/tools/measure.py" "$@"
