# Testes de usabilidade do Moa Media Player

Roteiro para avaliar o app com o usuário real (o pai do autor), no notebook dele. É um **protocolo de teste**: o que pedir, o que medir e como anotar. A análise e o texto do artigo são do autor.

> **Antes de aplicar:** confirme com o orientador (1) se é preciso um termo de consentimento e a aprovação ética da instituição, e (2) como a Uninter quer que o uso de IA seja declarado (o diário está em `docs/registro-ia.md`). O perfil do usuário foi definido **pela literatura** (ADR-0005), então este teste é a primeira observação direta.

## 1. O que se quer descobrir

| Pergunta | Como se responde |
| --- | --- |
| O idoso **se vira sozinho** (princípio central do projeto)? | Taxa de tarefas concluídas sem ajuda e número de dicas pedidas |
| As **metáforas** (estante, rádio, aparelho de CD, Lixeira) são entendidas? | Observação, o que ele diz em voz alta e a conversa final |
| Ele **nunca se sente perdido**? | Momentos de hesitação ("e agora?"), cliques sem efeito e uso do "Voltar para a estante" |
| Os **alvos grandes e o texto grande** ajudam? | Cliques errados, tempo por tarefa e opinião sobre o tamanho |
| O app é **rápido o bastante** no notebook dele? | Medição automática (`tools/measure.sh`) e a impressão de espera |

A hipótese de que o skeuomorfismo ajuda é tratada como **hipótese com evidência mista** (a favor: Urbano 2022; contra: Ellis & Marshall 2019). O teste serve para observar isso, não para presumir.

## 2. Preparação

- [ ] Notebook do usuário com a **versão do app anotada** (o commit aparece no resumo do `measure.sh` e, enquanto o atualizador de teste existir, em Configurações, "Versão instalada").
- [ ] Rodar `bash tools/measure.sh` **antes** das sessões e guardar o resumo (`medicoes/*.txt`).
- [ ] Coleção do usuário já na pasta de música. Escolher **3 discos conhecidos por ele** para as tarefas ("o disco X").
- [ ] Um **CD de verdade** à mão, para a tarefa 12 (se o leitor do notebook estiver funcionando).
- [ ] Volume do sistema ajustado uma vez; fones ou caixas conectados.
- [ ] Ambiente tranquilo, boa luz no monitor, **mouse** (não touchpad: é o que ele usa).
- [ ] Gravar a tela e o áudio (se ele concordar). Sem gravação, um observador anota.
- [ ] Imprimir a planilha (seção 5) e o questionário (seção 6) em **letra grande** (mínimo 16 pt).

**Piloto:** antes de ir ao usuário, o autor faz o roteiro inteiro sozinho e com uma pessoa próxima (de preferência não técnica), para acertar frases e tempos.

## 3. Como conduzir

1. **Acolhida (2 min).** Explique que o teste avalia **o programa, não ele**. Se algo for difícil, a falha é do programa. Ele pode parar quando quiser.
2. **Sem treino.** Não mostre nada antes. O app abre sozinho na Estante.
3. **Uma tarefa por vez**, lida em voz alta com as palavras da coluna "O que dizer". **Não use os nomes dos botões** do app (nada de "clique em Tocar"); descreva o objetivo.
4. **Pensar em voz alta:** peça que ele diga o que está pensando, sem insistir.
5. **Dicas em níveis**, anotadas: 0 = sem ajuda; 1 = o observador repete a tarefa com outras palavras; 2 = aponta a região da tela; 3 = faz por ele (a tarefa vale como "não concluída").
6. **Tempo máximo** por tarefa na tabela. Passado o tempo, encerre com calma e anote "não concluída".
7. **Não corrija o que ele faz de diferente** do esperado, se chegar ao objetivo: anote como caminho alternativo.
8. **Fim:** questionário SUS, conversa final e agradecimento.

## 4. Tarefas

| # | O que dizer | Sucesso quando | Tempo máx. | Mede |
| --- | --- | --- | --- | --- |
| 1 | "O programa já está aberto. Me diga o que você está vendo e para que serve." | Diz que são os discos/CDs dele | 60 s | Primeira impressão, metáfora da estante |
| 2 | "Quero ouvir o disco **[nome do disco 1]**." | A música do disco está tocando | 60 s | Pegar o disco da estante |
| 3 | "Pare a música um instante. Agora volte a tocar." | Pausou e voltou a tocar | 45 s | Tocar/Pausar |
| 4 | "Está baixo. Aumente o som. Agora diminua um pouco." | Volume mais alto e depois mais baixo | 45 s | Volume em degraus |
| 5 | "Pule para a próxima música. Agora volte para a anterior." | Trocou de faixa nos dois sentidos | 45 s | Próxima/Anterior |
| 6 | "Às vezes é difícil entender a voz. Tem algo que ajude?" | Ligou "Voz mais clara" e disse se ajudou | 90 s | Descoberta do controle |
| 7 | "Quero escolher outro disco: **[disco 2]**." | Voltou à estante e abriu o disco 2 | 60 s | Caminho de volta visível |
| 8 | "As letras estão pequenas para mim. Deixe maiores." | Mudou o tamanho da letra em Configurações | 90 s | Achar "Configurações" |
| 9 | "Monte um disco só com estas três músicas: **[A, B, C]**." | Disco novo criado com as três músicas | 180 s | Criar uma playlist |
| 10 | "Coloque a música **[D]** nesse disco novo." | A música D está no disco montado | 120 s | Botão "+" |
| 11 | "Não quero mais o disco **[disco 3]** na estante, mas sem perder as músicas. Depois traga de volta." | Tirou e recolocou o disco | 120 s | Lixeira, reversibilidade |
| 12 | "Aqui tem um CD novo. Coloque-o na sua estante." | O disco aparece na estante | 600 s | Aparelho de CD (se houver leitor) |
| 13 | "Feche o programa e abra de novo. Onde você parou?" | Fechou pelo X, abriu, e viu/usou "Continuar a ouvir" | 120 s | X da janela, retomar |

