# ADR-0004 — Audição: botão "Voz mais clara" no rádio

- **Status:** Aceito (princípio). Estado padrão e valores do ajuste ainda precisam ser testados.
- **Data:** 26/11/2026
- **Decisor:** autor do TCC

## Contexto

O plano original só tratava de som com o ReplayGain (`rgvolume`), que iguala o volume entre discos mas não ajuda quem ouve mal. Uma conferência do plano com a literatura levantou a audição como a maior lacuna:

- A revisão da W3C sobre usuários idosos (WAI-AGE, 2008) cita que, no Reino Unido, 55% das pessoas com mais de 60 anos têm perda auditiva, com perda maior em sons agudos.
- Um estudo da Universidade de Oldenburg (*Journal of the Acoustical Society of America*, via resumo de divulgação) achou que ouvintes com perda auditiva preferem voz mais alta, mais agudos e mixagens mais "limpas". Guias clínicos dizem que aumentar o volume não resolve e pode distorcer.
- Não encontrei estudo de usabilidade que teste controles de volume ou equalização em player para idosos.

**As fontes vieram de resumos de busca e precisam ser conferidas antes de citadas no artigo.**

## Alternativas

| Alternativa | Prós | Contras | Resultado |
| --- | --- | --- | --- |
| A. Só ReplayGain | Zero custo; rádio mais simples | Ignora a lacuna; o volume vira o único recurso | Descartada |
| **B1. "Voz mais clara" (liga/desliga)** | Um botão só; estado claro em texto; segue a preferência por voz e agudos | Um único ajuste fixo; pode não servir a ele | **Escolhida** |
| B2. "Tom" com "Mais grave" / "Mais agudo" | Ajuste mais fino; lembra o botão de tom do rádio antigo | Mais botões e decisões; risco de desajustar sem saber voltar | Possível evolução |
| C. Pré-ajuste feito pelo autor na instalação, sem controle visível | Rádio limpo | Traz de volta a dependência de outra pessoa (contra o ADR-0002); não acompanha mudanças na audição | Descartada |

Um "teste de ouvido" para calibrar foi descartado por escopo e por parecer diagnóstico médico.

## Decisão

Adotar a B1: o rádio terá um botão **"Voz mais clara"**, liga/desliga, com o estado em texto ("Voz mais clara: ligada" ou "desligada"), com alvo de no mínimo 64×64 px. O ajuste usa um equalizador do GStreamer que reforça as frequências de voz e agudos. A escolha do usuário é guardada entre as sessões.

- O elemento `equalizer-3bands` está no `gstreamer1.0-plugins-good`, **que já é dependência do projeto** (confirmado na máquina de desenvolvimento). Não há dependência nova. O `equalizer-10bands`, que tem bandas de 4 kHz e 8 kHz, é candidato se o de 3 bandas não bastar, mas **ainda não foi verificado**.
- O volume continua sendo o do app, com limite em 100% (sem ganho acima disso, para não distorcer). O volume do sistema é ajustado uma vez na instalação. **Confirmado pelo autor.**
- **O estado padrão é desativado**, também confirmado pelo autor. A escolha do usuário é guardada entre as sessões.

## Consequências

- **Positivas:** responde à lacuna sem acrescentar escolhas ao idoso e sem dependência nova. Cabe na metáfora do rádio.
- **Negativas e riscos:**
  - É mais um botão no rádio, e a literatura sobre escolha em idosos pede poucas opções.
  - Os valores do ajuste são hipóteses: não sabemos se ajudam o usuário real. É preciso testar com ele ouvindo.
  - Um ajuste de equalização pode interagir mal com aparelhos auditivos ou fones.
  - Como o padrão é desativado, quem não achar o botão não terá o benefício; a descoberta do botão precisa ser observada no teste.
- **Mudanças no projeto:** o `core/player.py` (M2) passa a incluir o equalizador, e a tela Tocando agora (M3) ganha o botão.

## Validação

Teste de escuta com o usuário real, comparando com e sem o ajuste. Observar se ele encontra o botão, entende o estado em texto e prefere a opção ligada. Se não bastar, avaliar a B2.
