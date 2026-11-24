# ADR-0001 — Escolha da stack tecnológica

- **Status:** Aceito
- **Data:** 22/11/2026
- **Decisor:** autor do TCC

## Contexto

O app é um reprodutor de música para um idoso, executado em um notebook antigo com Linux Mint (Cinnamon). Ele precisa funcionar 100% offline e ser leve. O escopo é só áudio. O autor conhece TypeScript, mas não Python nem Rust. A implementação terá assistência de IA, então o código precisa ser legível para o autor revisar, defender e manter.

## Critérios (em ordem de peso)

1. Consumo de recursos em hardware legado: RAM, CPU e tempo de abertura.
2. Funcionar bem sem GPU moderna.
3. Disponibilidade no Linux Mint, de preferência já instalado.
4. Legibilidade e manutenibilidade pelo autor.
5. Maturidade do ecossistema (documentação, bibliotecas de áudio e metadados).
6. Risco de prazo do TCC.

## Alternativas consideradas

| Alternativa | Recursos | Sem GPU moderna | No Mint | Legível para o autor | Ecossistema | Risco | Resultado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A. Python + GTK3 + GStreamer | Bom | Bom | Sim | Alta | Maduro | Baixo | **Escolhida** |
| B. TypeScript + GJS | Bom | Bom | Parcial | Alta | Pouco documentado | Médio | Descartada |
| C. Rust + gtk-rs | Ótimo | Bom | Compilação externa | Baixa | Maduro | Alto | Descartada |
| D. Vala + GTK3 | Ótimo | Bom | Compilação externa | Média | Restrito | Médio | Descartada (possível protótipo comparativo) |
| E. Electron | Ruim | Regular | Não | Alta | Maduro | Baixo | Descartada |
| F. Tauri | Regular | Regular | Parcial | Média | Em amadurecimento | Médio | Descartada |
| G. iced / Slint (Rust) | Bom | Incerto | Compilação externa | Baixa | Em amadurecimento | Alto | Descartada |

As avaliações são qualitativas e serão confirmadas por medição.

## Decisão

Python 3 + GTK3 (PyGObject) + GStreamer + mutagen, com a lógica separada da interface.

- A decodificação de áudio e o desenho da interface acontecem em bibliotecas nativas em C (GStreamer e GTK). A linguagem de cola executa poucas ações por minuto, então pesa pouco no desempenho e rende muito em legibilidade e produtividade.
- GTK3 em vez de GTK4: o GTK4 renderiza por GPU e pode ficar pesado em placas antigas. O GTK3 é o toolkit do próprio Cinnamon.

## Consequências

- **Positivas:** quase nenhuma dependência extra no Mint, código legível e muita documentação disponível.
- **Negativas:** mais RAM e abertura mais lenta que uma solução compilada. O GTK3 está em modo de manutenção.
- **Riscos e mitigação:**
  - Abertura lenta em HD mecânico: iniciar com a sessão, mostrar a janela imediatamente e garantir instância única.
  - mutagen ausente: declarar como dependência do .deb.
  - Instalação sem internet: pacote .deb testado offline.

## Validação

Medir RAM, CPU, tempo de abertura (a frio e a quente) e tamanho instalado na máquina do usuário, comparando com Rhythmbox e VLC.

## Nota

As afirmações técnicas deste ADR devem ser conferidas na documentação oficial (PyGObject, GTK, GStreamer, mutagen) antes de citadas no TCC.
