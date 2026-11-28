# CLAUDE.md — Reprodutor de música acessível para idosos (TCC)

Este arquivo dá ao Claude Code o contexto do projeto. Leia-o inteiro antes de qualquer tarefa.

## 1. O projeto em uma frase

Um reprodutor de música **offline por padrão**, **leve** e **autônomo para idosos**, que roda no **Linux Mint (XFCE)** em notebooks antigos. A interface reaproveita **imagens mentais que o idoso já tem do mundo real**: uma **estante de CDs** e **aparelhos de som antigos**. O usuário pega um disco da estante, coloca no aparelho e ele toca inteiro.

Nome do aplicativo: **Moa Media Player** (decidido pelo autor). É uma homenagem ao pai do autor, Moacir; a "moa" é uma ave extinta da Nova Zelândia, e o ícone será uma moa com fones de ouvido. O nome pesquisado não conflita com nenhum aplicativo conhecido (busca limitada; marca não consultada).

Use **`moa`** como nome do pacote Python e **`br.tcc.Moa`** como application ID. **Não ponha "music" nem "player" nos nomes do código**, porque o app deve poder crescer para vídeos e fotos. A **tela inicial continua se chamando "Estante"**: o nome do app e o nome da tela são coisas diferentes.

## 2. Princípio central: autonomia por meio de modelos mentais

O objetivo do projeto é que **o idoso abra o app e se vire sozinho**, sem depender de ninguém. Para isso:

- **Cada elemento da tela deve parecer um objeto do mundo real que o idoso já sabe usar**, para ele reconhecer padrões em vez de aprender uma interface nova.
- **Ele nunca deve se sentir perdido.** Sempre deve ser claro onde ele está, o que pode fazer e como voltar.
- **Não existe "modo escondido" nem "modo para quem entende".** Tudo o que o app faz, inclusive cuidar da coleção, é feito pelo próprio usuário, dentro da mesma metáfora.
- O app **não depende de um cuidador**. O autor pode ajudar, mas nenhuma função pode exigir isso.
- O **X da janela fica**. Fechar uma janela é uma noção básica de computador que o usuário deve aprender, então não há botão "Desligar" próprio.
- **Sempre há um caminho de volta visível**, em qualquer tela que não seja a Estante.

Mapa de metáforas (ponto de partida, a refinar com o autor; ver ADR-0002):

| Ação no app | Imagem do mundo real |
| --- | --- |
| Tela inicial | Estante de músicas, com os álbuns (capas) à vista |
| Escolher um disco | Pegar o disco da estante |
| Tocando agora | Um **rádio** antigo |
| Tocar, pausar, próxima, anterior | Botões do rádio |
| Volume | Botão de volume do rádio |
| Voltar | Guardar o disco na estante |
| Playlist | Montar um disco novo a partir de músicas de outros discos |

## 3. Contexto

- **Usuário:** um idoso (o pai do autor) que quer ouvir sua coleção de CDs, já copiada para o notebook dele. Ele mesmo escolhe, toca e cuida da coleção.
- **Finalidade acadêmica:** é o TCC de Engenharia de Software (Uninter). O foco do trabalho são as **decisões de UX, acessibilidade e arquitetura**. O código materializa essas decisões.
- **Acervo:** cerca de 80% dos arquivos têm tags completas, feitas com o MusicBrainz Picard (provavelmente incluindo IDs do MusicBrainz). O restante tem nomes como "Faixa 01" ou só o título da música. **Cada CD foi copiado (ripado) para uma pasta própria**, então a regra "pasta = disco" vale (confirmado pelo autor). As **músicas duplicadas** da coleção são **a mesma música em CDs diferentes** (confirmado pelo autor). A profundidade das pastas (por exemplo `Música/CD` ou `Música/Artista/Álbum`) também ainda não é conhecida: o leitor deve funcionar nos dois casos.
- **Perfil do usuário:** definido **pela literatura**, sem questionário nem observação do pai do autor (ADR-0005): um idoso típico **sem demência**, com declínio esperado de visão, audição (sobretudo agudos), precisão motora e memória de trabalho. **O Estante não é projetado para pessoas com demência.** Diretrizes de demência (Sheffield, AMI) servem de inspiração, não de regra.
- **Escopo:** este documento descreve o **MVP**.

## 4. Como trabalhar com o autor (leia com atenção)

