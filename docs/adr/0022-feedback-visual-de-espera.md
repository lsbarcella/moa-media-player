# ADR-0022 — Feedback visual nas esperas (primeira: o "carregando" da estante)

- **Status:** Aceito. Detalhes técnicos da IA marcados como **provisórios**; o texto das frases e o desenho ficam abertos à revisão do autor.
- **Data:** 27/11/2026
- **Decisor:** o autor pediu feedback visual onde se espera demora (mais de 5 s); a IA propôs e implementou o primeiro caso.

## Contexto

A medição no notebook do usuário (Pentium T4300, HDD) mostrou 11,9 s para a primeira leitura de 800 faixas e 2,7 s para as 371 do usuário. Durante esse tempo a estante ficava com uma frase parada ("Estou procurando os seus discos..."), parecendo travada. O CLAUDE.md pede que o idoso nunca se sinta perdido e nunca veja jargão.

## Decisão

1. **Indicador girando + frase calma + andamento em palavras simples**, no cartão que já existia: "Já olhei 340 músicas." (a leitura não sabe o total antes de terminar) e depois "Preparando as capas: 12 de 80.".
2. **Só depois de 5 s** aparece a frase de tranquilidade: "Isso pode demorar um pouco na primeira vez. Pode esperar: está tudo certo e não precisa fazer nada." Em esperas curtas nada extra aparece.
3. O andamento é atualizado **no lugar** (só o texto), no máximo 10 vezes por segundo, sem redesenhar a estante. O relógio da janela (500 ms) confere o tempo para o aviso de demora.
4. Sem dependência nova: `Gtk.Spinner`. O núcleo (`library`, `covers`, `Contexto`) só guarda e avisa números; quem desenha é a tela.

## Outros momentos de espera (estado atual)

- Copiar CD: barra de progresso e "COPIANDO: Faixa X de Y" (ADR-0018).
- Atualização de teste: frases de estado (ADR-0020, temporária).
- **Ainda sem feedback:** abrir um disco muito grande e criar playlist (centenas de linhas montadas de uma vez; ~0,3 a 0,6 s no notebook do usuário). A ideia é montar a lista em pedaços, com as primeiras linhas aparecendo na hora.

## Consequências

- **Não testado no notebook do usuário.** O Spinner anima sempre; se pesar na CPU antiga ou incomodar, trocar por uma barra sem animação.
- O contraste do indicador é menor que o do texto; por isso ele nunca vem sozinho (acompanha a frase).
