# ADR-0019 — Pacote .deb do aplicativo (M8, primeira etapa)

- **Status:** Aceito. Detalhes técnicos da IA marcados como **provisórios**.
- **Data:** 27/11/2026
- **Decisor:** o autor escolheu começar pelo `.deb` só do app (opção 1) e deixar os instaladores para depois.

## Contexto

O projeto roda do código-fonte (`python3 -m moa`), o que exige clonar, instalar dependências à mão e abrir terminal. O CLAUDE.md prevê um `.deb` no M8 e a abertura automática depende do comando `moa` instalado (ADR-0013).

## Decisão

1. `tools/build_deb.sh` gera `dist/moa-media-player_VERSAO_all.deb` usando só o `dpkg-deb` (sem `fakeroot`, `debhelper` nem outra dependência). A versão vem de `moa.__version__`.
2. O pacote instala o código em `/usr/lib/moa`, o comando `/usr/bin/moa`, o atalho do menu `br.tcc.Moa.desktop` e o ícone em `hicolor/scalable`. Não leva testes nem bytecode: o `postinst` roda `py3compile` com o Python da própria máquina (Mint 21 e 22 usam versões diferentes).
3. **Dependências declaradas:** `python3 (>= 3.10)`, `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-gstreamer-1.0`, `gstreamer1.0-plugins-base`, `gstreamer1.0-plugins-good`, `python3-mutagen`, `libcdparanoia0`. O `pytest` fica de fora.
4. A abertura automática (ADR-0013) passa a funcionar sozinha na primeira execução, porque `moa` existe no PATH.
5. O `Maintainer` usa o endereço de e-mail anônimo do GitHub (`@users.noreply.github.com`), para não expor e-mail pessoal num repositório público.
6. `tests/test_packaging.py` gera o pacote e confere dependências, conteúdo, permissões e se o comando importa o app de qualquer pasta.

## Alternativas

- **`.run` com as dependências offline e instalador para Windows:** ficam no M10 do CLAUDE.md. O `.deb` sozinho **ainda precisa de internet** para baixar as dependências que faltarem.
- **PyInstaller/AppImage:** rejeitados por tamanho e fragilidade com GTK e GStreamer.

## Consequências

- Instalação: `sudo apt install ./moa-media-player_0.1.0_all.deb` (o `apt` resolve as dependências, com internet).
- O **ícone é provisório**: a moa com fones de ouvido ainda precisa ser desenhada (ADR-0009).
- **Atalho na Área de Trabalho** não vai no pacote (um `.deb` não escreve na pasta de cada usuário). Fica para o M10 ou para um primeiro uso do app.
- **Não testado:** instalação em um Mint limpo, abertura pelo menu do XFCE e desinstalação.
