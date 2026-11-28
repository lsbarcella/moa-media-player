# ADR-0030 — Tipografia: Atkinson Hyperlegible para ler e Roboto Slab para os nomes

- **Status:** Decidido pelo autor em 28/11/2026. **Ainda não implementado** (ver "O que falta").
- **Data:** 28/11/2026
- **Decisor:** o autor, olhando `docs/preview/tipografia.html`: "Atkinson mais Roboto Slab".

## Contexto

O app não definia fonte (usava a do tema do sistema) e quase tudo estava em peso 800. O autor gostou da Atkinson Hyperlegible (desenhada pelo Braille Institute para baixa visão, com caracteres bem distintos entre si) e quer **duas fontes**, para a hierarquia vir da família e não só de tamanho e negrito.

## Decisão

1. **Atkinson Hyperlegible** faz o trabalho de ler: estado, botões, listas, notas, volume, tempos.
2. **Roboto Slab** só aparece onde há um **nome**: o título da música, o título da tela e os nomes dos discos.
3. **Pacote:** as duas vêm do apt (`fonts-atkinson-hyperlegible`, 141 KB; `fonts-roboto-slab`, 365 KB), declaradas como dependência do `.deb` e conferidas no `check_deps.sh`. Ambas são SIL OFL 1.1, livres e compatíveis com a GPL v3 do projeto. **Se a Atkinson não existir no apt do Linux Mint do notebook**, os arquivos entram no próprio `.deb` (com o texto da licença).
4. **Sem a fonte instalada nada quebra:** o CSS usa uma lista (`"Atkinson Hyperlegible", "Noto Sans", sans-serif` e `"Roboto Slab", "Noto Serif", serif`).
5. **Pesos:** o apt só traz a Atkinson em Regular (400) e Bold (700). Portanto 600 e 800 deixam de existir para ela; os botões e rótulos passam para 700 e o texto corrido para 400.

## O que falta (decidir ou fazer)

- **Confirmar no notebook:** `apt-cache policy fonts-atkinson-hyperlegible fonts-roboto-slab`. Se faltar a Atkinson no Mint, embutir.
- **Estado ("Pausado" ou "PAUSADO")** e **números de largura igual** no tempo e no volume: o autor ainda não decidiu (recomendação: "Pausado" e números de largura igual).
- **A Roboto Slab entra também no estado?** Combinado: só nomes. Confirmar olhando o app.
- **Implementar:** regras de `font-family` e de peso no `theme.py`; `fonts-atkinson-hyperlegible` e `fonts-roboto-slab` em `tools/build_deb.sh` e `tools/check_deps.sh`; testes (a lista de fontes no CSS e o pacote); conferir as telas de novo nos quatro tamanhos de letra (a Roboto Slab é mais larga que a Noto Sans); medir.
- **Hipótese a validar:** se a Atkinson ajuda de fato o idoso (a literatura e o desenho dizem que sim, mas o teste de usabilidade é que confirma).