**Anote em cada tarefa:** concluída (S = sim, P = parcial, N = não), tempo, **erros** (clique que não levou a nada, tela errada, botão errado), **dicas** (0 a 3) e a frase dele, se for reveladora.

**Sinais para observar sempre:** hesita antes de clicar; procura o botão com o olhar; tenta duplo clique, arrastar ou clique direito (o app não usa); confunde um texto; se assusta com alguma mensagem; pede ajuda; fala em voz alta ("e agora?").

## 5. Planilha de tempo e erros

Um modelo em CSV está em [`usabilidade/planilha-de-tempo-e-erros.csv`](usabilidade/planilha-de-tempo-e-erros.csv) (uma linha por tarefa, por sessão). Colunas:

`sessao, data, versao_do_app, participante, tarefa, concluida (S/P/N), tempo_s, erros, dicas (0-3), caminho_alternativo (S/N), observacao`

Resumo por sessão (preencha no fim):

| Medida | Valor |
| --- | --- |
| Tarefas concluídas sem nenhuma dica | ___ de 13 |
| Tarefas concluídas com dica | ___ |
| Tarefas não concluídas | ___ |
| Erros no total | ___ |
| Tempo total das tarefas | ___ min |
| Pontuação SUS | ___ |

## 6. Questionário SUS (System Usability Scale)

Peça que ele marque, para cada frase, de **1 (discordo totalmente)** a **5 (concordo totalmente)**. Com um idoso, o observador **lê em voz alta** e anota a resposta, com um cartão de letra grande mostrando a escala. Isso muda a condição de aplicação (anote no relatório).

| # | Frase | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Eu acho que gostaria de usar este sistema com frequência. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 2 | Eu achei o sistema desnecessariamente complexo. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 | Eu achei o sistema fácil de usar. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4 | Eu acho que precisaria de ajuda de uma pessoa com conhecimentos técnicos para usar o sistema. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 | Eu acho que as várias funções do sistema estão muito bem integradas. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 6 | Eu acho que o sistema apresenta muita inconsistência. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 7 | Eu imagino que as pessoas aprenderão como usar este sistema rapidamente. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 8 | Eu achei o sistema atrapalhado de usar. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 9 | Eu me senti confiante ao usar o sistema. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 10 | Eu precisei aprender várias coisas novas antes de conseguir usar o sistema. | ☐ | ☐ | ☐ | ☐ | ☐ |

**Como calcular a pontuação (0 a 100):**

- Itens **ímpares** (1, 3, 5, 7, 9): contribuição = resposta − 1.
- Itens **pares** (2, 4, 6, 8, 10): contribuição = 5 − resposta.
- Some as 10 contribuições e **multiplique por 2,5**.

Como referência amplamente usada, uma pontuação em torno de **68** é a média; acima de 80 costuma ser considerada boa. **Não compare como se fosse medida exata:** com um único usuário e com a leitura em voz alta, o SUS é um indício, não uma estatística.

> **A conferir pelo autor:** a redação em português acima é a usual em estudos brasileiros, mas **confirme a referência da tradução/validação** que vai citar e use a redação dela. Referência do instrumento original: Brooke, J. (1996), "SUS: a quick and dirty usability scale".

## 7. Conversa final (5 a 10 min)

Perguntas abertas, sem induzir:

1. O que foi mais fácil? E o mais difícil?
2. Em algum momento você não soube o que fazer? Quando?
3. A **estante** lembra algo para você? E o **rádio**? E o **aparelho de CD**? E a **lixeira**?
4. O tamanho das letras e dos botões está bom? Algo está pequeno ou apertado?
5. Tem algum botão ou palavra que você não entendeu?
6. O som: dá para ouvir bem? A "Voz mais clara" ajudou?
7. Você usaria sozinho no dia a dia? O que faria você desistir?
8. Alguma coisa o incomodou na velocidade (esperar, travar)?

## 8. Depois da sessão

- [ ] Salvar a planilha, o SUS, a gravação e o resumo do `measure.sh` na mesma pasta, com data e versão do app.
- [ ] Listar os **problemas encontrados** com: o que aconteceu, em qual tarefa, gravidade (impede / atrapalha / incomoda) e quantas vezes.
- [ ] Transformar problemas em **decisões**: cada mudança de desenho vira um ADR (o autor decide UX e UI).
- [ ] Repetir os testes depois de corrigir, com o mesmo roteiro, para comparar.

## 9. Limites a registrar

- **Um único usuário** (e conhecido do autor): não há generalização estatística. É um estudo de caso.
- O autor é **desenvolvedor e observador ao mesmo tempo**, o que pode influenciar as dicas. Anote e use sempre as mesmas frases.
- O teste é no **notebook real**, e o desempenho dele pode afetar a percepção de usabilidade; por isso o `measure.sh` roda antes.
- O perfil (sem demência, declínio normal de visão, audição e motricidade) vem da literatura, não de avaliação clínica.
