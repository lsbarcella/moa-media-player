# ADR-0007 — Botão "+" com capas e "Apagar de vez" só dentro da Caixa

- **Status:** Aceito.
- **Data:** 26/11/2026
- **Decisor:** autor do TCC

## Contexto

Duas decisões de interação ficaram abertas depois da ideação de interface (`docs/ideation/`): como o botão "+" de cada música pergunta o destino, e se a opção de apagar um disco de vez existe e onde. As duas foram comparadas em um preview interativo (`docs/preview/estante-preview.html`).

## Alternativas

### Botão "+"

| Alternativa | Prós | Contras | Resultado |
| --- | --- | --- | --- |
| A. Duas frases ("Adicionar a uma playlist existente", "Criar uma nova playlist") | Fiel ao pedido original | Exige ler e escolher entre duas frases; usa a palavra "playlist" | Descartada |
| **B. Capas dos discos ("Em qual disco?"), com "Disco novo" tracejado como primeira capa** | Reconhecimento visual de objeto; uma decisão em vez de duas; coerente com "playlist = disco novo" | Troca as duas frases escolhidas antes; a lista de capas cresce com o número de discos montados | **Escolhida** |

### "Apagar de vez"

| Alternativa | Prós | Contras | Resultado |
| --- | --- | --- | --- |
| A. Não existe na interface | Zero risco de perda | O usuário não consegue apagar nada sem sair do app, contra a autonomia (ADR-0002) | Descartada |
| **B. Só dentro da Caixa, com texto claro e dois botões grandes** | Autonomia completa; o caminho para apagar é longo e deliberado | Existe um caminho destrutivo | **Escolhida** |

## Decisão

- O botão "+" abre um painel "Em qual disco?" com as **capas dos discos montados** e um **"Disco novo"** como primeira opção. Escolher uma capa adiciona a música e mostra, na própria linha, onde ela entrou, com "Desfazer". Se a música já estiver no disco, o app diz isso em vez de duplicar.
- **"Apagar de vez" aparece somente dentro da Caixa.** "Tirar da estante" nunca apaga: só move o disco para a Caixa, e a tela repete que as músicas continuam no computador. Apagar de vez pede uma confirmação em texto simples ("os arquivos de música também serão apagados e não voltam") com os botões "Manter o disco" (destacado) e "Sim, apagar de vez".

## Consequências

- **Positivas:** menos leitura no "+"; o caminho destrutivo fica isolado e deliberado.
- **Negativas e riscos:**
  - A palavra "playlist" some do "+", mas continua no botão grande "Criar uma playlist". O vocabulário precisa ser coerente no resto do app.
  - **Risco de arquitetura:** se a biblioteca é varrida por pasta a cada abertura, um disco "tirado" volta na varredura seguinte. É preciso guardar uma lista de discos na Caixa que a varredura respeite.
  - Apagar arquivos de verdade exige cuidado: só apagar os arquivos do disco, nunca da pasta pai, e testar com pastas de exemplo.
  - Avisos e confirmações ficam até a próxima ação do usuário, porque a leitura varia entre pessoas. Confirmado pelo autor ao manter a primeira opção do preview como padrão.
- **Mudanças no projeto:** `core/library.py` (lista de discos tirados), `core/custom_albums.py` (discos montados) e as telas do M4.

## Validação

Teste de usabilidade: o usuário monta um disco pelo "+" sem errar o destino, entende que "Tirar da estante" não apaga e consegue desfazer. O fluxo de apagar de vez deve ser testado com arquivos de exemplo, nunca com a coleção real.
