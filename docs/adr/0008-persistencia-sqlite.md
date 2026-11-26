# ADR-0008 — Persistência: SQLite para biblioteca e dados do usuário, JSON para configurações

- **Status:** Aceito.
- **Data:** 26/11/2026
- **Decisor:** autor do TCC

## Contexto

O CLAUDE.md deixava em aberto o formato do cache da biblioteca (JSON ou SQLite). A IA recomendou JSON por simplicidade, considerando só o cache da varredura. O autor perguntou se SQLite não seria o correto e informou que a coleção tem cerca de **800 faixas**.

Duas coisas mudaram a análise:

1. **Desempenho não decide.** Medição na máquina de desenvolvimento, com 800 faixas sintéticas: JSON de 224 KB lido em 1,3 ms (gravado em 5,6 ms); SQLite de 228 KB lido em 1,1 ms (gravado em 8,5 ms). O custo real da abertura é ler tags e capas do HD, não o cache. A medição foi feita em uma máquina moderna, não no notebook antigo, e deve ser repetida lá.
2. **O app agora persiste mais coisas** do que na primeira versão do plano: cache da biblioteca, **discos montados** (referências a faixas), a **Caixa** (discos tirados da estante), os **recentes** e **onde parou**. Isso é dado do usuário, mais valioso que um cache que se refaz, e tem relações entre si (um disco montado aponta para faixas).

## Alternativas

| Alternativa | Prós | Contras | Resultado |
| --- | --- | --- | --- |
| A. Tudo em JSON | Simples e legível; fácil de explicar | Várias gravações de arquivo inteiro; é preciso gravar com cuidado (arquivo temporário e renomear) para não corromper em queda de energia; relações feitas à mão | Descartada |
| **B. SQLite para biblioteca e dados do usuário; JSON só para configurações** | Gravação atômica por transação (importante em notebook antigo que pode ser desligado de repente); atualização por linha; relações e consultas (por exemplo ordenar por artista e álbum) em SQL; um arquivo só; `sqlite3` já vem no Python, sem dependência nova | Mais conceitos (SQL) para o autor entender e defender; dois mecanismos (banco e JSON) | **Escolhida** |
| C. Tudo em SQLite, inclusive configurações | Um mecanismo só | Configurações deixam de ser legíveis e editáveis à mão | Descartada |

## Decisão

- Um arquivo SQLite em `GLib.get_user_data_dir()/moa/` guarda: o cache da biblioteca (com data de modificação por arquivo, para reprocessar só o que mudou), os discos montados, a lista da Caixa, os recentes e onde parou.
- As configurações do usuário (tamanho da letra, cores, "Voz mais clara") ficam em **JSON** em `GLib.get_user_config_dir()/moa/`, legíveis e simples.
- O módulo `core/db.py` isola o SQL. O núcleo continua sem importar GTK.
- O banco deve ter **versão de esquema** para permitir migração, e o app deve se recuperar sem alarme de um banco ausente ou corrompido: o cache da biblioteca se refaz varrendo as pastas; discos montados e Caixa são perdidos só em caso de arquivo corrompido, então vale uma cópia de segurança simples.

## Consequências

- **Positivas:** gravação segura em queda de energia; dados do usuário protegidos por transações; consultas simples para a estante (ordem por artista, depois álbum).
- **Negativas e riscos:**
  - O autor sabe TypeScript e não Python; SQL é um conceito a mais. Cada etapa deve explicar o SQL em linguagem simples.
  - Mais código que o JSON. Para 800 faixas isso não se paga em desempenho, e sim em robustez e em dados do usuário.
  - Um banco corrompido não pode mostrar erro técnico ao idoso (restrição 5): recriar o cache e seguir.
- **Mudanças no projeto:** novo `core/db.py`; `core/state.py` passa a usar o banco; o M1 grava o cache da biblioteca nele.

## Validação

- Testes pytest com banco em memória e em arquivo temporário, incluindo reabrir o app, banco ausente e banco corrompido.
- Repetir a medição de leitura no notebook real (M9) para registrar no capítulo de Resultados.