- **O autor decide UX, UI e arquitetura. Você implementa.** Quando surgir uma escolha que afete o usuário ou a arquitetura, apresente 2 ou 3 opções com prós e contras e uma recomendação, e **espere a decisão**. Não decida sozinho coisas listadas em "Decisões em aberto" (seção 11).
- **O autor sabe TypeScript, não sabe Python.** Ao final de cada etapa, explique em linguagem simples o que o código faz. Quando ajudar, compare com TypeScript ("isto é como uma interface em TS", "isto é como um callback/evento").
- **Ele vai defender o código perante uma banca.** O código precisa ser legível, sem esperteza desnecessária. Prefira clareza a concisão.
- **Registre cada decisão relevante como ADR** em `docs/adr/NNNN-titulo.md`, no formato do ADR-0001: contexto, alternativas, decisão, consequências.
- **Mantenha `docs/registro-ia.md`**, um diário curto de cada sessão: data, o que foi pedido, o que foi feito e quais decisões foram tomadas. Ele vai para o apêndice do TCC, como declaração de uso de IA.
- **Nunca escreva o texto do artigo do TCC.** Ajudar com documentação técnica é permitido (README, ADRs, comentários). Redigir parágrafos do artigo não é. Se o autor pedir isso, lembre-o de que trechos não autorais podem ser penalizados pela Uninter.
- Faça commits pequenos, com mensagens em português no imperativo (ex.: "Adiciona leitura de tags com mutagen").

## 5. Restrições não negociáveis

1. **Offline por padrão.** Tocar música, navegar e montar discos **nunca** dependem de internet. A rede é só um bônus **opcional e oportunista**: se houver conexão, o app pode consultar o MusicBrainz (e o Cover Art Archive) em segundo plano para melhorar nomes e capas. Sem conexão ou com falha, o idoso não percebe nada. **Nenhuma telemetria, nenhum envio de dados que identifiquem a máquina ou o usuário.** Ver ADR-0003.
2. **Leveza.** Rodar bem em CPU antiga, com pouca RAM, HD mecânico e GPU integrada antiga.
3. **Sem dependências novas sem ADR.** Use só o que está nos repositórios do Linux Mint (apt). Nada de `pip install` em tempo de execução.
4. **Compatível com Python 3.10 ou mais recente** (Mint 21 usa 3.10; Mint 22 usa 3.12).
5. **Nenhuma mensagem técnica para o idoso.** Nada de stack trace, diálogo de erro com jargão ou janela modal inesperada.
6. **Nada de função que exija outra pessoa.** Se algo parece "difícil demais" para o idoso, redesenhe dentro da metáfora, não esconda atrás de um modo.
7. **Software livre (GNU GPL v3).** Só use dependências, código e imagens com licença compatível, e confira a licença no ADR que introduzir cada novidade. Não copie trechos de fonte proprietária nem de GPL v2 somente. A arte do ícone deve ser original ou de licença livre (ADR-0009).

## 6. Stack (ver `docs/adr/0001-escolha-da-stack.md`)

| Componente | Uso | Pacote apt |
| --- | --- | --- |
| Python 3 | Linguagem | `python3` |
| GTK 3 via PyGObject | Interface, detecção de disco e de rede (`Gio`) | `python3-gi`, `gir1.2-gtk-3.0` |
| GStreamer 1.x | Reprodução de áudio, ReplayGain (`rgvolume`) e leitura de CD | `gir1.2-gstreamer-1.0`, `gstreamer1.0-plugins-base`, `gstreamer1.0-plugins-good` |
| mutagen | Tags e capas (MP3, FLAC, OGG) | `python3-mutagen` |
| pytest | Testes (só no ambiente de desenvolvimento) | `python3-pytest` |

- Use **GTK 3, não GTK 4**, porque o GTK 4 depende de aceleração gráfica que pode falhar em GPU antiga.
- Comece com `gi.require_version("Gtk", "3.0")` e `gi.require_version("Gst", "1.0")`.
- Reproduza com o elemento `playbin`, desligando o vídeo nos flags.
- Para o ambiente virtual de desenvolvimento, use `python3 -m venv --system-site-packages .venv`, já que o PyGObject vem do apt.
- O ajuste "Voz mais clara" usa um equalizador do GStreamer. O `equalizer-3bands` está no `gstreamer1.0-plugins-good`, **que já é dependência** (confirmado na máquina de desenvolvimento). Confirmar o `equalizer-10bands` antes de usá-lo (ADR-0004).
- Cópia de CD (M7, ADR-0017): leitura com `cdparanoiasrc` (`gstreamer1.0-plugins-base` + `libcdparanoia0`) e gravação em **FLAC** com `flacenc` (`gstreamer1.0-plugins-good`). Os dois elementos existem na máquina de desenvolvimento; **falta confirmar no Mint XFCE do notebook** pelo `check_deps.sh`.

