# ADR-0006 — Configurações de acessibilidade: tamanho da letra e cores

- **Status:** Aceito. As paletas de daltonismo são uma primeira versão a validar.
- **Data:** 26/11/2026
- **Decisor:** autor do TCC

## Contexto

O CLAUDE.md deixava em aberto se haveria um controle de tamanho da letra visível ao usuário ou só uma fonte grande por padrão. A literatura consultada traz dois sinais:

- Coyne e Nielsen (2002, via revisão da W3C sobre usuários idosos) recomendam um controle de aumentar texto, porque idosos não conhecem os controles do navegador. O "non-browser" de Gregor e Dickinson (2007) tinha botões "ampliar" e "preto e branco" sempre à mão.
- Gregor, Newell e Zajicek (2002) falam em "diversidade dinâmica": as necessidades dos idosos variam e mudam com o tempo. Sem cuidador no projeto (ADR-0002), o próprio usuário precisa poder se ajustar.

**As fontes vieram de resumos de busca e precisam ser conferidas antes de citadas no artigo.**

## Alternativas

| Alternativa | Prós | Contras | Resultado |
| --- | --- | --- | --- |
| A. Só fonte grande por padrão, sem controle | Interface mais simples | Não acompanha mudanças; não atende quem precisa de mais | Descartada |
| B. Controle de letra visível no cabeçalho de todas as telas | Descoberta fácil (é o que a literatura recomenda) | Mais botões em toda tela; contra a regra de poucas opções | Descartada |
| **C. Botão "Configurações" com texto, sempre visível no cabeçalho, que abre uma tela com letra e cores** | Cabeçalho limpo; um lugar único para ajustes de acessibilidade; cabe daltonismo | O usuário precisa descobrir o botão; mais uma tela | **Escolhida** |

## Decisão

Adotar a C:

- Um botão **"Configurações"** (texto sempre visível, de no mínimo 64 px) fica no cabeçalho, fora da tela de Configurações.
- A tela de Configurações tem o **tamanho da letra** (Normal, Grande e Maior, com um exemplo ao vivo) e as **cores**: cores padrão, dificuldade com vermelho e verde, dificuldade com azul e amarelo, e preto e branco bem forte. Os nomes evitam jargão ("protanopia" e similares não aparecem).
- O botão de volta da tela de Configurações diz **"Voltar para onde eu estava"**, porque ela abre em cima de qualquer tela.
- Todas as paletas mantêm contraste de pelo menos 7:1 (conferido por cálculo).
- O app **nunca usa só a cor** para comunicar algo: estado, seleção e volume têm sempre texto, forma ou posição. A configuração de cores é uma camada extra, não a base.
- As escolhas são guardadas entre as sessões.

## Consequências

- **Positivas:** o idoso se ajusta sozinho, sem cuidador. Cabeçalho mais limpo que na alternativa B.
- **Negativas e riscos:**
  - O usuário pode não achar o botão. A literatura recomenda o controle de letra visível, e a alternativa C o deixa um clique mais longe. A descoberta do botão deve ser observada no teste.
  - A palavra "Configurações" pode soar técnica; o texto do botão deve ser revisto se o teste mostrar confusão.
  - As paletas de daltonismo foram montadas por cálculo de contraste, **sem simulador de daltonismo e sem uma pessoa daltônica**. Precisam ser validadas (por exemplo com um simulador como o Color Oracle e, de preferência, com alguém daltônico). A paleta "azul e amarelo" é a menos certa.
  - Parte do tamanho do texto é decidida pelo sistema (escala do Cinnamon). É preciso testar se a escala do app e a do sistema se combinam bem.
- **Mudanças no projeto:** a tela de Configurações entra no M3, e o `core/config.py` guarda as preferências (letra e cores).

## Validação

Teste de usabilidade do M9 com o usuário real: ele acha o botão sozinho, entende as opções e consegue voltar? As paletas de daltonismo precisam de validação externa antes de serem apresentadas como funcionais.
