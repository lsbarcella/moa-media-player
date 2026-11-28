# Registro de uso de IA

Diário curto de cada sessão com o assistente de IA (Claude Code), para o apêndice do TCC.

## 24/11/2026 — M0: base do projeto

- **Pedido:** seguir o CLAUDE.md, inicializar repositório e projeto.
- **Feito:** repositório git, estrutura de pastas, README, `tools/check_deps.sh`, janela vazia em tela cheia (`python3 -m estante`). ADR-0001 movido para `docs/adr/`.
- **Decisões:** raiz do repositório é a própria pasta `TCC`, com o pacote `estante/` dentro. Nenhuma decisão em aberto foi tomada.

## 26/11/2026 — Revisão do plano (sem código)

- **Pedido:** revisar como o CLAUDE.md propunha desenvolver o software. O autor apontou que o plano contradizia o objetivo: o app deve dar autonomia ao idoso, sem depender de cuidador, reaproveitando imagens mentais do mundo real.
- **Feito:** o CLAUDE.md foi reescrito. Saem o modo cuidador e o marco M4 antigo. Entram o princípio de autonomia por modelos mentais, a rede opcional, os fluxos de manutenção da coleção e de montar discos (playlist) e os marcos de rede opcional (M6) e de copiar CDs (M7). Criados o ADR-0002 (modelos mentais) e o ADR-0003 (rede opcional). Também foi levantado o custo de copiar CDs dentro do app.
- **Decisões do autor:** linha de estante de CDs com ícones de aparelhos antigos; o X da janela permanece e não há botão de desligar; a manutenção da coleção é feita pelo próprio usuário; caminho de volta sempre visível; playlist é um novo disco na estante; o MusicBrainz pode ser usado quando houver internet, e o app funciona 100% offline; tudo isso vale para o MVP.
- **Recomendações da IA ainda não confirmadas:** o que vem do MusicBrainz fica só no cache; atualizações aparecem na próxima abertura; `urllib` em vez de biblioteca nova; discos montados são virtuais.
- **Apontado pela IA:** o M0 atual usa tela cheia, o que esconde o X.

## 26/11/2026 — Decisões de UX e ajuste do M0

- **Pedido:** o autor esclareceu que o app deve abrir como janela de programa normal; definiu o desenho de alto nível da playlist e da tela de tocar; aceitou as 5 recomendações da IA "por enquanto".
- **Feito:** `window.py` deixou de chamar `fullscreen()` e abre como janela normal (1024×700). CLAUDE.md e ADRs 0002 e 0003 atualizados.
- **Decisões do autor:** (1) botões, ícones e telas serão explorados com `ce-ideate` e validados em preview HTML; (2a) botão grande "Criar uma playlist", com marcação de músicas e digitação indo direto para a pesquisa; (2b) botão "+" em cada música dentro de um CD, com "adicionar a uma playlist existente" e "criar nova playlist"; (3) estante de músicas para os álbuns e um rádio como base para tocar; as 5 recomendações da IA foram aceitas por enquanto.

## 26/11/2026 — Ideação de UI e conferência com a literatura

