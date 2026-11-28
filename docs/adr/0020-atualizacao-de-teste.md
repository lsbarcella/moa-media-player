# ADR-0020 — Atualização de teste dentro do app (TEMPORÁRIA)

- **Status:** Aceito **por tempo limitado**. Deve ser removido antes da versão final.
- **Data:** 27/11/2026
- **Decisor:** o autor, que priorizou a velocidade de desenvolvimento ("depois a gente remove isso").

## Contexto

Para testar no notebook do usuário, cada correção exigia baixar o zip de novo à mão. O autor quer atualizar o app com base na branch `dev` do GitHub.

## Alternativas (apresentadas ao autor)

A) script `tools/atualizar_teste.sh`; B) A com atalho na Área de Trabalho; C) **atualizador dentro do app**; D) `git pull` agendado. A IA recomendou B. **O autor escolheu C.**

## Decisão

1. `core/atualizacao_de_teste.py` procura o commit mais novo da `dev` (API do GitHub), baixa o zip da `dev`, confere (formato, caminhos, sintaxe de todo o `moa/`), troca a pasta `moa/` e guarda a anterior em `moa.anterior/`. Se algo falhar, nada muda. Há "Voltar à versão anterior".
2. `ui/cartao_de_atualizacao.py` mostra o estado e os botões em **Configurações** (sempre) e na **Estante** (só quando há versão nova, instalando ou pronto). Depois de instalar, "Abrir de novo agora" agenda uma nova abertura e fecha a janela.
3. Ao abrir, se houver internet (`Gio.NetworkMonitor`), procura em segundo plano, **em silêncio** (falha só vai para o log).
4. **Só funciona numa pasta de código-fonte que o usuário pode escrever.** Instalado pelo `.deb` (`/usr/lib/moa`), fica desligado sozinho.
5. Sem dependência nova: `urllib`, `zipfile` e `compileall` da biblioteca padrão.

## Exceções às regras do projeto (por isso é temporário)

- **Offline por padrão (restrição 1):** esta função usa a rede. Só roda se houver conexão e a falha é silenciosa; o app continua 100% funcional offline. Ela só envia uma consulta HTTPS ao GitHub, com o identificador genérico `MoaMediaPlayer/0.1`, sem nenhum dado pessoal (o GitHub vê o IP, como em qualquer acesso).
- **Sem modo escondido / sem jargão para o idoso (restrições 5 e 6):** o cartão usa texto técnico ("versão de teste", "commit") e aparece na Estante. Aceito só no ambiente de testes.
- **Segurança:** o app baixa e **executa código** de um repositório. A proteção é só o HTTPS do GitHub, sem assinatura; quem controlar a `dev` controla o app. Aceito para teste.

## Como remover (checklist)

Procure por `ATUALIZACAO_DE_TESTE` (marcador nos arquivos) e apague:
1. `moa/core/atualizacao_de_teste.py` e `moa/ui/cartao_de_atualizacao.py`;
2. as linhas marcadas em `core/contexto.py`, `ui/window.py`, `ui/settings_view.py`, `ui/shelf_view.py` e `app.py`;
3. `tests/test_atualizacao_de_teste.py` e `tests/test_cartao_de_atualizacao.py`;
4. este ADR passa a "Removido" (com a data).

## Consequências

- O `.deb` ainda leva o código, mas desligado. Remover o módulo antes do M8 final.
- **Não testado:** no notebook do usuário (HD mecânico, versão do Python e do GTK dele) e a abertura de novo depois de instalar por dentro da janela real.
