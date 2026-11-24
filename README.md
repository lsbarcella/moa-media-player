# Estante

Reprodutor de música **offline**, **leve** e **acessível para idosos**, para Linux Mint (Cinnamon).
A interface imita uma estante de CDs: um clique na capa e o disco toca inteiro.

Projeto de TCC (Engenharia de Software, Uninter). Contexto completo em [CLAUDE.md](CLAUDE.md).

## Dependências

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gstreamer-1.0 \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good python3-mutagen python3-pytest
tools/check_deps.sh   # confere se está tudo instalado
```

## Executar

```bash
python3 -m estante
```

## Testes

```bash
python3 -m pytest
```

## Documentação

- `docs/adr/`: registros de decisão de arquitetura
- `docs/registro-ia.md`: diário do uso de IA