- **Pedido:** rodar `ce-ideate` para botões, ícones e telas; depois, antes dos previews visuais, buscar literatura na internet e conferir os documentos e o plano contra ela.
- **Feito:** ideação com 5 agentes de ideação, 1 de pesquisa web e 1 verificador (7 ideias sobreviventes, em `docs/ideation/`). Pesquisa de literatura em ~25 buscas; só a revisão da W3C (WAI-AGE) foi lida por inteiro, o resto vem de resumos de busca e precisa ser conferido nas fontes antes de ir ao artigo. Nenhum texto do artigo foi escrito.
- **Decisões do autor (após opções com prós e contras):** audição = botão "Voz mais clara" (opção B1, ADR-0004); perfil do usuário = só literatura (opção P3, ADR-0005). A IA havia recomendado, para o perfil, questionário seguido de observação (P4); o autor escolheu P3. O `equalizer-3bands` foi confirmado no `gstreamer1.0-plugins-good` da máquina de desenvolvimento.
- **Preview visual:** criado `docs/preview/moa-preview.html`, uma maquete interativa (HTML único, sem som) com as 7 ideias, painel de variantes (visor, "+", avisos, "apagar de vez", estante que lembra, controle de letra) e o botão "Voz mais clara". Respostas do autor: usa mouse; volume é o do app; "Voz mais clara" começa desativado. Verificação: paleta conferida (todos os pares de 7:1 ou mais), todos os fluxos percorridos por script sem erro, texto conferido em 20 px ou mais e alvos em 64 px ou mais (exceto a barra de título do sistema). Corrigidos na revisão: capa pequena no visor, textos abaixo de 20 px e mosaico vazio dos discos montados.
- **Decisões do autor após o preview:** o "+" mostra as capas dos discos; "Apagar de vez" só dentro da Caixa; o tamanho da letra fica dentro de um botão "Configurações", que também terá uma opção de cores para daltonismo; as demais opções ficam na primeira alternativa (visor diz o estado, avisos ficam até a próxima ação, estante que lembra ligada). Registrado nos ADR-0006 e ADR-0007 e no CLAUDE.md. O preview foi atualizado com a tela de Configurações e quatro paletas (normal, vermelho e verde, azul e amarelo, preto e branco), todas com contraste de 7:1 ou mais conferido no navegador. Corrigido na revisão: com a letra Grande os botões Anterior e Próxima estouravam; agora as colunas se empilham. As paletas de daltonismo não foram validadas com simulador nem com uma pessoa daltônica.
- **Acervo (resposta do autor):** cada CD foi ripado para uma pasta própria, então "pasta = disco" vale; há algumas músicas duplicadas. Registrado no CLAUDE.md: toda pasta com áudio é um disco em qualquer profundidade; duplicatas não são removidas automaticamente.
- **Decisões do M1 (autor):** ordem da estante por artista e depois álbum; duplicadas são a mesma música em CDs diferentes; cache em SQLite. A IA havia recomendado JSON; o autor perguntou se SQLite não seria o certo e informou ~800 faixas. A IA mediu (JSON 1,3 ms, SQLite 1,1 ms, diferença desprezível), reconsiderou porque o app passou a guardar mais dados do usuário (discos montados, Caixa, recentes, onde parou) e concordou com SQLite. Registrado no ADR-0008.
- **Resultado:** o plano está alinhado com a literatura em vários pontos (sem duplo clique, alvos grandes, texto nos ícones, preferir selecionar a digitar). Lacunas e pontos contestados foram levantados para decisão do autor (audição, perfil do usuário, dispositivo apontador, tamanho da letra, tema, avaliação e ética).

## 26/11/2026 — M1: biblioteca (partes 1 a 4)

- **Pedido:** começar o M1 em partes e commitar ao terminar cada uma.
- **Feito:** (1) modelos `Track` e `Album` e utilitários de ordenação; (2) leitor de pastas e tags com todos os fallbacks (tag, pasta, nome do arquivo); (3) capas (embutida, imagem da pasta, capa substituta como dado) e miniaturas com o GdkPixbuf; (4) banco SQLite com migrações, varredura incremental e cache de capas. 145 testes pytest passando em cerca de 0,7 s, com áudio gerado pelo GStreamer.
- **Verificação:** para as partes 2 a 4, regras importantes foram quebradas de propósito (teste de mutação) para confirmar que os testes as detectam; um teste circular foi trocado por valores fixos.
- **Medição (máquina de desenvolvimento, coleção sintética de 80 discos e 800 faixas, cache de arquivos aquecido):** primeira abertura cerca de 1,4 s; aberturas seguintes cerca de 35 ms. **Não vale para o notebook real com HD mecânico a frio**, que precisa ser medido no M9.
- **Decisões de implementação (sem pedir ao autor, por serem detalhes internos):** olhar até 3 faixas atrás de capa embutida; artista do disco é o que aparece em mais da metade das faixas, senão "Vários artistas"; a capa substituta é só dado (a interface desenha); miniaturas em PNG de até 256 px, geradas uma vez; banco corrompido é guardado ao lado e recriado, nunca apagado.
- **Limitação conhecida:** a leitura de capa embutida em `.m4a` está implementada, mas não testada, porque esta máquina não tem codificador AAC para gerar o arquivo de teste.

