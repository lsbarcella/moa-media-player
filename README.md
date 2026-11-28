# Moa Media Player

Reprodutor de música **offline**, **leve** e **acessível para idosos**, para Linux Mint (XFCE).
A interface imita objetos que o idoso já conhece: uma **estante de discos**, um **rádio antigo** para
ouvir e um **aparelho de CD** para colocar discos novos. Um clique na capa e o disco toca inteiro.

O nome é uma homenagem ao pai do autor, Moacir: a "moa" é uma ave extinta da Nova Zelândia.

Projeto de TCC (Engenharia de Software, Uninter). O contexto completo, as regras de UX e as decisões
do autor estão em [CLAUDE.md](CLAUDE.md).

> **Estado:** MVP em teste. Versão `0.1.0`. Já roda, mas ainda **não foi validado no notebook
> do usuário** (ver [O que ainda não foi testado](#o-que-ainda-não-foi-testado)).

## O que o app faz

| Tela | O que o usuário faz |
| --- | --- |
| **Minha estante** | Vê os discos (capas) e pega um com um clique. "Continuar a ouvir" e "Ouvidos há pouco" lembram onde parou. |
| **Tocando agora** (rádio) | Tocar/Pausar, Anterior, Próxima, volume em 10 degraus, **"Voz mais clara"** (reforça voz e agudos), lista das músicas do disco. |
| **Criar uma playlist** | Marca músicas de vários discos; ao digitar, o texto vai direto para a busca. O resultado vira um disco novo na estante (virtual, não copia arquivos). |
| **"+" em cada música** | Põe a música em um disco existente ou em um disco novo, escolhendo pelas capas. |
| **Mexendo no disco** | Renomeia, troca a capa ("Como era antes" desfaz) e tira o disco da estante. |
| **A Lixeira** | Guarda os discos tirados da estante (as músicas continuam no computador). "Apagar de vez" só existe aqui, com confirmação calma. |
| **Aparelho de CD** | Copia um CD para a estante (FLAC, lido com cdparanoia). O disco entra como "Disco N". |
| **Configurações** | Tamanho da letra (Normal, Grande, Maior) e cores para daltonismo. |

Outros comportamentos, sempre sem mensagem técnica para o idoso:

- **Retoma** de onde parou (disco, faixa e posição), ao abrir e a cada poucos segundos.
- **Funciona 100% offline.** Se houver internet, o app **pode** corrigir nomes e capas pelo
  MusicBrainz em segundo plano; as mudanças aparecem na abertura seguinte.
- **A estante se atualiza sozinha** a cada abertura (só o que mudou é relido).
- **Instância única** (abrir de novo traz a janela existente) e **impede a suspensão** enquanto toca.
- **Teclado:** espaço toca/pausa, setas esquerda/direita trocam de faixa, cima/baixo mudam o volume.
- Áreas clicáveis de **pelo menos 64 px**, letra base de 20 px, contraste AAA, foco bem visível,
  ícones sempre acompanhados de texto.

## Requisitos

- Linux Mint (XFCE) ou derivado do Ubuntu. Python **3.10 ou mais novo** (Mint 21 e 22).
- Pacotes do apt (nenhum `pip install`):

```bash
sudo apt update
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gstreamer-1.0 \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good python3-mutagen libcdparanoia0
bash tools/check_deps.sh     # confere o que falta e diz o comando para instalar
```

O `python3-pytest` só é preciso para rodar os testes (o `check_deps.sh` apenas avisa se faltar).
Para **tocar MP3** o GStreamer usa o `gstreamer1.0-plugins-good`; arquivos de outros formatos
(`.flac`, `.ogg`, `.m4a`, `.wav`) também são aceitos.

## Executar

A partir do código-fonte (baixe o zip da branch ou clone o repositório):

```bash
cd moa-media-player
python3 -m moa
```

O app procura a música em `~/Música` (pasta de música do sistema). Toda pasta que tem arquivos de
áudio, em qualquer profundidade, vira um disco.

| Variável de ambiente | Efeito |
| --- | --- |
| `MOA_PASTA_DE_MUSICA=/caminho` | Usa outra pasta de música. |
| `MOA_SEM_REDE=1` | Nunca usa a rede (nem MusicBrainz nem o atualizador de teste). |

Onde o app guarda as coisas:

| O quê | Onde |
| --- | --- |
| Banco (cache da estante, discos montados, Lixeira, onde parou) | `~/.local/share/moa/moa.db` |
| Log (para o autor; o idoso nunca vê) | `~/.local/share/moa/moa.log` |
| Preferências (letra, cores, volume, "Voz mais clara") | `~/.config/moa/config.json` |

Os arquivos de música **nunca são reescritos** pelo app (nem as tags): o que vem do MusicBrainz ou
da edição do usuário fica numa camada à parte, no banco.

## Instalar como pacote (.deb)

```bash
bash tools/build_deb.sh                       # gera dist/moa-media-player_0.1.0_all.deb
sudo apt install ./dist/moa-media-player_0.1.0_all.deb
```

Instala o comando `moa`, o atalho no menu e o ícone, e liga a abertura automática na primeira
execução. O `apt` baixa as dependências, então **precisa de internet na instalação**. Um instalador
offline e uma versão para Windows estão nos planos (M10 do [CLAUDE.md](CLAUDE.md)). O ícone atual
é provisório.

## Testes

```bash
python3 -m pytest
```

Para avaliar o app com o usuário (tarefas, planilha de tempo e erros, questionário SUS), veja
[`docs/testes-usabilidade.md`](docs/testes-usabilidade.md).

Os testes de interface desenham as telas fora da tela (precisam de uma sessão gráfica; sem ela são
pulados). Os de áudio geram arquivos curtos com o GStreamer, e os de rede usam um servidor falso
local: **nenhum teste acessa a internet**.

## Medir o desempenho

```bash
bash tools/measure.sh              # medição completa (alguns minutos); feche o Moa antes
bash tools/measure.sh --rapido     # coleções pequenas, só para ver se funciona
```

Mede a abertura, a RAM, a CPU e o tempo de 11 ações, com um disco de 371 faixas e outra coleção de
80 discos. Cada ação tem dois tempos: até a tela responder e até terminar de montar (listas grandes
vêm em pedaços). Mostra o andamento passo a passo e, no fim, imprime um resumo entre "copie daqui" e
"até aqui". Grava três arquivos em `medicoes/`: `.txt` (o resumo, para colar numa conversa), `.csv`
(todos os números, com a configuração da máquina) e `.log` (tudo o que apareceu na tela). Nada é
enviado pela rede. Detalhes e limites em [ADR-0021](docs/adr/0021-medicao-de-desempenho.md).

## Atualização de teste (temporária)

Enquanto o app está em teste, ele pode se atualizar pela branch `dev` do GitHub: aparece um cartão
na Estante ("Tem uma versão mais nova do app") e em Configurações. Só funciona em pasta de
código-fonte gravável (nunca na instalação por `.deb`) e **será removido antes da versão final**.
Veja o [ADR-0020](docs/adr/0020-atualizacao-de-teste.md), que traz a lista do que apagar.

## Estrutura

```
moa/
├── core/        Lógica, sem GTK (testável sem tela): biblioteca, player, rádio, banco SQLite,
│                discos montados, Lixeira, MusicBrainz, cópia de CD, sessão
├── ui/          Telas em GTK 3 (estante, rádio, playlist, Lixeira, editar, aparelho de CD,
│                configurações), tema e ícones SVG
tests/           pytest, com áudio de teste gerado na hora
tools/           check_deps.sh, build_deb.sh, measure.sh, gerador de coleção sintética
packaging/       comando moa, atalho .desktop e ícone do pacote
docs/            ADRs, registro de uso de IA, previews em HTML
```

Regra central: o `core/` **não importa GTK**. A interface só desenha o que o `core/` diz.

## Contribuindo

O autor decide UX, UI e arquitetura; mudanças que afetam o usuário viram um **ADR** em `docs/adr/`.

- Branches de trabalho saem da `dev` (`fix/...`, `feature/...`, `docs/...`) e voltam para ela por PR.
  A `main` só recebe da `dev`.
- Commits pequenos, em português, no imperativo ("Adiciona leitura de tags com mutagen").
- Todo arquivo `.py` ou `.sh` novo começa com o cabeçalho de licença de três linhas (um teste confere).
- Sem dependência nova sem ADR; só pacotes do apt.

## O que ainda não foi testado

- O app **no notebook do usuário** (HD mecânico, CPU antiga, Linux Mint XFCE): desempenho, aparência
  e as áreas clicáveis na tela real.
- A **cópia de CD com um disco de verdade** (a leitura do sumário do disco, a gaveta, discos riscados).
- A **instalação do `.deb`** num Mint limpo e a abertura automática no login do XFCE.
- O **MusicBrainz e o Cover Art Archive** reais (os testes usam respostas falsas).
- As paletas de daltonismo com uma pessoa daltônica de verdade.

## Licença

Copyright (C) 2026 Leonardo dos Santos Barcella

Moa Media Player é **software livre**: você pode redistribuí-lo e modificá-lo sob os termos da
**GNU General Public License**, publicada pela Free Software Foundation, na **versão 3 ou, a seu
critério, em qualquer versão posterior**. Ele é distribuído **sem nenhuma garantia**.
O texto completo da licença está em [LICENSE](LICENSE). Decisão registrada em
[ADR-0009](docs/adr/0009-licenca-gpl-v3.md).

## Documentação

- [`docs/adr/`](docs/adr/): registros de decisão de arquitetura (stack, modelos mentais, rede opcional,
  acessibilidade, persistência, licença, cópia de CD, pacote, medição...).
- [`docs/testes-usabilidade.md`](docs/testes-usabilidade.md): roteiro dos testes com o usuário.
- [`docs/registro-ia.md`](docs/registro-ia.md): diário do uso de IA, sessão a sessão.
- [`docs/preview/`](docs/preview/): desenhos interativos em HTML das telas e das opções de design.
