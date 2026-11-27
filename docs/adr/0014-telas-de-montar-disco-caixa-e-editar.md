# ADR-0014 — Telas do M4: montar disco, painel do "+", Caixa e editar disco

- **Status:** Aceito. Os detalhes de implementação da IA são **provisórios**.
- **Data:** 27/11/2026
- **Decisor:** o autor decidiu o conceito e aprovou o preview (ADR-0007, `docs/preview/moa-preview.html`); a IA escolheu a estrutura das telas. Os dados por trás delas estão no ADR-0012.

## Contexto

O M4 dá ao próprio idoso o cuidado da coleção, sem cuidador e sem modo escondido (ADR-0002). Tudo dentro da metáfora: o resultado de montar um disco é "um disco na estante", e tirar um disco é "guardar numa caixa". A regra mais delicada é que só "Apagar de vez" apaga arquivos, e só dentro da Caixa.

## Decisão

1. **Quatro telas/painéis, todos dentro da janela única** (nenhuma janela modal nova), cada um com o caminho de volta visível do cabeçalho (ADR-0011):
   - **Montando um disco novo** (`ui/playlist_view.py`, "Criar uma playlist"): lista de músicas com caixas de marcar de 64 px, sempre com o nome do disco de origem ao lado (as duplicatas são faixas distintas). Digitar em qualquer ponto manda a letra para a busca (atalho tratado em `Conteudo.tratar_tecla`). As marcações ficam num rascunho (`RascunhoDePlaylist`) fora do filtro, então filtrar não desmarca nada. Nome sugerido "Meu disco de dd/mm", sem repetir. "Guardar na estante" cria o disco e volta à estante com um aviso.
   - **Painel do "+"** (`ui/plus_panel.py`, "Em qual disco?"): fica por cima da tela, com "Disco novo" tracejado primeiro e as capas dos discos montados. A confirmação aparece na linha da música, com "Desfazer"; não duplica uma música já presente.
   - **A Caixa** (`ui/box_view.py`): lista os discos tirados, com "Colocar de volta na estante" e "Apagar de vez". Este abre uma pergunta clara com "Manter o disco" em destaque e "Sim, apagar de vez"; para disco montado o texto diz que só o disco será desfeito, sem tocar nas músicas.
   - **Mexendo no disco** (`ui/edit_view.py`): nome e capa (do arquivo, da pasta ou desenhada) com prévia ao vivo; "Guardar" e "Deixar como estava" são dois botões grandes; depois de guardar, o aviso oferece "Como era antes". Também tem "Tirar da estante". **Não tem "Apagar de vez".**
2. **Avisos até a próxima ação** (decisão do autor, R15): confirmações, "Desfazer" e falhas ficam na tela até o usuário fazer outra coisa. O "Desfazer" é a única ação que não apaga o aviso antes de rodar.
3. **Falhas calmas:** erro ao gravar, trocar capa ou apagar mostra uma frase no aviso da própria tela ("Não consegui apagar tudo. O que sobrou continua na Caixa."); o detalhe vai para o log. As marcações da playlist são mantidas se gravar falhar.
4. **Sem jargão:** nenhuma tela usa "pasta", "tag", "varredura", "playlist" aparece só no botão pedido pelo autor.

## Alternativas rejeitadas

- Janelas de diálogo para confirmar: contrariam a regra de nenhuma janela modal inesperada.
- "Apagar de vez" também na tela de editar: o autor decidiu que só existe na Caixa (ADR-0007), para o gesto de apagar exigir dois passos conscientes.
- Duas frases no "+" ("Adicionar a uma playlist existente" / "Criar uma nova playlist"): substituídas pelas capas dos discos (ADR-0007).

## Consequências

- Cada tela é testada fora da tela (`Gtk.OffscreenWindow`), com os PNGs conferidos contra o preview.
- **Não testado:** uso real pelo idoso; se ele entende "A Caixa" e "Mexendo no disco" é hipótese para o teste de usabilidade (M9).
