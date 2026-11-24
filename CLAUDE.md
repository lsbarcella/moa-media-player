# CLAUDE.md — Reprodutor de música acessível para idosos (TCC)

Este arquivo dá ao Claude Code o contexto do projeto. Leia-o inteiro antes de qualquer tarefa.

## 1. O projeto em uma frase

Um reprodutor de música **offline**, **leve** e **acessível para idosos**, que roda no **Linux Mint (Cinnamon)** em notebooks antigos. A interface imita uma **estante de CDs**: o usuário clica na capa de um disco e ele toca inteiro.

Nome de trabalho: **Estante**. O nome definitivo ainda não foi escolhido. Use `estante` como nome do pacote Python e `br.tcc.Estante` como application ID até o autor decidir.

## 2. Contexto

- **Usuário primário:** um idoso (o pai do autor) que quer ouvir sua coleção de CDs, já copiada para o notebook dele.
- **Usuário secundário (cuidador):** o autor. Ele adiciona discos, corrige nomes e capas e ajusta preferências.
- **Finalidade acadêmica:** é o TCC de Engenharia de Software (Uninter). O foco do trabalho são as **decisões de UX, acessibilidade e arquitetura**. O código materializa essas decisões.
- **Acervo:** cerca de 80% dos arquivos têm tags completas, feitas com o MusicBrainz Picard. O restante tem nomes como "Faixa 01" ou só o título da música. **Ainda não se sabe se há uma pasta por CD.** Pergunte ao autor antes de depender disso.

## 3. Como trabalhar com o autor (leia com atenção)

- **O autor decide UX, UI e arquitetura. Você implementa.** Quando surgir uma escolha que afete o usuário ou a arquitetura, apresente 2 ou 3 opções com prós e contras e uma recomendação, e **espere a decisão**. Não decida sozinho coisas listadas em "Decisões em aberto" (seção 10).
- **O autor sabe TypeScript, não sabe Python.** Ao final de cada etapa, explique em linguagem simples o que o código faz. Quando ajudar, compare com TypeScript ("isto é como uma interface em TS", "isto é como um callback/evento").
- **Ele vai defender o código perante uma banca.** O código precisa ser legível, sem esperteza desnecessária. Prefira clareza a concisão.
- **Registre cada decisão relevante como ADR** em `docs/adr/NNNN-titulo.md`, no formato do ADR-001: contexto, alternativas, decisão, consequências.
- **Mantenha `docs/registro-ia.md`**, um diário curto de cada sessão: data, o que foi pedido, o que foi feito e quais decisões foram tomadas. Ele vai para o apêndice do TCC, como declaração de uso de IA.
- **Nunca escreva o texto do artigo do TCC.** Ajudar com documentação técnica é permitido (README, ADRs, comentários). Redigir parágrafos do artigo não é. Se o autor pedir isso, lembre-o de que trechos não autorais podem ser penalizados pela Uninter.
- Faça commits pequenos, com mensagens em português no imperativo (ex.: "Adiciona leitura de tags com mutagen").

## 4. Restrições não negociáveis

1. **Zero rede em tempo de execução.** O app não pode fazer nenhuma requisição, nem telemetria, nem buscar capas online.
2. **Leveza.** Rodar bem em CPU antiga, com pouca RAM, HD mecânico e GPU integrada antiga.
3. **Sem dependências novas sem ADR.** Use só o que está nos repositórios do Linux Mint (apt). Nada de `pip install` em tempo de execução.
4. **Compatível com Python 3.10 ou mais recente** (Mint 21 usa 3.10; Mint 22 usa 3.12).
5. **Nenhuma mensagem técnica para o idoso.** Nada de stack trace, diálogo de erro com jargão ou janela modal inesperada.

## 5. Stack (ver `docs/adr/0001-escolha-da-stack.md`)

| Componente | Uso | Pacote apt |
| --- | --- | --- |
| Python 3 | Linguagem | `python3` |
| GTK 3 via PyGObject | Interface | `python3-gi`, `gir1.2-gtk-3.0` |
| GStreamer 1.x | Reprodução de áudio e ReplayGain (`rgvolume`) | `gir1.2-gstreamer-1.0`, `gstreamer1.0-plugins-base`, `gstreamer1.0-plugins-good` |
| mutagen | Tags e capas (MP3, FLAC, OGG) | `python3-mutagen` |
| pytest | Testes (só no ambiente de desenvolvimento) | `python3-pytest` |

- Use **GTK 3, não GTK 4**, porque o GTK 4 depende de aceleração gráfica que pode falhar em GPU antiga.
- Comece com `gi.require_version("Gtk", "3.0")` e `gi.require_version("Gst", "1.0")`.
- Reproduza com o elemento `playbin`, desligando o vídeo nos flags.
- Para o ambiente virtual de desenvolvimento, use `python3 -m venv --system-site-packages .venv`, já que o PyGObject vem do apt.

