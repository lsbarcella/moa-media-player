# ADR-0021 — Medição de desempenho repetível (`tools/measure.sh`)

- **Status:** Aceito. Detalhes técnicos da IA marcados como **provisórios**.
- **Data:** 27/11/2026
- **Decisor:** o autor pediu a medição automatizada para comparar o notebook do usuário com a máquina de desenvolvimento; a IA desenhou a ferramenta.

## Contexto

O CLAUDE.md (seção 10) fixa metas de abertura, RAM e CPU, e o primeiro teste no notebook do usuário mostrou travadas (lista de 371 faixas refeita a cada clique) que só apareciam lá. É preciso medir de forma repetível, na máquina real, e guardar os números para o capítulo de Resultados.

## Decisão

1. `bash tools/measure.sh` roda `tools/measure.py`, que gera duas coleções sintéticas e grava um CSV em `medicoes/` (fora do git):
   - `mix`: **um disco com 371 faixas**, como a coleção do usuário;
   - `estante`: 80 discos de 10 faixas, como o acervo descrito no CLAUDE.md.
2. **Abertura** (processo de verdade, na sessão gráfica real): tempo até a estante aparecer (o app registra `estante pronta` no log), sem o cache do app (`abertura_1a_ms`) e com ele (`abertura_seguinte_ms`), mais RAM (RSS) e CPU em repouso.
3. **Ações** (dentro do processo da medição, com a janela desenhada fora da tela, sobre uma coleção de **faixas longas** (links para um áudio de 5 minutos), para o disco não avançar sozinho; o "tela pronta" tem limite de 5 s): mediana e máximo, em 5 repetições, de abrir disco, tocar/pausar, próxima, tocar a faixa do meio, volume, "Voz mais clara", voltar à estante, criar playlist, Caixa, Aparelho de CD e Configurações. O tempo vai até a tela estar desenhada.
4. **CPU tocando** (som de verdade, 10 s, MP3 se o codificador existir, senão FLAC): CPU do processo, onde 100% é um núcleo. `--sem-audio` pula.
5. O CSV leva em cada linha a configuração da máquina (CPU, núcleos, RAM, tipo de disco, sistema, desktop, Python, GTK, versão do app). **Sem nome da máquina nem do usuário.**
6. A ferramenta compara com as metas do CLAUDE.md (abertura fria ≤ 3 s, quente ≤ 1 s, CPU tocando < 5%). A comparação da RAM com o Rhythmbox e o VLC continua manual.

## Acompanhamento durante a medição

A medição leva alguns minutos e tem esperas de propósito (a RAM e a CPU em repouso). Para ninguém achar que travou:
- cada passo tem número e hora desde o começo (`(4/6) ...`) e as esperas dizem o motivo;
- se passam 5 s sem nenhuma linha nova, aparece "ainda trabalhando (passo ou ação atual)";
- um passo que falha é anotado e o resto da medição continua; a falha vai para o resumo, e o detalhe técnico para o `.log`.

Cada rodada grava três arquivos em `medicoes/`: `.txt` (resumo curto, para colar numa conversa), `.csv` (todos os números) e `.log` (tudo o que apareceu na tela, mais os detalhes das falhas). O resumo também é impresso entre "copie daqui" e "até aqui". **Nada é enviado pela rede**: quem mede decide o que compartilhar.

## Limites e escolhas

- **Não isola o D-Bus.** Numa sessão nova (`dbus-run-session`) o app demorou ~25 s para começar, o que não acontece de verdade. Por isso a medição usa a sessão real, e o script se recusa a rodar se já houver um Moa aberto (ele atenderia o pedido, por ser instância única).
- **"Abertura a frio"** aqui é "sem o cache do app", não "depois de reiniciar". Com `--frio` o script esvazia o cache de arquivos do sistema (precisa de `sudo` sem senha); sem isso o número fica otimista no HD mecânico. A medida de verdade a frio exige reiniciar a máquina antes.
- As ações são medidas com um destino de som falso (`fakesink`) para separar o custo da tela do custo do áudio.
- A coleção é sintética: arquivos curtos, sem capas embutidas. A leitura de capas e de arquivos grandes em HD mecânico não está representada.

## Consequências

- O app ganhou uma linha de log (`estante pronta: N discos`) que serve de ponto de medição.
- **Não rodado no notebook do usuário ainda.** A primeira rodada lá é a linha de base; cada otimização é comparada com ela.