## 26/11/2026 — Nome do aplicativo: Moa Media Player

- **Pedido:** o autor propôs o nome "Moa Media Player" (homenagem ao pai, Moacir; ícone de uma moa, ave extinta, com fones de ouvido) e perguntou a opinião da IA. Depois pediu nomes mais generalistas, porque pretende expandir para vídeos e fotos. A IA sugeriu alternativas ("Moa", "Estante do Moa", "Baú do Moa", "Casa do Moa" e outras), com prós e contras, e recomendou o nome curto e um pacote sem "music" nem "player". O autor decidiu ficar com **Moa Media Player**.
- **Feito:** pacote renomeado de `estante` para `moa`, application ID `br.tcc.Moa`, comando `python3 -m moa`, título da janela, README, CLAUDE.md, ADR-0008 e o preview (agora `docs/preview/moa-preview.html`). A tela inicial continua se chamando "Estante". A ideação (`docs/ideation/`) foi mantida como registro datado, com o nome antigo.
- **Verificação:** 145 testes passando; o app abre (rodou até o timeout). Uma busca web limitada não achou aplicativo com o mesmo nome; a marca não foi consultada. A IA avisou que "Moa" evoca no Brasil o Mestre Moa do Katendê, o que não é conflito de nome.
- **Tropeço corrigido:** o primeiro commit da renomeação saiu só com os renomes de arquivo, sem as trocas de import, por um erro de comando da IA (o comando listava a pasta antiga, que não existia mais). Foi percebido antes de qualquer envio e corrigido com `--amend`.

## 26/11/2026 — Licença GPL v3 e repositório no GitHub

- **Pedido:** o autor criou o repositório público `lsbarcella/moa-media-player` com a licença GNU GPL v3 (quer software livre) e pediu o envio do trabalho para lá.
- **Feito:** o histórico local foi colocado depois do commit inicial do remoto (`LICENSE`), com `git rebase`, sem conflitos e com os 145 testes passando. Conferida a compatibilidade das dependências com a GPL v3. O mutagen aparece como "GPL-2" no pacote do Debian, mas o código-fonte e os metadados dizem "versão 2 ou posterior", então é compatível. Criados o ADR-0009, a seção "Licença" do README e a restrição 7 do CLAUDE.md.
- **Pendências para o autor:** escolher entre "somente GPL v3" e "GPL v3 ou posterior" antes de pôr cabeçalhos nos arquivos-fonte; definir a licença da arte do ícone.

## 26/11/2026 — Correção da identidade nos commits

- **Problema:** os commits foram gravados com um e-mail do autor que não era o da conta do GitHub, então o GitHub não ligava os commits à conta (sem foto), e esse e-mail ficou público no histórico. A causa foi a configuração local do git, que a IA não conferiu antes do primeiro push.
- **Correção (autorizada pelo autor):** configurado o e-mail da conta do GitHub, reescrito o autor dos 14 commits (conteúdo e datas de autoria preservados, conferidos por comparação das árvores) e feito `force push` com trava de segurança.
- **Lição para a IA:** conferir `git config user.email` e perguntar ao autor se é o e-mail certo antes do primeiro push para um repositório público.

## 26/11/2026 — Aviso de direitos autorais

- **Pedido:** o autor quis colocar o nome completo e o ano na licença. A IA explicou que o `LICENSE` é o texto oficial da GPL e não deve ser editado; o nome e o ano vão no README e nos cabeçalhos dos arquivos.
- **Decisões do autor:** titular Leonardo dos Santos Barcella, ano 2026, GPL v3 **ou posterior**.
- **Feito:** cabeçalho de três linhas em 19 arquivos-fonte, seção de direitos autorais no README, ADR-0009 atualizado e o teste `tests/test_license_headers.py`, que falha se um arquivo novo ficar sem o cabeçalho.

## 26/11/2026 — M2: reprodução (execução autônoma do MVP, `lfg`)

