# ADR-0027 — Ano do disco (tags e MusicBrainz) e "Artista · Álbum · Ano" no visor do rádio

- **Status:** Aceito.
- **Data:** 28/11/2026
- **Decisor:** o autor. Perguntou por que a capa descoberta pelo MusicBrainz não aparecia e propôs mostrar artista, álbum, ano e capa. Escolheu a opção B: o rádio mostra "Artista · Álbum · Ano", lendo o ano das tags e aproveitando o que o MusicBrainz trouxe.

## Contexto

O app lia artista, álbum e número da faixa, mas **nunca lia o ano**, e o artista não aparecia no rádio. O MusicBrainz (M6) já guardava nome, artista e capa por disco, mas só quando as tags não diziam nada.

## Alternativas

A) só o artista no rádio e na estante; **B) artista, álbum e ano no rádio (escolhida)**; C) B mais uma tela "Sobre este disco" (capa grande, gravadora, faixas com duração), que fica para depois.

## Decisão

1. **Ano das tags.** `Track.year` vem da tag de data (`date`, `TDRC` ou `originaldate`), em qualquer formato ("2005", "2005-03-01", "1987-1989"), aceito de 1800 a 2100; lixo vira `None`. `Album.year` é o ano que mais se repete entre as faixas (empate: o mais antigo). Discos montados (playlists) não têm ano.
2. **Ano do MusicBrainz.** `RegistroMB.year` vem da data de lançamento da resposta. Como o resto da camada (ADR-0003), só vale **onde as tags não têm ano**: a tag do usuário vence sempre, e nada é reescrito nos arquivos.
3. **Quando consultar.** Um disco sem ano nas tags passa a justificar uma consulta (antes só disco sem nome ou sem capa). Disco completo, com ano, continua sem consulta.
4. **Banco: migração 5.** Colunas `year` em `tracks` e `musicbrainz`. As faixas já guardadas ganham `mtime = -1` (data impossível), o que faz a **próxima varredura reler as tags de todos os arquivos uma vez** para achar o ano. Nenhuma tag é alterada.
5. **Visor do rádio.** Uma linha "Artista · Álbum · Ano", só com o que existe (artista igual ao nome do disco não se repete), e a linha "Faixa X de Y" separada. Foi preciso enxugar o espaçamento do painel para o volume continuar na primeira tela em 1366×768 e letra "Maior" (um teste confere).

## Consequências

- **A primeira abertura depois da atualização relê as tags de toda a coleção** (371 arquivos no mix do usuário): um pouco mais lenta uma vez, só no notebook do pai.
- Discos que o MusicBrainz já tinha marcado como "ok" **não** são reconsultados só para pegar o ano (só os novos e os "sem certeza" depois de 30 dias).
- A capa do MusicBrainz **continua só para discos sem capa própria** e só aparece na abertura seguinte à consulta. Se for preciso mudar essa regra (trocar capa ruim por melhor), exige decisão do autor e confiança alta no disco encontrado.
- **Em aberto:** mostrar artista e ano também na Estante; a opção C (tela "Sobre este disco"); o log do notebook para saber por que o MusicBrainz não trouxe capa lá.
- **NÃO testado** no notebook do pai.
