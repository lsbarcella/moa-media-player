# Moa Media Player

Reprodutor de música **offline**, **leve** e **acessível para idosos**, para Linux Mint (Cinnamon).
A interface imita uma estante de CDs: um clique na capa e o disco toca inteiro.
O nome é uma homenagem ao pai do autor, Moacir.

Projeto de TCC (Engenharia de Software, Uninter). Contexto completo em [CLAUDE.md](CLAUDE.md).

## Dependências

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gstreamer-1.0 \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good python3-mutagen python3-pytest
tools/check_deps.sh   # confere se está tudo instalado
```

## Executar

```bash
python3 -m moa
```

## Testes

```bash
python3 -m pytest
```

## Licença

Moa Media Player é **software livre**, licenciado sob a **GNU General Public License versão 3**.
O texto completo está em [LICENSE](LICENSE). Decisão registrada em `docs/adr/0009-licenca-gpl-v3.md`.

## Documentação

- `docs/adr/`: registros de decisão de arquitetura
- `docs/registro-ia.md`: diário do uso de IA
