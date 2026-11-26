# ADR-0003 — Rede opcional e oportunista (MusicBrainz)

- **Status:** Aceito. Os detalhes de implementação foram aceitos "por enquanto" e podem ser revistos.
- **Data:** 26/11/2026
- **Decisor:** autor do TCC

## Contexto

A primeira versão do CLAUDE.md proibia qualquer uso de rede ("zero rede em tempo de execução"). O autor esclareceu que a ideia é o app **rodar as músicas offline**, mas que, **se houver internet, ele pode consultar o MusicBrainz** para atualizar as informações da estante. Isso também resolve um problema da cópia de CDs (M7): um CD não traz os nomes das faixas, e o MusicBrainz os fornece.

Cerca de 80% do acervo foi etiquetado com o MusicBrainz Picard e provavelmente já tem IDs do MusicBrainz nas tags, o que torna a consulta exata para a maior parte dos discos.

## Alternativas

| Alternativa | Autonomia do idoso | Privacidade | Complexidade | Resultado |
| --- | --- | --- | --- | --- |
| A. Zero rede, sempre | Média: discos sem tags ficam sem nome e capa | Máxima | Baixa | Descartada |
| B. Rede opcional e oportunista, em segundo plano | Alta | Boa, com cuidados | Média | **Escolhida** |
| C. Rede obrigatória para dados completos | Baixa: quebra com HD e sem internet | Pior | Média | Descartada |

## Decisão

Adotar a alternativa B:

1. **Tocar e navegar nunca dependem de internet.**
2. Com conexão, detectada por `Gio.NetworkMonitor`, o app consulta o MusicBrainz (e o Cover Art Archive para capas) **em segundo plano**, em thread separada, respeitando o limite de 1 requisição por segundo.
3. **Falha silenciosa:** sem internet, timeout ou erro, o idoso não vê mensagem nenhuma. Os detalhes vão para o log.
4. **Na dúvida, não muda nada.** Com ID do MusicBrainz nas tags, a consulta é exata. Sem ID, só se aceitam resultados de alta confiança.
5. **Nenhuma telemetria.** Só se envia o mínimo necessário (ID do disco ou artista e álbum). O cabeçalho de identificação do app é genérico, sem dados pessoais.

**Detalhes aceitos pelo autor "por enquanto" (revisáveis):**
- O resultado fica **só no cache do app**, sobreposto às tags, sem reescrever os arquivos de música. É reversível e não corrompe a coleção. Gravar nas tags pode ser avaliado depois.
- As atualizações aparecem **na próxima abertura** da estante, para a capa não mudar enquanto o idoso olha para ela.
- A comunicação usa `urllib` do Python, sem dependência nova (o pacote `python3-musicbrainzngs` é uma alternativa, a verificar no repositório do Mint).

## Consequências

- **Positivas:** discos sem tags e discos copiados de CD podem ganhar nome e capa sem ajuda de ninguém. O núcleo continua 100% funcional offline.
- **Negativas e riscos:**
  - A restrição 1 do projeto deixa de ser "zero rede" e passa a ser "offline por padrão". É preciso garantir, com teste, que nenhuma função de reprodução dependa da rede.
  - Correspondências erradas podem trocar um disco por outro. Mitigação: limiar de confiança e camada reversível.
  - Capas e nomes que mudam podem desorientar o idoso. Mitigação: aplicar na próxima abertura.
  - Há tráfego de rede, então é preciso respeitar o limite da API.
- **Mudanças no projeto:** novo módulo `core/musicbrainz.py` (sem GTK, testável com respostas falsas), fila de pendências no cache e o marco M6.

## Validação

- Testes automatizados com respostas falsas da API, incluindo falha, timeout e resultado ambíguo.
- Teste manual sem rede, confirmando que nada muda para o usuário.
- Conferir os limites e as regras de uso da API do MusicBrainz na documentação oficial antes de implementar.