## 7. Arquitetura

A lógica fica separada da interface. **O núcleo (`core/`) não importa GTK**, para poder ser testado sem tela.

```
moa/
├── CLAUDE.md
├── README.md
├── docs/
│   ├── adr/                # Registros de decisão
│   ├── registro-ia.md      # Diário das sessões com IA
│   └── testes-usabilidade.md
├── moa/
│   ├── __main__.py         # Ponto de entrada: python3 -m moa
│   ├── app.py              # Gtk.Application (garante instância única)
│   ├── core/
│   │   ├── library.py      # Varre pastas e monta álbuns e faixas (com fallbacks)
│   │   ├── models.py       # dataclasses: Album, Track
│   │   ├── covers.py       # Capa embutida, folder.jpg ou capa substituta
│   │   ├── player.py       # Envolve o GStreamer: tocar, pausar, próxima, volume
│   │   ├── db.py           # Banco SQLite: cache da biblioteca, discos montados, Lixeira, recentes (ADR-0008)
│   │   ├── state.py        # Salva e restaura onde parou (usa o banco)
│   │   ├── config.py       # Preferências do próprio usuário (JSON)
│   │   ├── custom_albums.py# "Discos montados" pelo usuário a partir de faixas existentes
│   │   ├── musicbrainz.py  # Atualização opcional e oportunista de nomes e capas
│   │   ├── ripper.py       # Copiar um CD para a biblioteca (M7, ADR-0017)
│   │   └── aparelho.py     # Estados e textos do "Aparelho de CD" (ADR-0018)
│   └── ui/
│       ├── window.py       # Janela principal e navegação entre telas
│       ├── shelf_view.py   # Tela "estante": grade de capas
│       ├── player_view.py  # Tela "tocando agora" (aparelho de som)
│       ├── cd_view.py      # Tela "Aparelho de CD": colocar um disco (ADR-0018)
│       ├── (telas de manutenção e de montar disco: desenho em aberto)
│       ├── icons/          # Ícones de aparelhos antigos (SVG)
│       └── style.css       # Tamanhos, cores e contraste
├── tests/                  # pytest, com pastas de música de exemplo
├── tools/
│   ├── check_deps.sh       # Verifica se a máquina-alvo tem tudo instalado
│   └── measure.sh          # Mede RAM, CPU e tempo de abertura
└── packaging/              # .desktop, ícone, autostart, scripts do .deb
```

Use `GLib.get_user_data_dir()` (para estado e cache) e `GLib.get_user_config_dir()` (para preferências), sempre numa subpasta `moa/`. A pasta de música padrão é a do sistema, `GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC)`, que no Mint em português é `~/Música`. O app a detecta sozinho.

**Regra para dados de origem externa (MusicBrainz e discos montados):** nunca reescreva os arquivos de música do usuário. Guarde as informações novas em uma camada separada, no cache do app, que se sobrepõe às tags (aceito pelo autor por enquanto; ver seção 11).

## 8. Regras de montagem da estante

A ordem de preferência para cada informação é:

1. **Tags do arquivo**, lidas com mutagen: artista do álbum (ou artista), álbum, número da faixa, título e capa embutida.
2. **Estrutura de pastas:** pasta = álbum. **Toda pasta que contém arquivos de áudio é um disco, em qualquer profundidade**; pastas sem áudio são ignoradas. O nome da pasta vira o nome do álbum quando a tag faltar.
3. **Nome do arquivo:** "Faixa 01" vira "Faixa 1". Um arquivo só com o título usa esse título.
4. **Capa:** a embutida; senão, `folder.jpg`, `cover.jpg` ou `front.jpg` (também `.png`) na pasta; senão, uma **capa substituta desenhada** com o nome do álbum em letras grandes e uma cor sólida derivada do nome (sempre a mesma cor para o mesmo álbum, com contraste de texto alto).
5. **Camada opcional do MusicBrainz**, quando já tiver sido obtida em uma conexão anterior (ver seção 9, "Rede opcional").

