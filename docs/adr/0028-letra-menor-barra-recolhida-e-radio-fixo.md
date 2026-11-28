# ADR-0028 — Letra menor, barra do rádio recolhida (progresso no hover) e painel do rádio fixo

- **Status:** Aceito. A regra da letra mínima foi relaxada por decisão do autor; a hipótese de que 17 px basta fica a validar com o usuário.
- **Data:** 28/11/2026
- **Decisor:** o autor, depois de testar no notebook (1366x768): "a barra ocupa espaço demais", "o Maior quebra TODAS as telas, o Grande algumas e o Normal já está quase quebrando", e pediu o progresso só no hover, "Abrir o rádio" na mesma linha das teclas e o painel do rádio fixo ao lado da lista.

## Contexto

O ADR-0026 deixou a barra do pé com duas linhas e a letra em 20, 24 e 28 px. No notebook isso comia a tela. O CLAUDE.md fixava a fonte base em no mínimo 20 px (decisão anterior do próprio autor, baseada na literatura de idosos).

## Decisão

1. **Letra.** `ESCALAS` passa a 0,85, 1,02 e 1,19 da referência de 20 px: **Normal 17 px, Grande 20 px, Maior 24 px**. Nenhum texto do CSS abaixo de 16 px (`LETRA_MINIMA_PX`). O alvo clicável continua de no mínimo 64 px. Está em um só lugar (`theme.ESCALAS`).
2. **Barra do pé recolhida.** Uma linha só: visor (estado, música, faixa), as três teclas na bandeja e **"Abrir o rádio" na mesma linha, todo à direita**. Um **fio fino de andamento** fica sempre visível. A letra da barra nunca passa de "Grande".
3. **Progresso no hover.** A barra de progresso clicável **flutua por cima da tela** (`Gtk.Overlay` + `Gtk.Revealer`) quando o mouse está na barra, e some depois de uma pausa de 400 ms. Como flutua, **não redimensiona a tela de baixo**: redimensionar a lista de discos a cada passada do mouse pesaria no Pentium.
4. **Exceção à regra "nada depende do mouse":** só o progresso clicável depende do hover; tudo o mais fica sempre à vista, e o fio mostra o andamento. O teclado não perde nada (as setas são Anterior e Próxima).
5. **Painel do rádio fixo.** Cada coluna tem a sua rolagem: lado a lado, **o painel não se move e só a lista rola**. Só a letra "Maior" (ou janela com menos de 900 px) empilha, e aí a tela inteira rola. Nenhum widget troca de pai; mudam só as políticas de rolagem, porque trocar a lista de pai refazia suas centenas de linhas por dentro.

## Consequências

- Sai a regra de fonte mínima de 20 px; **a hipótese de que 17 px basta fica a validar** no teste de usabilidade (idosos têm declínio de visão). Se não bastar, é só trocar os números de `ESCALAS`.
- A barra recolhida tem cerca de 135 px (18% de 768 px): é o piso do alvo de 64 px mais a borda e a bandeja. Eram 26% no "Maior" e 38% antes.
- Quem só usa teclado nunca vê a barra de progresso (não era acessível por teclado mesmo).
- **NÃO testado** no notebook do pai.
