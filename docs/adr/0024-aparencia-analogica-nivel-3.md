# ADR-0024 — Aparência analógica, nível 3 ("Aparelho detalhado")

- **Status:** Aceito. **Parcialmente substituído pelo ADR-0025** (28/11/2026): os materiais (madeira, latão) viraram grafite e prata; a estrutura (teclas com curso, peças em Cairo com cache, contraste no pior ponto) continua valendo.
- **Data:** 28/11/2026
- **Decisor:** o autor. Pediu para transformar os "quadradões" em objetos analógicos, viu o preview em três níveis e escolheu ir **direto ao nível 3**. A IA recomendava o nível 2 primeiro.

## Contexto

Os botões e painéis eram retângulos arredondados com borda grossa. O CLAUDE.md (seção 2) pede que cada elemento pareça um objeto do mundo real que o idoso já sabe usar, e a seção 11 deixava o desenho visual como decisão em aberto. A ideação (`docs/ideation/2026-11-28-aparencia-analogica-ideation.html`) gerou as ideias I1 a I7 e o preview (`docs/preview/aparencia-analogica.html`) mostrou três níveis de detalhe. Restrições que continuam valendo: GTK 3 com CSS e Cairo, sem GPU, Pentium T4300 com HDD, alvos de 64 px, letra de 20 px, contraste de 7:1, ícones sempre com texto, foco visível, nada depende de arrastar, e sem imagens nem dependências novas.

## Alternativas

1. **Nível 1 (como estava) ou nível 2 (aparelho, sem peças desenhadas).** Mais barato e quase tudo em CSS. Recusado pelo autor: "ainda parece muito simples".
2. **Imagens prontas (PNG, `border-image`) para madeira, latão e botões.** Visual fácil de acertar, mas precisa de arquivos com licença livre, cresce o pacote e não troca de cor nas quatro paletas. Recusado.
3. **Botão de volume arrastável ou clicável.** Mais "real", mas quebra a regra de não depender de arrastar. Recusado: o botão só gira sozinho com "Mais baixo" e "Mais alto".
4. **Animações (a tecla descendo, o botão girando).** Custo contínuo de CPU. Recusado: o estado muda de uma vez, sem animação.
5. **CSS para o relevo + peças pequenas em Cairo com cache.** Escolhida.

## Decisão

Implementar o **nível 3** das ideias I1 a I6. **I7 (interruptor "Simples ou Aparelho") não entra**: não foi decidida.

1. **Teclas com curso.** No GTK 3 não há `transform`, então a tecla "desce" trocando borda de baixo por espaço em cima (a altura total não muda). Brilho translúcido só na faixa de cima (8 px, acima do rótulo, também na letra "Maior"), sombra rígida embaixo, moldura de metal escovado atrás de Anterior, Tocar e Próxima. Tocar e Pausar continuam **trocando** de botão.
2. **Teclas travadas com lâmpada.** "Voz mais clara", as opções de Configurações (tamanho da letra e cores, onde apertar uma solta as outras) e a marcação de músicas na playlist ficam **baixadas** e com a lâmpada acesa. A posição é o terceiro sinal do estado, junto do texto e da lâmpada, e não depende de cor.
3. **Rádio.** Gabinete de madeira com veios, moldura de latão, parafusos, plaquinha "MOA", grade do alto-falante e visor de vidro (degradê âmbar, sombra interna, reflexo só na borda) com régua gravada e marcador da faixa atual.
4. **Botão de volume** desenhado em Cairo: serrilha, coroa de dez lâmpadas com lente, gira sozinho. Mantém "Volume: N de 10" e os rótulos "No mínimo" e "No máximo". Não é clicável, arrastável nem focável.
5. **Capa em caixa de CD** (`Capa`): moldura de plástico, lombada com duas dobradiças. A caixa vem do cache com o **miolo transparente**: o reflexo só existe na moldura e não pode cobrir a arte nem o texto da capa substituta (um teste confere pixel a pixel).
6. **Estante com profundidade:** fundo recuado de madeira, tampo com sombra, vão côncavo para "Em uso no rádio", plaquinhas de latão com parafusos nos títulos. Cartões, painel do "+", Aparelho de CD, Lixeira e Configurações usam a mesma luz (realce em cima, sombra rígida embaixo).

**Regras técnicas fixadas:**

- **Relevo por camada translúcida sobre a cor do token**, nunca por degradê opaco nas teclas (a armadilha do preview: o "Tocar" verde virou creme com letra branca).
- **Contraste de 7:1 no pior ponto de cada material.** `theme.MATERIAIS` descreve cada texto sobre seu degradê, e `contraste_no_pior_ponto` confere todos os trechos e as camadas translúcidas, nas quatro paletas. A mesma tabela de opacidades gera o CSS e alimenta o teste. Latão com texto usa o tom claro; o escuro só em moldura sem texto.
- **Preto e branco:** relevo por contorno duplo e sombra, sem degradês nem tons (inclusive `btnradio`, que era bege).
- **Cairo com cache.** `moa/ui/cairo_pecas.py` tem funções puras de desenho e o `CacheDeDesenho` (chave: nome, tamanho, estado, paleta; limite de 64 itens). A paleta em uso fica em `theme.paleta_atual()`, lida na hora de desenhar, então trocar a paleta não exige reconstruir telas.
- **Nada novo para instalar, exceto `python3-gi-cairo`**, que já vem com o PyGObject no Mint e agora consta no `.deb` e no `check_deps.sh`. Sem imagens, sem animação, arte original (GPL v3).
- **Texto novo só com 20 px ou mais**, ou nenhum: o botão de volume e a régua não desenham números.
- `tools/telas.py` gera as imagens das seis telas nas quatro paletas e três escalas de letra (72 imagens) para conferir a aparência.

## Consequências

- **Medido antes e depois** (máquina de desenvolvimento, i5, `tools/measure.sh --sem-audio`): ações iguais (tocar/pausar 18 ms, volume 15 ms, abrir Configurações 17 ms), RAM em repouso +1 MB (86 para 87 MB com o mix; 88 para 89 MB com a estante), abertura seguinte 297 para 279-315 ms. Um máximo de 261 ms em uma rodada não se repetiu em duas outras. **Não medido no notebook do usuário:** é lá que o custo das peças em Cairo precisa ser conferido.
- O contraste agora é verificado em todos os pontos dos degradês, o que torna perigoso mexer em cor sem rodar `tests/test_theme.py`.
- O desenho do painel do rádio ficou mais alto (régua e botão de volume): em tela baixa a página do rádio rola.
- **Ficam em aberto** (não decididas): I7, o interruptor "Simples ou Aparelho"; clicar no próprio botão de volume; barra de progresso da música; cor da lombada da caixa (cinza-escuro por padrão); sombra rígida preta por padrão.
- **NÃO testado** com o pai do autor, nem em uma pessoa daltônica real. O skeuomorfismo continua sendo hipótese com evidência mista (Urbano 2022 a favor, Ellis e Marshall 2019 contra) a validar no teste de usabilidade.
