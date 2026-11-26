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
- **Preview visual:** criado `docs/preview/estante-preview.html`, uma maquete interativa (HTML único, sem som) com as 7 ideias, painel de variantes (visor, "+", avisos, "apagar de vez", estante que lembra, controle de letra) e o botão "Voz mais clara". Respostas do autor: usa mouse; volume é o do app; "Voz mais clara" começa desativado. Verificação: paleta conferida (todos os pares de 7:1 ou mais), todos os fluxos percorridos por script sem erro, texto conferido em 20 px ou mais e alvos em 64 px ou mais (exceto a barra de título do sistema). Corrigidos na revisão: capa pequena no visor, textos abaixo de 20 px e mosaico vazio dos discos montados.
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