- **Pedido:** montar todo o MVP (M2 a M9) antes dos reviews, seguindo o plano `docs/plans/2026-11-26-0653-feat-moa-mvp-m2-a-m9-plan.md`, em um ramo `mvp`.
- **Feito:** `core/player.py` (fila do disco, volume em 11 posições com curva cúbica e teto 1.0, ReplayGain, "Voz mais clara" desligada por padrão, erro numa faixa pula para a próxima, fim do disco para), `core/state.py` (onde parou e recentes), `core/config.py` (JSON com gravação atômica) e a migração 2 do banco. ADR-0010.
- **Verificação:** 183 testes passando. Teste de mutação nas três regras mais delicadas (teto do volume, fim do disco, pulo no erro): os testes falharam como esperado.
- **Decisões provisórias** (a revisar pelo autor): curva e padrão do volume, ganhos de "Voz mais clara" (−3, +3, +6 dB), fim do disco para.
- **NÃO testado:** som real, ReplayGain com arquivos reais, qualidade do equalizador.

## 26/11/2026 — M3: telas principais

- **Pedido:** continuar o MVP: Estante, Tocando agora e Configurações, seguindo o preview aprovado.
- **Feito:** `core/session.py` (navegação e avisos que ficam até a próxima ação), `core/radio.py` (as frases do visor, testáveis sem janela), `core/contexto.py`, `ui/theme.py` (4 paletas e 3 tamanhos de letra gerados em Python, contraste 7:1 testado), `ui/window.py` (cabeçalho fixo, mini-rádio, atalhos de teclado), `ui/shelf_view.py`, `ui/radio_view.py`, `ui/settings_view.py`, `ui/loader.py` (varredura em segundo plano, uma conexão de banco por thread), 10 ícones SVG originais e `tools/make_synthetic_collection.py` (80 discos, 800 faixas, para verificar sem usar a coleção real). ADR-0011.
- **Verificação:** 247 testes; as telas foram desenhadas fora da tela (`Gtk.OffscreenWindow`) e os PNGs foram olhados; `timeout 5 python3 -m moa` abre (código 124). Teste de mutação em três regras (aviso até a próxima ação, contraste das paletas, limite do volume): os testes falharam como esperado.
- **Bug achado pelos testes:** dar "Tocar" num disco pausado não registrava o disco em "Ouvidos há pouco"; corrigido.
- **Decisões provisórias:** progresso só em texto, fim do disco para, tema claro, X do sistema, abre sempre na Estante com "Continuar a ouvir" (ADR-0011).
- **NÃO testado:** aparência no monitor real do notebook, X do Cinnamon, HD mecânico, paletas de daltonismo com simulador ou pessoa daltônica.

## 26/11/2026 — M4 (parte 1): dados dos discos montados e da Caixa

- **Feito:** migração 3 do banco, `MixDisc`, `core/custom_albums.py` (criar, adicionar sem duplicar, remover, nome sugerido), `core/box.py` (Caixa, nome e capa com "Como era antes", "Apagar de vez" com regras de segurança), escolhas de capa em `refresh_covers`, `Contexto.recarregar` e o `test_loader.py` que faltava (conexão por thread). ADR-0012.
- **Verificação:** 275 testes. Mutação em quatro regras de segurança do apagar: três foram pegas de primeira; uma sobreviveu (faixa apontando para fora da pasta) e gerou um teste novo, depois pega.
- **Tropeço:** uma suíte "quebrada" depois de uma mutação era só o cache de bytecode velho (arquivo de mesmo tamanho na mesma hora); resolvido limpando `__pycache__`; nas mutações seguintes o bytecode foi desligado.
- **NÃO testado:** apagar em disco de rede, uso real.

## 26/11/2026 — M4 (parte 2): telas de montar disco, Caixa e editar

- **Feito:** tela "Criar uma playlist" (digitar vai direto para a busca, marcações sobrevivem ao filtro), painel do "+" com as capas dos discos, tela da Caixa (com "Apagar de vez" só nela), tela "Mexendo no disco" (nome, capa, "Como era antes", "Tirar da estante"). 307 testes passando.
- **Execução interrompida por limite de uso:** M5 a M9 NÃO foram feitos (robustez, MusicBrainz, cópia de CD, empacotamento, avaliação). ADRs 0013 em diante e o ADR do M4 sobre telas ainda não escritos.

## 27/11/2026 — M5: robustez