Outras regras:
- **Ordem das faixas:** número da faixa; sem número, ordem natural do nome do arquivo ("Faixa 2" antes de "Faixa 10").
- **Ordem da estante:** **por artista e, dentro do artista, por álbum** (decidido pelo autor). Coletâneas ficam em "Vários artistas"; sem tag de artista, o disco entra ordenado pelo nome do álbum (que vem da pasta se a tag faltar).
- **Músicas duplicadas:** **não remova nem esconda duplicatas automaticamente.** A identidade de uma faixa é o **caminho do arquivo**, e a mesma música em dois CDs (coletâneas) são duas faixas, cada uma no seu disco. Na busca da tela de playlist, mostre sempre o nome do disco ao lado da música para distinguir (já previsto no preview). Arquivos repetidos na **mesma pasta** só vão para o log, sem aviso ao idoso.
- **Formatos aceitos:** `.mp3`, `.flac`, `.ogg`, `.oga`, `.m4a`, `.wav`. Arquivos `.cda` não contêm áudio: ignore-os em silêncio e registre no log. O idoso não vê aviso nenhum.
- **A estante se atualiza sozinha:** a varredura roda em toda abertura. O cache com data de modificação de cada arquivo faz com que só o que mudou seja reprocessado.
- **Miniaturas:** gere as capas reduzidas uma vez (GdkPixbuf) e guarde no cache, para não decodificar JPEG grande a cada abertura.
- Escreva **testes pytest** para todos os fallbacks, com pastas de exemplo em `tests/fixtures/`. Os arquivos de áudio de teste podem ser curtos, gerados com GStreamer no próprio teste.

## 9. Regras de UX e acessibilidade (obrigatórias)

Referências: WCAG 2.2, Czaja et al. (2019), Hawthorn (2000) e a revisão de literatura do W3C (WAI-AGE).

**Estrutura**
- As telas principais são **Estante** (grade de capas) e **Tocando agora**, mais a tela de **Configurações** (ADR-0006), aberta por um botão com texto sempre visível no cabeçalho. Os fluxos de **montar um disco** e **cuidar da coleção** também ficam dentro da metáfora e do mesmo estilo. O número final de telas é decisão em aberto.
- O app **abre como uma janela de programa normal**, com barra de título e X visíveis (nem em tela cheia, que esconde o X). Ele abre direto na Estante ou, se havia algo tocando, em Tocando agora, no ponto em que parou.
- Fechar pelo X salva o estado e encerra. Não há botão de desligar.
- **Um caminho de volta sempre visível** em toda tela que não seja a Estante, com texto ("Voltar para a estante"). A tela atual também deve ser identificável de relance (título ou imagem do aparelho).
- **Um clique ativa** (`FlowBox.set_activate_on_single_click(True)`). Nenhuma ação depende de duplo clique, de passar o mouse por cima, de arrastar ou de clicar com o botão direito. Isso inclui o volume: nada de botão giratório que exija arrastar, e sim botões "−" e "+" com a imagem do botão do aparelho.

**Tamanhos e cores**
- Áreas clicáveis de **no mínimo 64×64 px**, bem acima do mínimo de 44×44 px do nível AAA da WCAG. Os botões principais (tocar/pausar) devem ser maiores.
- Fonte base de no mínimo **20 px**, títulos de 28 a 36 px. O **tamanho da letra** (Normal, Grande, Maior) e as **cores para daltonismo** ficam na tela de Configurações, que o próprio usuário abre sozinho (ADR-0006).
- Contraste de texto de **pelo menos 7:1** (WCAG nível AAA).
- Os **ícones imitam aparelhos de som antigos** (decisão do autor), mas vêm **sempre acompanhados de texto** ("Tocar", "Pausar", "Próxima", "Voltar para a estante").
- O foco do teclado tem que ser **bem visível** (borda grossa).

**Tela Tocando agora**
- Mostra a capa grande, o nome da música em letras grandes, o nome do disco e "Faixa X de Y", dentro da imagem de um **rádio** antigo.
- Botões: Tocar/Pausar, Anterior, Próxima, Volume − e Volume + com indicação visual do nível, **"Voz mais clara"** (liga/desliga, com o estado em texto; ADR-0004) e Voltar para a estante.
- O estado de tocando ou pausado tem que ser óbvio, com texto e não só ícone.