## 6. Arquitetura

A lógica fica separada da interface. **O núcleo (`core/`) não importa GTK**, para poder ser testado sem tela.

```
estante/
├── CLAUDE.md
├── README.md
├── docs/
│   ├── adr/                # Registros de decisão
│   ├── registro-ia.md      # Diário das sessões com IA
│   └── testes-usabilidade.md
├── estante/
│   ├── __main__.py         # Ponto de entrada: python3 -m estante
│   ├── app.py              # Gtk.Application (garante instância única)
│   ├── core/
│   │   ├── library.py      # Varre pastas e monta álbuns e faixas (com fallbacks)
│   │   ├── models.py       # dataclasses: Album, Track
│   │   ├── covers.py       # Capa embutida, folder.jpg ou capa substituta
│   │   ├── player.py       # Envolve o GStreamer: tocar, pausar, próxima, volume
│   │   ├── state.py        # Salva e restaura onde parou (JSON)
│   │   └── config.py       # Preferências do cuidador (JSON)
│   └── ui/
│       ├── window.py       # Janela principal e navegação entre telas
│       ├── shelf_view.py   # Tela "estante": grade de capas
│       ├── player_view.py  # Tela "tocando agora"
│       ├── caregiver.py    # Modo cuidador (escondido)
│       └── style.css       # Tamanhos, cores e contraste
├── tests/                  # pytest, com pastas de música de exemplo
├── tools/
│   ├── check_deps.sh       # Verifica se a máquina-alvo tem tudo instalado
│   └── measure.sh          # Mede RAM, CPU e tempo de abertura
└── packaging/              # .desktop, ícone, autostart, scripts do .deb
```

Use `GLib.get_user_data_dir()` (para estado e cache) e `GLib.get_user_config_dir()` (para preferências), sempre numa subpasta `estante/`. A pasta de música padrão é a do sistema, `GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC)`, que no Mint em português é `~/Música`. O cuidador pode trocá-la.

## 7. Regras de montagem da estante

A ordem de preferência para cada informação é:

1. **Tags do arquivo**, lidas com mutagen: artista do álbum (ou artista), álbum, número da faixa, título e capa embutida.
2. **Estrutura de pastas:** pasta = álbum. O nome da pasta vira o nome do álbum quando a tag faltar.
3. **Nome do arquivo:** "Faixa 01" vira "Faixa 1". Um arquivo só com o título usa esse título.
4. **Capa:** a embutida; senão, `folder.jpg`, `cover.jpg` ou `front.jpg` (também `.png`) na pasta; senão, uma **capa substituta desenhada** com o nome do álbum em letras grandes e uma cor sólida derivada do nome (sempre a mesma cor para o mesmo álbum, com contraste de texto alto).

Outras regras:
- **Ordem das faixas:** número da faixa; sem número, ordem natural do nome do arquivo ("Faixa 2" antes de "Faixa 10").
- **Ordem da estante:** alfabética por nome do álbum ou do artista. Essa escolha é uma decisão em aberto.
- **Formatos aceitos:** `.mp3`, `.flac`, `.ogg`, `.oga`, `.m4a`, `.wav`. Arquivos `.cda` não contêm áudio: ignore-os e mostre um aviso **no modo cuidador**.
- **Cache:** guarde o resultado da varredura com a data de modificação de cada arquivo, para a abertura ser rápida. Reprocesse só o que mudou.
- **Miniaturas:** gere as capas reduzidas uma vez (GdkPixbuf) e guarde no cache, para não decodificar JPEG grande a cada abertura.
- Escreva **testes pytest** para todos os fallbacks, com pastas de exemplo em `tests/fixtures/`. Os arquivos de áudio de teste podem ser curtos, gerados com GStreamer no próprio teste.

## 8. Regras de UX e acessibilidade (obrigatórias)

Referências: WCAG 2.2, Czaja et al. (2019), Hawthorn (2000) e a revisão de literatura do W3C (WAI-AGE).

**Estrutura**
- São só duas telas para o idoso: **Estante** (grade de capas) e **Tocando agora**.
- O app **abre em tela cheia**, direto na Estante ou, se havia algo tocando, em Tocando agora, no ponto em que parou.
- **Um clique ativa** (`FlowBox.set_activate_on_single_click(True)`). Nenhuma ação depende de duplo clique, de passar o mouse por cima, de arrastar ou de clicar com o botão direito.

**Tamanhos e cores**
- Áreas clicáveis de **no mínimo 64×64 px**, bem acima do mínimo de 44×44 px do nível AAA da WCAG. Os botões principais (tocar/pausar) devem ser maiores.
- Fonte base de no mínimo **20 px**, títulos de 28 a 36 px. O cuidador pode aumentar a escala.
- Contraste de texto de **pelo menos 7:1** (WCAG nível AAA).
- Os ícones vêm **sempre acompanhados de texto** ("Tocar", "Pausar", "Próxima", "Voltar para a estante").
- O foco do teclado tem que ser **bem visível** (borda grossa).

