# ADR-0010 — Reprodução: motor, volume e "Voz mais clara"

- **Status:** Aceito, com valores **PROVISÓRIOS** (a ouvir com o usuário).
- **Data:** 26/11/2026
- **Decisor:** decisões estruturais já tomadas pelo autor (ADR-0004, CLAUDE.md); valores abaixo propostos pela IA, a revisar.

## Contexto

O M2 entrega o `moa/core/player.py`. O CLAUDE.md fixa: GStreamer com `playbin`, volume do app limitado a 100%, ReplayGain com `rgvolume`, botão "Voz mais clara" (começa desligado) e núcleo sem GTK.

## Decisão

1. **Um `playbin` por vez, com a fila do disco dentro do nosso código.** O app avança de faixa ao receber o fim de fluxo (EOS). Não usamos `about-to-finish` nem reprodução sem intervalo: para CDs a pausa entre faixas é natural e o tratamento de erro fica mais simples. Vídeo desligado nos flags do `playbin`.
2. **Cadeia de áudio no `audio-filter`:** `rgvolume` (modo álbum, pois toca-se o disco inteiro) → `equalizer-3bands` → `volume`. Se um plugin faltar, o app toca sem ele e registra no log.
3. **Volume em 11 posições (0 a 10), curva cúbica, teto 1.0, padrão 6.** O app nunca amplifica; o volume do sistema é ajustado uma vez na instalação. *Provisório:* a curva e o padrão 6 (ganho 0,216) precisam ser ouvidos no notebook do usuário.
4. **"Voz mais clara"** muda só os ganhos do `equalizer-3bands` (bandas de 100 Hz, 1,1 kHz e 11 kHz): **−3 dB, +3 dB, +6 dB**. Desligado, os ganhos voltam a zero. *Provisório:* valores ainda a ouvir com o usuário (ADR-0004). O `equalizer-3bands` está no `gstreamer1.0-plugins-good`, já dependência.
5. **Fim do disco = parar.** Tocar depois do fim recomeça o disco na faixa 1. *Provisório.*
6. **Erro numa faixa não para o disco:** o player avisa "erro na faixa" e toca a próxima; erro na última faixa para.

## Alternativas rejeitadas

- Reprodução sem intervalo (`about-to-finish`): complexidade sem ganho para CDs.
- Volume do sistema (PulseAudio): dependência e risco de distorção (decisão do autor).
- `equalizer-10bands`: ainda não confirmado no Mint; o de 3 bandas basta para o B1 do ADR-0004.

## Consequências

- O `rgvolume` pode aplicar ganho positivo (limitado pelo pico da faixa) em arquivos com ReplayGain; o "teto 100%" vale para o degrau do app, não para esse ajuste. Se isso incomodar, ajustar na revisão.
- Os testes usam `fakesink`; **nada foi ouvido por uma pessoa nem numa placa de som real.**

## NÃO testado

Som real, qualidade do equalizador, ReplayGain com arquivos etiquetados reais, comportamento em CPU antiga.