- **Pedido:** seguir o MVP pelo M5.
- **Feito:** `core/logsetup.py` (log com rotação e gancho de exceções), `core/autostart.py`, `ui/inibidor.py` (suspensão), faixa de falha calma na janela (`Session.falha`), `do_startup` no `app.py`. ADR-0013.
- **Verificação:** 328 testes passando (inclui o de instância única com barramento D-Bus próprio); o app real abre, grava o log e fecha sem erro.
- **Achado:** no teste de instância única, o primeiro processo leva mais de 4 s para abrir num barramento novo; o teste espera o log dizer "iniciado".
- **Decisão provisória:** a abertura automática só é criada quando o comando `moa` está instalado.
- **NÃO testado:** suspensão real e abertura automática no login. O registro do M4 e o ADR das telas do M4 continuam por escrever.

## 27/11/2026 — Documentação do M4 e M6: rede opcional

- **Pedido:** documentar o M4 e seguir para o M6.
- **Feito (M4):** ADR-0014 (as quatro telas do M4). O diário do M4 já existia.
- **Feito (M6):** `core/musicbrainz.py` (cliente com limite de 1 pedido por segundo, atualizador em segundo plano, `aplicar` e `capas_baixadas`), migração 4 do banco, `read_musicbrainz_album_id`, capas baixadas como alternativa em `refresh_covers`, camada lida uma vez por abertura no `Contexto`, rede disparada pelo `Carregador` depois de a estante aparecer, `esta_online` com `Gio.NetworkMonitor` e `MOA_SEM_REDE`. ADR-0015.
- **Verificação:** 355 testes (26 novos, com servidor HTTP falso local, nenhum acesso à internet). Mutação em cinco regras (número de faixas na busca, nome só quando falta a tag, não tentar offline, camada lida uma vez): todas pegas. App real abre com 80 discos e o log diz "sem conexão".
- **Tropeço:** um teste meu estava errado (disco sem tags nunca gera pedido, então "reconsultar depois de 30 dias" não podia ser observado); corrigido usando um disco com ID.
- **Decisão provisória:** `User-Agent` apenas `MoaMediaPlayer/0.1`, sem URL do projeto nem contato.
- **NÃO testado:** servidores reais do MusicBrainz e do Cover Art Archive.

## 27/11/2026 — Texto das cores e ambiente XFCE

- **Pedido:** trocar "Cores normais" por "Cores padrão" nas Configurações; avaliar Windows; saber se o XFCE dá problema.
- **Feito:** texto trocado em `theme.py`, no preview e no ADR-0006 (355 testes passam). CLAUDE.md e README passam a dizer Linux Mint XFCE. ADR-0016.
- **Decisão do autor:** ambiente-alvo XFCE. Windows foi apresentado em três opções (A: mesma stack empacotada; B: outro toolkit; C: preparar o código sem entregar); a escolha ficou em aberto.
- **NÃO testado:** inibição de suspensão, autostart e aparência no XFCE real.

## 27/11/2026 — Instalador entra no plano (M8)

- **Pedido:** um instalador executável, para o usuário não precisar resolver pacotes à mão (o `apt` do notebook não achou `gstreamer1.0-plugins-base`).
- **Feito:** a meta foi escrita no M8 do CLAUDE.md. Nada implementado.
- **Em aberto:** o formato do instalador (`.deb` com dependências embutidas, `.run` autoextraível ou script em volta do `.deb`); a IA apresenta as opções antes de implementar.

## 27/11/2026 — Leitor de CD confirmado

- **Informado pelo autor:** o notebook do pai tem leitor de CD. O M7 deixa de ser condicionado e entra no plano.
- **Em aberto antes de implementar:** formato da cópia (FLAC ou MP3), pacotes de leitura e codificação no Mint XFCE (a confirmar no `check_deps.sh`, com ADR).

## 27/11/2026 — M7 (parte 1): núcleo da cópia de CD

- **Decisões do autor:** formato FLAC; leitura com cdparanoia.
- **Feito:** `core/ripper.py` (copiar faixa a faixa para pasta provisória, tags mínimas, cancelar, resultados calmos, "Disco N"), 12 testes em `tests/test_ripper.py` com gerador de áudio no lugar do CD, `check_deps.sh` confere `cdparanoiasrc` e `flacenc`, ADR-0017, CLAUDE.md atualizado.
- **NÃO testado:** CD de verdade (o leitor daqui está vazio) e a leitura do sumário (`contar_faixas_do_cd`). A tela de colocar o disco ainda não existe e precisa de proposta de desenho.

