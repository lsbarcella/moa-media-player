# ADR-0025 — Tema hi-fi (teclas de metal cinza com bisel) e símbolo sem texto no volume

- **Status:** Aceito. Hipótese de que o símbolo basta, sem texto, a validar com o usuário.
- **Data:** 28/11/2026
- **Decisor:** o autor. Enviou uma imagem de referência (fileira de teclas de metal cinza com bisel numa bandeja preta, a tecla do pause afundada) e pediu: mudar a base do tema do app para esse estilo; cortar o texto de "Mais alto" e "Mais baixo", ficando só os ícones; reescrever a regra do CLAUDE.md.

## Contexto

O ADR-0024 deu ao app madeira, latão e teclas bege. O autor preferiu o visual de um aparelho de som hi-fi: metal cinza, bisel, bandejas pretas, gabinete grafite. Também propôs cortar texto onde o idoso tem memória de ícones de aparelhos antigos. O CLAUDE.md dizia que ícones "vêm sempre acompanhados de texto", decisão anterior do próprio autor, que a literatura sobre idosos também apoia. Constraints que continuam: GTK 3 com CSS e Cairo, sem imagens nem dependência nova, 7:1 de contraste no pior ponto de cada degradê, alvos de 64 px, nada depende de arrastar ou de passar o mouse.

## Alternativas

1. **Só as teclas em cinza, mantendo madeira e latão.** Mudança pequena, mas cinza moderno sobre madeira destoava no preview.
2. **O aparelho todo no estilo hi-fi (escolhida).** Coerente de ponta a ponta.
3. **Dois temas escolhidos em Configurações (Madeira e Metal).** É a ideia I7 (interruptor de aparência), não decidida, e dobra o que testar. Fora de escopo.
4. **Cortar o texto de todas as teclas de transporte e volume.** O autor só pediu o volume; o transporte fica como está até ele decidir.

## Decisão

1. **Materiais.** Os tokens `wood*` e `brass*` foram renomeados e trocados: `case*` (gabinete grafite, estrias de metal escovado), `plate*` (prata: friso, plaquinhas, parafusos), `key*` (tecla solta), `keyon*` (tecla afundada), `tray`/`tray_edge` (bandeja preta). Os tokens agora dizem o que a coisa é.
2. **Tecla solta:** metal cinza, bisel claro em cima e à esquerda e escuro embaixo e à direita, brilho só na faixa de cima, sombra rígida embaixo. **Tecla afundada** (pause tocando, Voz mais clara, opção escolhida, música marcada): cinza escuro, bisel invertido, sombra por dentro, **letra branca**. No lugar de "mais escuro" (que dava 5,7:1), `keyon` foi escolhido para dar 7:1 com texto branco em todo o degradê.
3. **Bandeja preta** (`.moa-bandeja`) segura as teclas de transporte e o volume. **Gabinete** do rádio e fundo da estante em grafite com friso prateado; plaquinhas, cartões e painel do "+" seguem a mesma luz.
4. **Tocar** continua verde e **Pausar** vira a tecla afundada (no lugar do âmbar).
5. **Volume sem texto.** "Mais baixo" e "Mais alto" são o alto-falante com **−** e **+** (`botao_so_com_icone`), com 120 px de largura. Cada uma tem **nome acessível** e dica. No mínimo ou no máximo, a tecla fica apagada (tracejada) e o nome vira "Volume no mínimo" ou "Volume no máximo". O estado continua escrito ("Volume: N de 10") e a coroa de luzes continua mostrando.
6. **Regra do CLAUDE.md reescrita:** texto visível em todo botão, exceto símbolos de aparelho antigo (hoje só o volume), com nome acessível e estado em texto.
7. **Preto e branco:** relevo por contorno duplo e sombra, sem tons; tecla afundada é preta com letra branca.

## Consequências

- Os testes de contraste no pior ponto foram refeitos para os novos materiais, nas quatro paletas; um teste novo garante que o tema normal não tem tom amarelado ou marrom.
- Os ajudantes de teste passaram a achar botões também pelo nome acessível; o teste "nenhum botão sem texto" aceita nome acessível.
- **Hipótese a validar:** o idoso reconhece o alto-falante com − e + sem a palavra. Se não reconhecer, volta o texto (o nome acessível já existe).
- **Custo:** o relevo continua em CSS; não há peça nova em Cairo. Não medido no Pentium T4300 (só a máquina de desenvolvimento).
- **Ficam em aberto:** texto no transporte (Anterior, Tocar/Pausar, Próxima); a barra do rádio nas outras telas (visor, teclas e barra de progresso clicável, preview aprovado mas não implementado; o que mostrar sem nada tocando); a cor da lombada; contraste do tema com uma pessoa daltônica de verdade.