**Cuidar da coleção (feito pelo próprio usuário)**
- Adicionar, renomear, trocar a capa e remover discos, tudo dentro da metáfora, sem jargão (nada de "pasta", "tag" ou "varredura" na tela).
- O desenho exato é **decisão em aberto**. Será explorado com `ce-ideate` e validado em um **preview em HTML** antes de qualquer implementação.
- Operações destrutivas precisam ser reversíveis ou pedir confirmação calma. Remover um disco da estante **não deve apagar os arquivos de música** sem deixar isso claro. "Tirar da estante" leva o disco para a **Lixeira**; **"Apagar de vez" só existe dentro da Lixeira**, com texto claro e dois botões grandes (ADR-0007).

**Playlist (montar um disco)**
- O usuário cria um **disco novo na estante** a partir de músicas que já estão em outros discos. O resultado aparece na estante como qualquer outro disco, com capa e nome.
- Ele é **virtual**: guarda referências às faixas, sem copiar arquivos.
- Há **duas formas de criar**, decididas pelo autor:
  - **a. Botão grande "Criar uma playlist"** na Estante. Abre uma tela em que o usuário **marca as músicas** que vão para a playlist. **Ao começar a digitar, o texto vai direto para a barra de pesquisa**, sem precisar clicar nela antes, e filtra as músicas.
  - **b. Botão "+" em cada música**, quando o usuário está dentro de um CD. Abre duas opções: **"Adicionar a uma playlist existente"** e **"Criar uma nova playlist"**.
- O desenho visual das duas formas será explorado no `ce-ideate` e no preview em HTML.

**Comportamento**
- **Retomar automaticamente:** salve o disco, a faixa e a posição periodicamente e ao fechar.
- **Normalização de volume** com `rgvolume` (ReplayGain), quando houver tags de ReplayGain.
- **Sem modos escondidos:** não existe aleatório nem repetir na interface.
- **Impedir suspensão e descanso de tela durante a reprodução** com `Gtk.Application.inhibit`.
- **Instância única:** abrir o app de novo traz a janela existente para frente. O `Gtk.Application` faz isso via D-Bus.
- **Abertura automática com o sistema:** ligada por padrão na instalação.
- **Erros:** uma mensagem calma no próprio lugar, por exemplo "Não consegui tocar esta música. Vou tocar a próxima." Os detalhes técnicos vão para um arquivo de log, que o autor consulta fora do app.
- **Teclado:** espaço tocar/pausar, setas esquerda e direita anterior/próxima, setas cima e baixo volume. Os atalhos são uma comodidade, nunca o único caminho.

**Rede opcional (MusicBrainz)**
- Roda em **segundo plano**, em thread separada, só quando `Gio.NetworkMonitor` indicar conexão. Respeite o limite de 1 requisição por segundo.
- **Falha silenciosa:** sem internet, timeout ou erro vão só para o log.
- **Na dúvida, não muda nada.** Com ID do MusicBrainz nas tags, a consulta é exata. Sem ID, só aceite resultados de alta confiança.
- **Não desoriente o idoso:** as atualizações aparecem na **próxima abertura** da estante, e não enquanto ele olha para ela (decisão recomendada, aguardando confirmação).
- **Privacidade:** envie só o mínimo necessário (ID do disco ou artista e álbum). O cabeçalho de identificação do app é genérico, sem dados pessoais.

## 10. Metas de desempenho (a validar na máquina real)

| Métrica | Meta inicial |
| --- | --- |
| RAM em repouso com a estante aberta | Menor que Rhythmbox e VLC na mesma máquina |
| CPU média tocando MP3 | Abaixo de 5% |
| Abertura a frio (depois de reiniciar) | Até 3 s até a estante aparecer |
| Abertura a quente | Até 1 s |
| Tamanho instalado | Abaixo de 20 MB |

O `tools/measure.sh` deve medir esses números de forma repetível, por exemplo com `ps -o rss`, `pidstat` (pacote `sysstat`) e o tempo até a janela aparecer, e gravar um CSV com data e configuração da máquina. Esses dados vão para o capítulo de Resultados.

## 11. Decisões em aberto (pergunte ao autor)

