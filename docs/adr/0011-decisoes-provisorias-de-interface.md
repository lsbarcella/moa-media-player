# ADR-0011 — Decisões provisórias de interface (M3)

- **Status:** Aceito como **PROVISÓRIO**. O autor revisa depois do MVP.
- **Data:** 26/11/2026
- **Decisor:** autor decidiu a metáfora e o preview (ADR-0002, ADR-0006, ADR-0007); os itens abaixo foram decididos pela IA na execução autônoma do MVP (`lfg`) e **precisam de revisão do autor**.

## Contexto

O M3 implementa as telas Estante, Tocando agora e Configurações a partir do preview aprovado (`docs/preview/moa-preview.html`). O CLAUDE.md deixa alguns pontos em aberto; para entregar o MVP sem parar, a IA escolheu o padrão do preview ou a opção mais simples e registra aqui.

## Decisões provisórias

| Ponto | Escolha provisória | Alternativa | Por quê |
| --- | --- | --- | --- |
| Progresso da música | Só texto no visor ("1:23 de 3:45"), **não clicável** | Barra clicável | Preview aprovado; clicar em ponto de barra é um gesto de precisão que o perfil de literatura desaconselha |
| Fim do disco | **Para** e diz "Este é o fim do disco."; "Tocar" recomeça na faixa 1 | Voltar para a estante | Não tira o idoso da tela sem aviso |
| Tema | **Claro** (texto escuro sobre fundo claro), com 4 paletas em Configurações | Escuro | Preview aprovado |
| Barra de título | **X do sistema** | Cabeçalho próprio com X grande | O X precisa ser o do sistema, que ele aprende a usar em todo programa (decisão do autor: o X da janela fica) |
| Ao abrir | Sempre na **Estante**, com "Continuar a ouvir" quando há onde parou; **nada toca sozinho** | Abrir direto no rádio | Preview aprovado ("estante que lembra"); o CLAUDE.md diz "ou, se havia algo tocando, em Tocando agora", e o cartão cumpre o mesmo papel sem som surpresa |
| Volume lembrado | O degrau do volume fica no JSON de configurações | Sempre começar em 6 | Evita o idoso refazer o volume toda vez |
| Estante ao abrir | Aparece quando a varredura incremental termina ("Estou procurando os seus discos..." enquanto isso) | Mostrar o cache antes | A varredura com cache lê só metadados de arquivo; mostrar o cache antes exigiria reconstruir os discos do banco. Medir no notebook real antes de complicar |
| Colunas em janela estreita | Rádio empilha as colunas em letra Grande/Maior ou janela com menos de 900 px | CSS com media query | O GTK 3 não tem media query; a troca é feita em código |
| Ícones | 10 SVGs originais e simples (tocar, pausar, anterior, próxima, volume, voltar, engrenagem, mais, caixa, disco), sempre ao lado de texto | Ícones de terceiros | Licença: arte original do projeto, GPL v3 ou posterior (como o código). A licença definitiva da arte continua pendente (ADR-0009) |

## Consequências

- Nada disso exige refazer a arquitetura: cada ponto é uma troca localizada (`session.py`, `radio.py`, `theme.py`).
- As paletas de daltonismo têm contraste de 7:1 **calculado** (teste automático); **não** foram validadas com simulador nem com pessoa daltônica.

## NÃO testado

Aparência em monitor real do notebook do usuário, tamanho real do X no Cinnamon, desempenho em HD mecânico.
