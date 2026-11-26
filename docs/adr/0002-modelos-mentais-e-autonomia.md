# ADR-0002 — Autonomia do idoso por meio de modelos mentais do mundo real

- **Status:** Aceito (princípio). O desenho detalhado de cada tela ainda é decisão em aberto.
- **Data:** 26/11/2026
- **Decisor:** autor do TCC

## Contexto

A primeira versão do CLAUDE.md previa um **cuidador** (o autor) que faria as tarefas "mais difíceis" por trás de um modo escondido: escolher a pasta de música, reescanear a biblioteca, ajustar a fonte e ver avisos. Isso contradiz o objetivo do projeto, que é a **autonomia do idoso**: ele deve abrir o app e se virar sozinho, sem sentir que está perdido.

A linha de pesquisa do projeto é reaproveitar **imagens mentais já estabelecidas** pelas pessoas de idade, de modo que elas reconheçam, no software, padrões que já conhecem do mundo real.

## Alternativas

| Alternativa | Autonomia | Esforço de aprendizado | Risco | Resultado |
| --- | --- | --- | --- | --- |
| A. Interface convencional de player (listas, menus) com modo cuidador | Baixa: depende de outra pessoa | Alto para o idoso | Baixo | Descartada |
| B. Interface convencional, mas com tudo acessível ao usuário | Média | Alto | Médio | Descartada |
| C. Metáforas do mundo real (estante de CDs, aparelhos antigos), com tudo acessível ao usuário | Alta | Baixo, por reaproveitar o que ele já sabe | Médio: a metáfora precisa ser bem desenhada e validada | **Escolhida** |

## Decisão

Adotar a alternativa C, com estas regras:

1. **Cada elemento da tela imita um objeto do mundo real** que o idoso já sabe usar. A linha visual é uma **estante de CDs** com **ícones de tocadores de música antigos**. Os ícones sempre vêm acompanhados de texto.
2. **Não há cuidador nem modo escondido.** A manutenção da coleção (adicionar, renomear, trocar a capa, remover discos) é feita pelo **próprio usuário**, dentro da mesma metáfora.
3. **O X da janela permanece.** Fechar uma janela é uma noção básica de computador que deve ser aprendida. Não há botão "Desligar" próprio. Por isso o app abre **como uma janela de programa normal**, com a barra de título visível, e não em tela cheia.
4. **Sempre há um caminho de volta visível** em qualquer tela que não seja a Estante, e a tela atual é identificável de relance.
5. **A estante mostra os álbuns e o rádio toca as músicas.** A tela Tocando agora usa a imagem de um **rádio** antigo.
6. **Playlist é "montar um disco novo"** na estante, a partir de faixas de discos que o usuário já tem. Pode ser criada por um botão grande "Criar uma playlist" ou pelo botão "+" em cada música.
7. Nenhuma ação depende de arrastar, duplo clique, passar o mouse ou botão direito. Isso exclui, por exemplo, um botão de volume giratório arrastável: usa-se "−" e "+" com a imagem do botão.

## Consequências

- **Positivas:** o app atende ao objetivo de autonomia. A metáfora dá material consistente para justificar as decisões no TCC.
- **Negativas e riscos:**
  - Funções que antes ficavam com o cuidador (manutenção da coleção, montar discos) precisam ser **desenhadas** dentro da metáfora, o que é trabalho de UX novo e ainda em aberto.
  - A metáfora pode não funcionar bem para todas as ações, por exemplo renomear um disco. Isso precisa ser validado com o usuário real.
  - Se um aparelho antigo for usado como referência, ele deve ser o que o pai do autor realmente reconhece.
- **Mudanças no projeto:** o M4 deixa de ser "modo cuidador" e passa a ser "cuidar da coleção e montar discos". O M0 foi ajustado: tela cheia trocada por janela normal.

## Validação

Testes de usabilidade com o usuário real (tarefas como "toque o disco X", "volte para a estante", "monte um disco com estas músicas"), medindo tempo, erros e o questionário SUS. Observar especialmente se ele se sente perdido em alguma tela.

## Pendências

- Desenhar os botões, os ícones e as telas (inclusive a manutenção da coleção) com `ce-ideate`, e validar em um preview em HTML.