**Já decididas pelo autor** (não perguntar de novo):
- Sem cuidador e sem modo escondido; o usuário faz tudo sozinho.
- Linha visual: estante de CDs, com ícones de tocadores de música antigos.
- O X da janela fica; não há botão de desligar.
- A manutenção da coleção é feita pelo próprio usuário, idoso ou não.
- Caminho de volta sempre visível.
- Playlist = criar um novo disco na estante a partir de faixas já existentes, de duas formas: botão grande "Criar uma playlist" (marcar músicas, com digitação indo direto para a pesquisa) e botão "+" em cada música dentro de um CD (adicionar a uma existente ou criar nova).
- A estante mostra os álbuns como uma **estante de músicas**, e **tocar usa um rádio antigo** como base.
- O app abre como **janela de programa normal** (não tela cheia).
- MusicBrainz é opcional e oportunista; o app funciona 100% offline.
- Este escopo vale para o MVP.
- **Licença: GNU GPL versão 3 ou posterior** (software livre), titular Leonardo dos Santos Barcella, 2026, com o repositório público `lsbarcella/moa-media-player` no GitHub. **Todo arquivo `.py` ou `.sh` novo deve começar com o cabeçalho de três linhas** (copie de qualquer arquivo existente); um teste confere. O `LICENSE` não é editado. Ver ADR-0009.
- **Nome: Moa Media Player.** O autor escolheu o nome completo, sabendo que "Media Player" é genérico e em inglês. Pacote `moa`, ID `br.tcc.Moa`.
- **Expansão futura:** depois do MVP, o autor pretende expandir para vídeos e fotos. Vídeo num notebook antigo é bem mais pesado que áudio e exigirá medição e um ADR antes de qualquer promessa.
- **Audição:** o rádio terá um botão **"Voz mais clara"** (liga/desliga, estado em texto), que reforça agudos e voz. É a opção B1 do ADR-0004; pode evoluir para um controle "Tom" (B2) se o teste mostrar que não basta.
- **Perfil do usuário definido só por literatura** (ADR-0005). A IA havia recomendado questionário seguido de observação; o autor escolheu só a literatura.
- **Dispositivo apontador: mouse** (o usuário usa mouse, não touchpad).
- **Cada CD tem uma pasta própria**; as duplicadas são a mesma música em CDs diferentes (mantidas, cada uma no seu disco).
- **Ordem da estante: por artista e depois álbum.**
- **Persistência em SQLite** para o cache da biblioteca e os dados do usuário (discos montados, Lixeira, recentes, onde parou); **JSON** só para as configurações legíveis (letra, cores, "Voz mais clara"). Ver ADR-0008. O acervo tem cerca de **800 faixas**.
- **"Voz mais clara" começa desativado.** Os valores do ajuste ainda precisam ser testados com ele ouvindo.
- **Volume:** é o do app, com limite em 100% (sem ganho acima disso), e o volume do sistema é ajustado uma vez na instalação.
- **Botão "+" em cada música:** mostra as **capas dos discos** ("Em qual disco?"), com um "Disco novo" como primeira capa, no lugar das duas frases (ADR-0007).
- **"Apagar de vez" só dentro da Lixeira** (ADR-0007).
- **Tamanho da letra** fica dentro de um botão **"Configurações"** (ADR-0006).
- **Configuração para daltonismo**, como camada extra de acessibilidade, também dentro de "Configurações" (ADR-0006).
- **As demais opções do preview ficam na primeira alternativa** (padrão): o visor do rádio diz o estado ("TOCANDO: Faixa 3 de 12"); avisos e confirmações ficam até a próxima ação; a "estante que lembra" (continuar a ouvir, ouvidos há pouco e lugar vazio) fica ligada.
- Aceitas pelo autor "por enquanto" (podem ser revistas): o que vem do MusicBrainz fica só no cache do app, sem reescrever tags; atualizações aparecem na próxima abertura; API via `urllib` do Python, sem dependência nova; conexão detectada com `Gio.NetworkMonitor`; discos montados são virtuais (referências, sem copiar arquivos).

**Recomendadas por mim, aguardando confirmação:**
- Detalhe de pesquisa: tratar o skeuomorfismo como **hipótese com evidência mista** (Urbano 2022 a favor, Ellis & Marshall 2019 contra), a validar com o usuário.

