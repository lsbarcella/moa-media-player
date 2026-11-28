# ADR-0012 — Discos montados, Caixa, edições e "Apagar de vez"

- **Status:** Aceito. Detalhes técnicos novos da IA marcados como **provisórios**.
- **Data:** 26/11/2026
- **Decisor:** o autor decidiu o conceito (ADR-0007, CLAUDE.md seção 9); a IA propôs a estrutura de dados.

## Contexto

O M4 deixa o próprio idoso cuidar da coleção: montar discos (playlists), tirar discos da estante, renomear, trocar a capa e, só dentro da Caixa, "Apagar de vez". Nenhuma tag nem arquivo de música pode ser reescrito, e "Apagar de vez" é a única operação que apaga arquivos do usuário.

## Decisão

1. **Camadas sobre a biblioteca (KTD10).** A varredura do M1 continua intacta. `box.aplicar_camadas` roda depois dela: esconde os discos da Caixa e aplica os nomes escolhidos. Sem nada guardado, devolve exatamente a biblioteca do M1 (testado). *Desvio do plano:* em vez de alterar `refresh_library`, a camada é uma função à parte; o resultado é o mesmo e os 147 testes do M1 ficam intocados.
2. **Banco (migração 3, aditiva):** `mix_discs`, `mix_tracks` (só caminhos), `box` e `overrides` (nome e capa escolhidos, com o valor de antes para "Como era antes").
3. **Disco montado = `MixDisc` virtual (KTD9).** Guarda referências por caminho; faixa cujo arquivo sumiu da coleção é pulada e vai para o log.
4. **"Como era antes" vale um passo só**, depois de guardar (a segunda vez não faz nada).
5. **Capa escolhida** entra na assinatura do cache de capas (`refresh_covers(escolhas=...)`), então a miniatura antiga é descartada e a nova vale na abertura seguinte. A capa "desenhada" é a substituta do M1.
6. **"Apagar de vez" (KTD11), regras de segurança:**
   - disco montado: só o registro é apagado, nenhum arquivo é tocado;
   - disco de verdade: apaga só os arquivos das faixas do próprio disco e as imagens `cover`/`folder`/`front` da própria pasta; recusa pasta fora da pasta de música, a própria raiz, link simbólico e disco sem faixas; nunca apaga um arquivo fora da pasta do disco; a pasta só some se ficar vazia (outro arquivo do usuário, como um encarte, fica);
   - se algum arquivo não puder ser apagado, o disco **continua na Caixa** com o que sobrou e a tela mostra uma frase calma; detalhes vão para o log.

## Alternativas rejeitadas

- Dar uma pasta fictícia ao disco montado: enganaria a varredura e o "Apagar de vez".
- Guardar a Caixa mexendo nos arquivos (mover para uma pasta): reescreveria a coleção e quebraria o "nada muda nos arquivos".
- Lixeira do sistema para "Apagar de vez": o texto da tela promete "não voltam"; a dependência do `gio trash` e o comportamento variam por instalação.

## Consequências

- Testes de segurança (limite da raiz, arquivo fora da pasta, falha no meio) com **mutação**: três regras quebradas de propósito, os testes falham. Uma mutação sobreviveu na primeira rodada (faltava um teste de faixa apontando para fora da pasta); o teste foi acrescentado.
- Os testes usam só pastas temporárias; a coleção real nunca é tocada.

## NÃO testado

Apagar em sistema de arquivos de rede ou com pasta sem permissão de leitura da pasta pai; comportamento de link simbólico de arquivo (não de pasta) dentro do disco em outros sistemas de arquivos; uso por um usuário real.
