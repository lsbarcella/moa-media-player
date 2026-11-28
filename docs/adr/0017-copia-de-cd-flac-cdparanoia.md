# ADR-0017 — Cópia de CD: leitura com cdparanoia, gravação em FLAC

- **Status:** Aceito. Detalhes técnicos da IA marcados como **provisórios**.
- **Data:** 27/11/2026
- **Decisor:** o autor escolheu o **formato (FLAC)** e a **leitura (cdparanoia)**; a IA escolheu a forma de implementar.

## Contexto

O notebook do usuário tem leitor de CD (confirmado em 27/11/2026), então o M7 é possível. O usuário deve poder colocar um CD sozinho, offline, e o disco aparecer na estante. O acervo atual já são CDs copiados, em pastas.

## Alternativas

- **Formato:** FLAC (sem perda, ~300 MB por CD, `flacenc` já vem no `gstreamer1.0-plugins-good`) ou MP3 (menor, mas exige `gstreamer1.0-plugins-ugly` para o `lamemp3enc` e perde qualidade). **Escolhido: FLAC.**
- **Leitura:** `cdparanoiasrc` (corrige riscos e erros de leitura) ou `cdiocddasrc` (mais simples, sem correção). **Escolhido: cdparanoia.**

## Decisão

1. `core/ripper.py` lê o CD com `cdparanoiasrc`, codifica com `flacenc` e grava em `Disco N/Faixa 01.flac`, sem dependência nova além do que já está nos plugins do GStreamer (mais `libcdparanoia0`, que o plugin já puxa).
2. O disco entra **offline** como **"Disco N"** (primeiro número livre), com tags mínimas gravadas com o mutagen: título "Faixa N", álbum "Disco N", número e total. O M6 corrige nomes e capas quando houver internet.
3. A cópia vai para uma pasta provisória `.Disco N.copiando` e só vira `Disco N` no fim. Falha ou cancelamento apagam a pasta provisória, então a estante nunca mostra um disco pela metade.
4. A cópia roda numa thread; a tela chama `cancelar()` de fora. Toda falha vai para o log e vira um `Resultado` (`COPIADO`, `CANCELADO`, `SEM_DISCO`, `FALHOU`), que a tela traduz em frase calma.
5. O número de faixas vem do sumário (TOC) que o `cdparanoiasrc` publica no GStreamer.
6. `tools/check_deps.sh` passa a conferir `cdparanoiasrc` e `flacenc`.

## Consequências

- Nenhum arquivo existente é tocado; um CD novo nunca sobrescreve outro disco.
- **Não testado com disco real**: a máquina de desenvolvimento tem o leitor, mas sem CD. Os testes usam um gerador de áudio no lugar do CD (`audiotestsrc`). Falta testar no notebook: a leitura do TOC (`contar_faixas_do_cd`), a qualidade da cópia, o tempo por CD num HD mecânico e discos riscados.
- **Pendente:** a tela de "colocar um disco" (o desenho precisa de proposta e aprovação do autor), a ejeção do disco e o ID do disco do MusicBrainz (calculável a partir do TOC) para o M6 achar o álbum exato.
- Espaço: ~300 MB por CD. Se o HD do notebook for pequeno, reavaliar (MP3).