## 27/11/2026 — M7 (parte 2): tela "Aparelho de CD"

- **Pedido:** cinco opções de desenho para colocar um disco; o autor escolheu a **A (aparelho de CD)**.
- **Feito:** preview em HTML com as 5 opções; `core/aparelho.py` (estados, textos do visor, cópia em thread, cancelar), `ui/cd_view.py`, botão "Colocar um disco" na Estante (também com a estante vazia), `Carregador.reler`, ligação no `app.py`, limpeza de sobras de cópia interrompida, ADR-0018.
- **Verificação:** testes novos de núcleo (`test_aparelho.py`) e de tela (`test_cd_view.py`, com gerador de áudio no lugar do CD); telas desenhadas e conferidas por imagem.
- **NÃO testado:** CD de verdade, a gaveta no XFCE, HD mecânico.
- **Em aberto:** ouvir música durante a cópia; impedir a suspensão durante a cópia.

## 27/11/2026 — M8 (primeira etapa): pacote .deb e instaladores no plano

- **Pedido:** gerar o `.deb` primeiro; registrar nos planos que o autor quer instaladores, principalmente para Windows, depois.
- **Feito:** CLAUDE.md (M8 vira o `.deb`; novo M10 com o instalador `.run` offline e o Windows, com a decisão técnica em aberto), `tools/build_deb.sh`, `packaging/` (comando `moa`, `.desktop`, ícone provisório), `tests/test_packaging.py`, ADR-0019. O pacote tem ~68 KB.
- **Verificação:** o pacote extraído roda `moa` a partir de `/`, e a abertura automática é criada com o caminho do comando.
- **NÃO testado:** instalação em Mint limpo (`apt install ./arquivo.deb`), menu do XFCE, desinstalação.
- **Pendência:** a janela em branco no notebook do pai ainda não foi diagnosticada (a saída do terminal e do log não chegou).

## 27/11/2026 — Primeiro teste no notebook do pai: travada no volume

- **Relato do autor:** o app abriu (a janela em branco era a `main` antiga, só com o M0); clicar no volume dava uma travada forte. A coleção dele é uma pasta "MIX" com 371 músicas.
- **Causa:** cada clique de volume redesenhava a tela do rádio inteira, inclusive as 371 linhas da lista, e cada linha relia e convertia o SVG do ícone "+". Medido aqui: 335 ms por clique (em CPU rápida).
- **Feito:** cache dos ícones já convertidos (`widgets.icone`) e a lista de músicas só é refeita quando muda disco, faixa, estado de tocar, aviso ou coleção (`RadioView`). Depois: 14 ms por clique. `tests/test_radio_lista.py` (6 testes; o de reaproveitar falha se a regra for desligada).
- **Fluxo de branches:** daqui em diante, branches a partir da `dev` (esta: `fix/volume-travando`).
- **NÃO testado:** no notebook do pai (HD mecânico e CPU antiga). As outras telas com listas grandes (montar playlist, Caixa) podem ter o mesmo problema e ainda não foram medidas.

## 27/11/2026 — Travada em tudo no rádio (371 faixas)

- **Relato do autor:** depois da correção do volume, ele percebeu que pausar e as demais ações também travavam (notebook com ventoinha alta). A correção anterior só poupava o volume, porque a lista era refeita sempre que mudava a faixa ou o estado de tocar.
- **Medido aqui (371 faixas):** tocar/pausar ~100 ms, próxima ~97 ms.
- **Feito:** a marca "Tocando agora"/"Parado aqui" passa a ser movida no lugar (só duas linhas mudam), e a lista é marcada como `no_show_all` depois de mostrada, para o `show_all` da janela não percorrer as 371 linhas. Depois: tocar/pausar ~12 ms, próxima ~14 ms, abrir o rádio ~17 ms.
- **Verificação:** `tests/test_radio_lista.py` (8 testes, um deles confere que só uma linha fica destacada); desenho do rádio conferido por imagem.
- **NÃO testado:** no notebook do pai. Falta o `tools/measure.sh` para medir lá de forma repetível.

