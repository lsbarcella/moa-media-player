# ADR-0015 — MusicBrainz opcional: detalhes de implementação (M6)

- **Status:** Aceito. Os detalhes técnicos da IA são **provisórios**; a decisão de fundo é o ADR-0003.
- **Data:** 27/11/2026
- **Decisor:** o autor decidiu o princípio (ADR-0003: offline por padrão, rede só como bônus, na dúvida não muda nada); a IA escolheu a forma.

## Contexto

O ADR-0003 manda consultar o MusicBrainz e o Cover Art Archive em segundo plano, com falha silenciosa e sem telemetria. Faltava decidir quando consultar, o que aceitar e onde guardar.

## Decisão

1. **Só consulta quando algo pode melhorar:** disco **sem capa** (nem embutida, nem da pasta) ou disco **sem a tag de álbum** (o nome veio da pasta). Disco completo não gera nenhum pedido (menos rede, mais privacidade).
2. **Como identifica o disco:**
   - com `musicbrainz_albumid` nas tags (o Picard grava): consulta exata, por ID. O ID só entra na URL se tiver o formato de UUID;
   - sem ID, mas com artista **e** álbum nas tags: busca e aceita só um resultado com o **mesmo nome, o mesmo artista e o mesmo número de faixas**;
   - sem nada disso, **nenhuma consulta**: o disco fica como está.
3. **Onde guarda:** tabela `musicbrainz` (migração 4, aditiva), por pasta do disco, com status `ok` ou `nada`. Nenhum arquivo de música ou tag é reescrito. Capas baixadas ficam em `~/.local/share/moa/capas-musicbrainz/`.
4. **Como se sobrepõe às tags** (`musicbrainz.aplicar`): nome do disco só se nenhuma faixa tem a tag de álbum; artista só se o disco não tem; nome de faixa só se ela não tem título na tag **e** o número de faixas bate. A capa baixada só vale se o disco não tem capa própria. **A escolha do usuário (nome e capa, M4) vence o MusicBrainz.**
5. **Só na próxima abertura:** o `Contexto` lê a camada uma vez, ao abrir, e não a relê durante a sessão. Um resultado que chega com o app aberto fica gravado e aparece na abertura seguinte.
6. **Rede:** `urllib`, sem dependência nova; no máximo 1 pedido por segundo (`Limitador`); tempo limite de 10 s; respostas limitadas em tamanho; a capa precisa começar como JPEG ou PNG. Depois de 3 falhas seguidas, desiste até a próxima abertura. Erro de rede não grava nada (tenta de novo depois); "sem certeza" só é reconsultado depois de 30 dias.
7. **Quando roda:** numa thread, **depois** de a estante ser entregue à tela, só se `Gio.NetworkMonitor` disser que há conexão. `MOA_SEM_REDE=1` desliga (usado em medições).
8. **Privacidade:** vai pela rede só o ID do álbum, ou o artista e o nome do álbum. O cabeçalho `User-Agent` é `MoaMediaPlayer/0.1`: sem e-mail, sem nome de pessoa, sem dados da máquina.

## Alternativas rejeitadas

- Consultar todos os discos: pedidos inúteis num acervo de ~80 discos, e mais dados saindo da máquina.
- Aceitar o melhor resultado da busca mesmo sem certeza: arrisca trocar o nome de um disco certo por um errado, que o idoso não saberia desfazer sozinho.
- Gravar o resultado nas tags: não é reversível (ADR-0003).

## Consequências

- **Para o acervo real**, os discos já etiquetados pelo Picard e com capa nunca geram consulta. A rede ajuda mesmo nos discos sem capa e nos que o M7 copiar de CD.
- O `User-Agent` genérico pode ser limitado pelo MusicBrainz, que prefere um contato. Se isso acontecer, o autor decide o que pôr nele; a IA não pôs dados pessoais.
- **Não testado:** contra os servidores reais (todos os testes usam um servidor falso local); o comportamento dos nomes de faixa em discos de vários CDs.