**Tela Tocando agora**
- Mostra a capa grande, o nome da música em letras grandes, o nome do disco e "Faixa X de Y".
- Botões: Tocar/Pausar, Anterior, Próxima, Volume − e Volume + com indicação visual do nível, e Voltar para a estante.
- O estado de tocando ou pausado tem que ser óbvio, com texto e não só ícone.

**Comportamento**
- **Retomar automaticamente:** salve o disco, a faixa e a posição periodicamente e ao fechar.
- **Normalização de volume** com `rgvolume` (ReplayGain), quando houver tags de ReplayGain.
- **Sem modos escondidos para o idoso:** não existe aleatório nem repetir na interface dele.
- **Impedir suspensão e descanso de tela durante a reprodução** com `Gtk.Application.inhibit`.
- **Instância única:** abrir o app de novo traz a janela existente para frente. O `Gtk.Application` faz isso via D-Bus.
- **Erros:** uma mensagem calma no próprio lugar, por exemplo "Não consegui tocar esta música. Vou tocar a próxima." Os detalhes técnicos vão para um arquivo de log, que só o modo cuidador mostra.
- **Teclado:** espaço tocar/pausar, setas esquerda e direita anterior/próxima, setas cima e baixo volume. Os atalhos são uma comodidade, nunca o único caminho.

**Modo cuidador**
- Fica escondido atrás de um atalho, por exemplo Ctrl+Alt+C (decisão em aberto).
- Permite escolher a pasta de música, varrer a biblioteca de novo, ajustar a escala da fonte, ver avisos (arquivos `.cda`, discos sem capa, faixas sem tag), ver o log e ligar ou desligar a abertura automática com o sistema.
- O idoso nunca deve cair nele por acidente.

## 9. Metas de desempenho (a validar na máquina real)

| Métrica | Meta inicial |
| --- | --- |
| RAM em repouso com a estante aberta | Menor que Rhythmbox e VLC na mesma máquina |
| CPU média tocando MP3 | Abaixo de 5% |
| Abertura a frio (depois de reiniciar) | Até 3 s até a estante aparecer |
| Abertura a quente | Até 1 s |
| Tamanho instalado | Abaixo de 20 MB |

O `tools/measure.sh` deve medir esses números de forma repetível, por exemplo com `ps -o rss`, `pidstat` (pacote `sysstat`) e o tempo até a janela aparecer, e gravar um CSV com data e configuração da máquina. Esses dados vão para o capítulo de Resultados.

## 10. Decisões em aberto (pergunte ao autor)

- Nome definitivo do app.
- O idoso pode fechar o app? Se sim, como evitar fechar por engano?
- Atalho do modo cuidador.
- Ordem da estante: por álbum ou por artista.
- Mostrar ou não a barra de progresso da música, e se ela é clicável.
- Comportamento ao fim do disco: parar ou voltar para a estante.
- Paleta de cores e tema (claro, escuro ou alto contraste).
- Formato do cache: JSON ou SQLite.
- Versão do Linux Mint e especificações do notebook do usuário (CPU, RAM, tipo de disco).

## 11. Roteiro de implementação

Siga em ordem. Termine cada marco com algo executável, uma explicação ao autor e uma entrada em `docs/registro-ia.md`.

1. **M0 – Base:** repositório, estrutura de pastas, `README.md` com o comando de execução, `tools/check_deps.sh` e uma janela vazia em tela cheia rodando com `python3 -m estante`.
2. **M1 – Biblioteca:** `core/library.py`, `models.py` e `covers.py`, com todos os fallbacks da seção 7 e testes pytest passando.
3. **M2 – Reprodução:** `core/player.py` (tocar um álbum, próxima, anterior, volume, ReplayGain) e `core/state.py` (retomar). Testes do que for testável sem áudio real.
4. **M3 – Telas do idoso:** Estante e Tocando agora, com `style.css` seguindo a seção 8.
5. **M4 – Modo cuidador.**
6. **M5 – Robustez:** erros amigáveis, log, instância única, inibir suspensão e abertura automática (`~/.config/autostart/`).
7. **M6 – Empacotamento:** arquivo `.desktop`, ícone e um pacote `.deb` com as dependências declaradas. Testar a instalação **sem internet**.
8. **M7 – Avaliação:** `tools/measure.sh` e `docs/testes-usabilidade.md` com o roteiro de tarefas (ex.: "toque o disco X", "pause", "volte para a estante"), a planilha de tempo e erros e o questionário SUS em português.

## 12. Comandos

```bash
# Dependências no Linux Mint
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gstreamer-1.0 \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good python3-mutagen python3-pytest

# Executar
python3 -m estante

# Testes
python3 -m pytest
```
