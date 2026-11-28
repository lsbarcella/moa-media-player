# ADR-0029 — Tema de letra "Pequeno", escalas menores e rádio sem o botão "Guardar o disco"

- **Status:** Aceito. Substitui os números do ADR-0028 (17, 20 e 24 px). A hipótese de que 16 px basta como padrão fica a validar com o usuário.
- **Data:** 28/11/2026
- **Decisor:** o autor, depois do teste no notebook: "diminuir todos os temas mais um pouco, e criar um tema pequeno que tenta ter o tamanho Padrão para quem não tem problema de visão; o Normal continua o padrão do app". Também pediu para tirar o botão "Guardar o disco na estante e parar" e deixar o rádio mais colado no canto.

## Decisão

1. **Escalas** (`theme.ESCALAS`, 0,70 / 0,80 / 0,90 / 1,05 da referência de 20 px): **Pequeno 14 px, Normal 16 px (padrão), Grande 18 px, Maior 21 px**. O Pequeno aparece nas Configurações como a primeira opção. O mínimo do CSS passa a 14 px (`LETRA_MINIMA_PX`); o alvo clicável continua de 64 px.
2. **Botão "Guardar o disco na estante e parar" removido da tela do rádio.** Ele parava a música e esvaziava o rádio. A função (`Radio.guardar_o_disco_e_parar`) continua, porque a edição de discos a usa quando o disco do rádio é tirado da estante. Consequência: **depois de pôr um disco no rádio, a barra do pé fica na tela até fechar o app** (pausar não a tira).
3. **Rádio mais enxuto:** margens da tela de 24 para 12 px e o painel colado no canto (o painel herdava "expandir" e ficava longe dele); botão de volume de 132 para 104 px; menos espaço dentro do gabinete, do visor e da bandeja. Em 1366x768 e letra Normal cabem na primeira tela o visor, as teclas, o volume e o "Voz mais clara".

## Consequências

- Quem usa o Pequeno tem letra de 14 px, **bem abaixo** da regra anterior de 20 px: ele é só para quem enxerga bem, e o padrão do app continua o Normal.
- Para voltar atrás em qualquer tamanho, basta trocar os números de `ESCALAS`.
- Quem quiser esvaziar o rádio de verdade só fecha o app; se isso fizer falta, o botão volta (a função existe).
- **NÃO testado** no notebook do pai.