## 27/11/2026 — Atualizador de teste dentro do app (temporário)

- **Pedido:** poder atualizar o app no notebook com base na branch `dev`, sem baixar o zip à mão. Opções apresentadas (A script, B script com atalho, C dentro do app, D git pull agendado); a IA recomendou B; **o autor escolheu C** ("quero velocidade; depois a gente remove").
- **Feito:** `core/atualizacao_de_teste.py` (procura, baixa o zip da `dev`, confere, troca `moa/`, guarda `moa.anterior/`, volta), `ui/cartao_de_atualizacao.py` (Configurações e Estante), procura em silêncio ao abrir, ADR-0020 com a lista de remoção. Todo trecho marcado com `ATUALIZACAO_DE_TESTE`.
- **Verificação:** 20 testes novos sem internet; uma atualização real contra o GitHub numa cópia (procurar, instalar, importar o código novo, voltar); suíte completa passa (424).
- **Custo aceito pelo autor:** quebra "offline por padrão", expõe jargão e baixa código sem assinatura. Só liga em pasta de código-fonte gravável.
- **NÃO testado:** no notebook do pai; o "Abrir de novo agora" dentro da janela de verdade.

## 27/11/2026 — Medição de desempenho (`tools/measure.sh`)

- **Pedido:** medir o desempenho de forma automatizada, para comparar o notebook do pai com a máquina de desenvolvimento.
- **Feito:** `tools/measure.sh` e `tools/measure.py` (abertura do app de verdade, RAM e CPU em repouso, tempo de 11 ações em duas coleções sintéticas, CPU tocando), CSV com a configuração da máquina, linha de log `estante pronta` no `Carregador`, ADR-0021, `tests/test_measure.py`.
- **Tropeço:** a primeira versão isolava o D-Bus (`dbus-run-session`) e media 25 s de abertura; era um artefato do isolamento (o app espera um serviço que não existe na sessão nova), não do app. Passei a medir na sessão real e a recusar rodar com um Moa aberto. Também a CPU tocando dava 4,6% por causa do meu próprio laço de espera; troquei por um laço de eventos e caiu para ~3,5%.
- **Medido aqui (i5-9600K, `--rapido`):** abertura ~0,3 s, RAM ~85 MB em repouso, CPU tocando ~3,5%.
- **NÃO rodado no notebook do pai.** Falta a rodada completa lá e a medida a frio depois de reiniciar.

## 27/11/2026 — Medição travou no notebook; a causa real da travada da lista

- **Relato do autor:** o `measure.sh` não existia lá (o atualizador só trocava `moa/`) e a medição ficou presa em "[mix] cronometrando as ações...".
- **Atualizador:** passa a trocar também `tools/` (anterior em `tools.anterior/`); falha em `tools/` não impede a atualização; "voltar" devolve as duas pastas.
- **Medição presa:** reproduzida aqui com 371 faixas. As faixas de teste eram curtas, o disco avançava sozinho o tempo todo e a tela nunca ficava parada para o cronômetro. As ações passam a usar faixas longas (links para um áudio de 5 min), a espera por "tela pronta" tem limite de 5 s e cada ação imprime o resultado ao terminar.
- **Achado importante:** com a janela montada, o volume ainda custava ~440 ms com 371 faixas (e 49 ms com 20). Dois culpados, os dois por linha: (1) a lista trocava de pai a cada clique, o que desfaz e refaz por dentro as 371 linhas; (2) toda preferência (inclusive o volume) reaplicava o tema, e o GTK recalcula o estilo de todos os widgets. Corrigido: a lista agora fica sempre no mesmo lugar (só o painel do rádio é refeito) e o tema só é reaplicado quando a letra ou a cor mudam. Volume: ~35 ms com qualquer número de faixas; tocar/pausar e próxima: ~40 a 50 ms.
- **Lição:** minha medida anterior (14 ms) usava uma janela não montada e por isso não via o custo do GTK. Medir sempre com a janela desenhada.
- **NÃO testado:** no notebook do pai (HD mecânico, CPU antiga).
