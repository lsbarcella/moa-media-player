#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.
# Gera o pacote .deb em dist/. Só precisa do dpkg-deb (já vem no Mint/Ubuntu).
set -euo pipefail

raiz="$(cd "$(dirname "$0")/.." && pwd)"
versao="$(python3 -c "import sys; sys.path.insert(0, '$raiz'); import moa; print(moa.__version__)")"
nome="moa-media-player"
destino="$raiz/dist"
palco="$(mktemp -d)"
trap 'rm -rf "$palco"' EXIT

# 1. O aplicativo (sem testes nem bytecode: o pós-instalação compila para o Python da máquina)
install -d "$palco/usr/lib/moa"
cp -r "$raiz/moa" "$palco/usr/lib/moa/moa"
find "$palco/usr/lib/moa" -name '__pycache__' -type d -prune -exec rm -rf {} +

# 2. Comando, atalho do menu, ícone e licença
install -D -m 755 "$raiz/packaging/moa" "$palco/usr/bin/moa"
install -D -m 644 "$raiz/packaging/br.tcc.Moa.desktop" "$palco/usr/share/applications/br.tcc.Moa.desktop"
install -D -m 644 "$raiz/packaging/br.tcc.Moa.svg" "$palco/usr/share/icons/hicolor/scalable/apps/br.tcc.Moa.svg"
install -D -m 644 "$raiz/LICENSE" "$palco/usr/share/doc/$nome/copyright"

# 3. Permissões: pastas 755, arquivos 644 (o comando já é 755)
find "$palco/usr/lib/moa" -type d -exec chmod 755 {} +
find "$palco/usr/lib/moa" -type f -exec chmod 644 {} +

# 4. Controle do pacote
install -d "$palco/DEBIAN"
tamanho="$(du -sk "$palco/usr" | cut -f1)"
cat > "$palco/DEBIAN/control" <<CONTROLE
Package: $nome
Version: $versao
Section: sound
Priority: optional
Architecture: all
Installed-Size: $tamanho
Depends: python3 (>= 3.10), python3-gi, python3-gi-cairo, gir1.2-gtk-3.0, gir1.2-gstreamer-1.0, gstreamer1.0-plugins-base, gstreamer1.0-plugins-good, python3-mutagen, libcdparanoia0
Maintainer: Leonardo dos Santos Barcella <lsbarcella@users.noreply.github.com>
Homepage: https://github.com/lsbarcella/moa-media-player
Description: Reprodutor de música offline e acessível para idosos
 Uma estante de discos e um rádio antigo na tela do computador. Toca a
 coleção de música sem internet e copia CDs para a estante.
CONTROLE
cat > "$palco/DEBIAN/postinst" <<'POS'
#!/bin/sh
set -e
if [ "$1" = "configure" ] && command -v py3compile >/dev/null 2>&1; then
    py3compile -p moa-media-player /usr/lib/moa || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
exit 0
POS
cat > "$palco/DEBIAN/prerm" <<'PRE'
#!/bin/sh
set -e
if command -v py3clean >/dev/null 2>&1; then
    py3clean -p moa-media-player || true
fi
exit 0
PRE
chmod 755 "$palco/DEBIAN/postinst" "$palco/DEBIAN/prerm"

# 5. Empacotar
mkdir -p "$destino"
arquivo="$destino/${nome}_${versao}_all.deb"
dpkg-deb --root-owner-group --build "$palco" "$arquivo" >/dev/null
echo "Gerado: $arquivo ($(du -h "$arquivo" | cut -f1))"
