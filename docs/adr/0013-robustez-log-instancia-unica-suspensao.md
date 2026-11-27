# ADR-0013 — Robustez: log, falhas calmas, instância única, suspensão e abertura automática

- **Status:** Aceito. Detalhes técnicos da IA marcados como **provisórios**.
- **Data:** 27/11/2026
- **Decisor:** o autor definiu as regras (CLAUDE.md, seções 5 e 9); a IA escolheu a forma de implementar.
- **Nota de numeração:** o plano reservava o 0013 para o MusicBrainz; esse ADR passa a ser o próximo número livre quando o M6 for feito.

## Contexto

O idoso não pode ver mensagem técnica, não pode perder a música porque o notebook dormiu, e abrir o app duas vezes não pode criar duas janelas. O autor precisa de um arquivo de log para entender problemas fora do app.

## Decisão

1. **Log em arquivo** (`core/logsetup.py`): `~/.local/share/moa/moa.log`, com rotação (512 KB por arquivo, 3 cópias antigas, no máximo cerca de 2 MB). Se a pasta não puder ser escrita, o app segue sem log.
2. **Falha inesperada:** `sys.excepthook` e `threading.excepthook` registram a exceção no log e a sessão mostra a frase calma "Algo não saiu como eu esperava. Pode tentar de novo." numa faixa abaixo do cabeçalho, em qualquer tela. Como todo aviso, ela fica até a próxima ação do usuário. O aviso passa pela thread principal (`GLib.idle_add`).
3. **Instância única:** já vem do `Gtk.Application` com `application_id` (D-Bus). Um teste sobe um barramento próprio e confere que o segundo processo termina com código 0 e o primeiro continua vivo.
4. **Suspensão:** `ui/inibidor.py` chama `Application.inhibit` (SUSPEND e IDLE) quando começa a tocar e `uninhibit` ao pausar, parar ou fechar. Falha ao pedir só vai para o log.
5. **Fechar pelo X:** já salvava a posição (`Contexto.encerrar`); agora também devolve o pedido de suspensão. Há teste de fechar e reabrir mostrando "Continuar a ouvir".
6. **Abertura automática** (`core/autostart.py`): na primeira execução cria `~/.config/autostart/br.tcc.Moa.desktop` e um marcador em `~/.local/share/moa/`. Se o usuário apagar o atalho, o app **não o recria**. **Só cria quando o comando `moa` está instalado** (o `.deb` do M8 o instala); rodando do código-fonte, não cria nada, para o ambiente de desenvolvimento não ganhar um autostart sem querer.

## Alternativas rejeitadas

- Um diálogo de erro amigável: contraria a regra de nenhuma janela modal inesperada.
- Criar o autostart também em `python3 -m moa`: o `Exec` dependeria da pasta atual e quebraria no login.
- Colocar o autostart só no `.deb` (`/etc/xdg/autostart`): o usuário não conseguiria desligar apagando um arquivo da própria pasta. Pode ser somado depois, se o autor preferir.

## Consequências

- O atalho de abertura automática só passa a existir depois do M8; até lá, não há como testá-lo de ponta a ponta.
- **Não testado:** suspensão real (precisa de um notebook que durma), abertura automática no login do Cinnamon.
