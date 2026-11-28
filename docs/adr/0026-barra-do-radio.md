# ADR-0026 — Barra do rádio nas outras telas: visor, teclas e barra de progresso clicável

- **Status:** Aceito. As duas pendências (sem nada tocando, altura em letra "Maior") ficaram no padrão recomendado.
- **Data:** 28/11/2026
- **Decisor:** o autor, a partir do preview `docs/preview/barra-do-radio.html`. Pediu a mistura das ideias B e E, com **barra de progresso interativa "como em qualquer app"** e botões de avançar e voltar.

## Contexto

A tira do pé das outras telas era uma linha de texto com dois botões: não mostrava a faixa, não deixava pular de música e não dizia de relance se estava tocando. A seção 11 do CLAUDE.md tinha "mostrar ou não a barra de progresso, e se é clicável" em aberto.

## Alternativas

A mini-rádio com capa e um botão grande; B visor com as três teclas; C gaveta que abre o rádio; D só o essencial, grande; E régua de progresso. A régua gravada foi recusada ("ficou feia") em favor de uma barra comum.

## Decisão

1. **Barra B + E:** visor âmbar (estado em palavra e lâmpada, música, "Faixa X de Y · Disco"), a bandeja preta com **Anterior, Tocar/Pausar e Próxima** (com texto e símbolo), "Abrir o rádio" e, embaixo, a **barra de progresso** com o tempo decorrido e o total nas pontas e a dica escrita "Clique na barra para ir a outro ponto da música".
2. **Barra clicável (`BarraDeProgresso`):** um clique vai ao ponto clicado (`Radio.buscar_fracao` e `Player.buscar`, que não pausa nem toca sozinho e não deixa pular para depois do fim). **Só clique, sem arrastar** (regra do projeto). Área clicável de 64 px de altura. **Sem foco de teclado**, porque as setas esquerda e direita já são Anterior e Próxima.
3. **Quando aparece:** em toda tela menos no rádio, e só com um disco no rádio. Sem nada tocando, a barra continua sumindo (padrão recomendado).
4. **Custo:** a barra só é refeita quando muda a música, a faixa ou tocando/pausado; o andamento mexe só na fração e nos dois tempos, uma vez por segundo, e só com o rádio tocando e a barra visível.
5. **Altura:** são duas linhas (três na letra "Maior"). Aceito; a medir no notebook.

## Consequências

- Passa a existir `Player.buscar` e `Radio.progresso`/`buscar_fracao`, com testes de faixa longa (ponto pedido, pausado continua pausado, fora da faixa, sem disco).
- Ir a um ponto da música só é possível com o mouse (o teclado fica com anterior e próxima). Se for preciso, uma tecla extra (por exemplo Page Up e Page Down) pode pular 10 s.
- Em letra "Maior" a barra ocupa muito da tela baixa (cerca de um terço em 800 px); se atrapalhar no teste, a dica sai ou o "Abrir o rádio" vai para dentro do visor.
- O estado em movimento (a barra andando) é redesenho pequeno e contínuo: **não medido no Pentium T4300**.
- **NÃO testado** com o pai do autor: se ele descobre sozinho que a barra é clicável (a dica escrita ajuda).
