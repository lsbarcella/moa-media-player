# ADR-0023 — "A Caixa" passa a se chamar "A Lixeira"

- **Status:** Aceito.
- **Data:** 27/11/2026
- **Decisor:** o autor.

## Contexto

Os discos tirados da estante iam para "A Caixa" (ADR-0007, ADR-0012, ADR-0014). O autor quer um nome que o idoso já conhece de outros objetos do dia a dia: a lixeira, de onde se pode recuperar o que foi jogado fora ou esvaziá-la de vez.

## Decisão

1. O nome na tela passa a ser **"A Lixeira"**: botão da Estante ("A Lixeira (N discos)"), título da tela, frases ("A Lixeira está vazia.", "Ele está na Lixeira; as músicas continuam no computador.") e o texto de "Tirar da estante".
2. O ícone troca da caixa para uma **lixeira** (`ui/icons/lixeira.svg`, desenho original do projeto), para a imagem combinar com o texto.
3. As regras **não mudam**: "Tirar da estante" nunca apaga arquivos de música, "Colocar de volta na estante" desfaz, e **"Apagar de vez" só existe dentro da Lixeira**, com texto claro e dois botões grandes (ADR-0007).
4. Os nomes **internos** continuam como estão (`Tela.CAIXA`, `ctx.caixa`, `core/box.py`, a tabela `box` do banco, a classe `moa-perigo-caixa`): trocá-los não muda nada para o usuário e traria risco para os dados já gravados. Quem lê o código deve entender "caixa" como "lixeira".

## Atenção

A palavra "lixeira" sugere "já foi jogado fora". Por isso as frases ao tirar um disco repetem que **as músicas continuam guardadas no computador**. Se no teste com o usuário ele achar que o disco foi apagado, rever o texto (ou voltar a um nome mais neutro).

## Consequências

- Os ADR-0007, 0008, 0012 e 0014 continuam falando em "Caixa": são o registro da época. O CLAUDE.md, o preview em HTML e os testes foram atualizados.