**Em aberto:**
- Licença da arte do ícone e da documentação (ADR-0009).
- Valores do ajuste "Voz mais clara" (o estado padrão é desativado); precisam ser testados com ele ouvindo.
- **Desenho visual dos botões, dos ícones e das telas** (inclusive da manutenção da coleção: adicionar, renomear, trocar capa, remover). Será explorado com `ce-ideate`, seguido de um preview em HTML.
- Confirmação ao fechar pelo X (por padrão, não há).
- Se os usuários acham o botão "Configurações" no teste (a literatura recomenda o controle de letra visível), e se as paletas de daltonismo funcionam para uma pessoa daltônica real.
- Mostrar ou não a barra de progresso da música, e se ela é clicável.
- Comportamento ao fim do disco: parar ou voltar para a estante.
- Paleta de cores e tema (claro, escuro ou alto contraste).
- Versão do Linux Mint e especificações do notebook do usuário (CPU, RAM, tipo de disco), (o leitor de CD **existe**, confirmado pelo autor em 27/11/2026; falta a versão do Mint, a CPU, a RAM e o tipo de disco).

## 12. Roteiro de implementação

Siga em ordem. Termine cada marco com algo executável, uma explicação ao autor e uma entrada em `docs/registro-ia.md`.

1. **M0 – Base** (feito): repositório, estrutura de pastas, `README.md`, `tools/check_deps.sh` e janela vazia, como janela normal de programa (ajuste de tela cheia já feito em 26/11/2026).
2. **M1 – Biblioteca:** `core/library.py`, `models.py` e `covers.py`, com todos os fallbacks da seção 8 e testes pytest passando.
3. **M2 – Reprodução:** `core/player.py` (tocar um álbum, próxima, anterior, volume, ReplayGain, "Voz mais clara") e `core/state.py` (retomar). Testes do que for testável sem áudio real.
4. **M3 – Telas principais:** Estante e Tocando agora, com `style.css` seguindo a seção 9 e os ícones de aparelhos antigos.
5. **M4 – Cuidar da coleção e montar discos:** os dois fluxos do próprio usuário (`core/custom_albums.py` e as telas correspondentes). **Antes de começar, fazer o `ce-ideate` e o preview em HTML do desenho (seção 11) e obter a aprovação do autor.**
6. **M5 – Robustez:** erros amigáveis, log, instância única, inibir suspensão e abertura automática (`~/.config/autostart/`).
7. **M6 – Rede opcional:** `core/musicbrainz.py`, fila de pendências, atualização em segundo plano, testes com respostas falsas.
8. **M7 – Colocar um disco (copiar CD):** `core/ripper.py` e a tela correspondente. O disco entra offline como "Disco N", e o M6 o atualiza quando houver internet. **O notebook do usuário tem leitor de CD (confirmado em 27/11/2026), então o marco está liberado.** Se o prazo apertar, este marco é o primeiro a ser cortado, depois o M6.
9. **M8 – Empacotamento (`.deb`):** `tools/build_deb.sh` gera `dist/moa-media-player_VERSAO_all.deb` com o app, o comando `moa`, o `.desktop`, o ícone e as dependências declaradas (ADR-0019). Testar a instalação **sem internet** e numa máquina limpa (no notebook do usuário, Mint XFCE).
10. **M10 – Instaladores (depois do MVP, pedido pelo autor em 27/11/2026):** o autor **quer instaladores**, para ninguém rodar `apt`, clonar repositório nem resolver pacote à mão.
    - **Linux, sem internet:** um instalador executável (`.run`) que leva junto os `.deb` das dependências da **versão exata do Mint** do notebook. Depende de saber essa versão.
    - **Windows (prioridade do autor para depois):** instalador para Windows. O caminho técnico é **decisão em aberto** (preview das opções em 27/11/2026): A) mesma stack GTK 3 + GStreamer empacotada com MSYS2 (código quase igual, instalador grande), B) outro toolkit (reescreve `ui/`, não recomendado), C) só isolar o que é específico de Linux no código (autostart, inibição de suspensão, rede, pasta de música, `.deb`). Qualquer opção exige ADR e quebra a meta de 20 MB no Windows.
11. **M9 – Avaliação:** `tools/measure.sh` e `docs/testes-usabilidade.md` com o roteiro de tarefas (ex.: "toque o disco X", "pause", "volte para a estante", "monte um disco com estas músicas"), a planilha de tempo e erros e o questionário SUS em português.

## 13. Comandos

```bash
# Dependências no Linux Mint
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gstreamer-1.0 \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good python3-mutagen python3-pytest

# Executar
python3 -m moa

# Testes
python3 -m pytest
```
