# Pendências e pontos de retomada

Estado em **28/11/2026**. Este arquivo existe para o autor (e a IA) retomarem de onde pararam. Atualize-o ao fim de cada sessão.

## Git: atenção antes de testar
- A branch de trabalho é `feature/tema-hifi`. **A `dev` NÃO tem todos os commits dela** (os PR #14 e #15 foram mergeados antes de alguns pushes). Falta mergear: a barra do rádio recolhida, o painel do rádio fixo, as letras 14/16/18/21 e a opção Pequeno, o botão "Guardar o disco" removido e os previews de tipografia. Abrir PR de `feature/tema-hifi` para `dev` **depois de a IA avisar que terminou**.
- Já mergeadas e apagáveis: `feature/barra-de-rolagem`, `feature/aparencia-nivel-3`, `feature/feedback-da-atualizacao`.
- **Não apertar "Atualizar agora" no app rodando da pasta do projeto**: o atualizador de teste (ADR-0020) troca `moa/` e `tools/` pela `dev` e desfaz o trabalho não comitado.
- Sem `gh` instalado: o PR é aberto pelo navegador (link de compare do GitHub).

## Decisões já tomadas (resumo)
- Tema **hi-fi** cinza e grafite (ADR-0025). Volume só com ícone (alto-falante com − e +), com nome acessível.
- **Barra do rádio** nas outras telas: uma linha, "Abrir o rádio" à direita, fio de andamento sempre à vista e progresso clicável flutuando só com o mouse (ADR-0026, ADR-0028). Sem nada tocando, a barra some.
- **Ano do disco** nas tags e no MusicBrainz; visor mostra "Artista · Álbum · Ano" (ADR-0027).
- **Letras:** Pequeno 14, **Normal 16 (padrão)**, Grande 18, Maior 21 px (ADR-0029). Botão "Guardar o disco na estante e parar" removido da tela do rádio (a função continua no código).
- **Tipografia:** Atkinson Hyperlegible + Roboto Slab, ambas pelo apt (ADR-0030). **Não implementada ainda.**

## Próximos passos (em ordem sugerida)
1. **Implementar a tipografia** (ADR-0030): `font-family` e pesos no `theme.py`; `fonts-atkinson-hyperlegible` e `fonts-roboto-slab` no `.deb` e no `check_deps.sh`; testes; conferir as telas nos 4 tamanhos de letra.
2. Decidir: estado "Pausado" ou "PAUSADO"; números de largura igual (recomendado); a Roboto Slab só nos nomes (combinado).
3. No notebook: `apt-cache policy fonts-atkinson-hyperlegible fonts-roboto-slab` (e se falta a Atkinson no Mint, embutir).
4. **Mergear** `feature/tema-hifi` na `dev` (PR) e testar no notebook; apagar as branches remotas já mergeadas.

## Perguntas em aberto para o autor
- **Capa do MusicBrainz não aparece:** rodar no notebook `grep -i musicbrainz ~/.local/share/moa/moa.log | tail -20` e trazer o resultado. (A regra atual: só baixa capa para disco sem capa própria, e só mostra na abertura seguinte.)
- Artista e ano também **na Estante**, sob a capa?
- Opção C: tela **"Sobre este disco"** (capa grande, ano, faixas com duração).
- **Transporte** (Anterior, Tocar/Pausar, Próxima) também só com símbolo, ou com texto?
- A barra do pé fica na tela até fechar o app depois de pôr um disco: aceitável, ou o botão de guardar volta?
- Interruptor de aparência "Simples ou Aparelho" (I7), nunca decidido.
- Cor da lombada da caixa de CD e a sombra rígida (padrões atuais: cinza-escuro e preta).

## Para validar no teste de usabilidade (hipóteses)
- 16 px como padrão basta para o idoso? (a regra antiga era 20 px)
- O idoso reconhece o alto-falante com − e + sem a palavra?
- Ele percebe que a barra de progresso é clicável?
- A Atkinson Hyperlegible ajuda de fato?

## Medições
- Linha de base e depois do nível 3 (máquina de desenvolvimento, i5): ações em 13 a 53 ms, RAM 86 a 89 MB. **Não medido no Pentium T4300** desde o tema hi-fi. A primeira abertura depois do ADR-0027 relê as tags de tudo uma vez.
