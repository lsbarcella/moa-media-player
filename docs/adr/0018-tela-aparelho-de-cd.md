# ADR-0018 — Tela "Aparelho de CD": colocar um disco na estante

- **Status:** Aceito. Detalhes técnicos da IA marcados como **provisórios**.
- **Data:** 27/11/2026
- **Decisor:** o autor escolheu a opção **A (aparelho de CD)** no preview `docs/preview/colocar-disco-opcoes.html`; a IA implementou.

## Contexto

O núcleo da cópia (ADR-0017) já existe. Faltava a tela em que o idoso põe um CD sozinho, dentro da metáfora e sem jargão. O preview apresentou cinco opções: A (aparelho de CD), B (painel sobre a estante), C (lugar vazio na prateleira), D (aviso automático) e E (passo a passo).

## Decisão

1. Uma tela própria, **"Aparelho de CD"**, da mesma família do rádio (mesma moldura de madeira e visor). Quem leva até ela é o botão **"Colocar um disco"** na Estante, ao lado de "Criar uma playlist". Com a estante vazia o botão também aparece, porque é por ele que o primeiro disco entra.
2. Quatro momentos, sempre com o estado **em texto no visor**:
   - **Começo:** "ABRA A GAVETA E PONHA O CD", com "Abrir a gaveta" e "Já coloquei o disco".
   - **Copiando:** "COPIANDO: Faixa 3 de 12", barra e "Parar de copiar".
   - **Pronto:** "PRONTO: 12 músicas", com "Ver o disco na estante" e "Abrir a gaveta" (para tirar o CD).
   - **Sem disco / falhou:** frases calmas e "Tentar de novo".
3. **Caminho de volta sempre visível** ("Voltar para a estante"). Sair durante a cópia não a interrompe; enquanto copia, o botão da Estante passa a dizer **"Ver a cópia do disco"**.
4. Estados e textos ficam em `core/aparelho.py` (sem GTK, testável); `ui/cd_view.py` só desenha. A cópia roda numa thread e avisa a tela pela thread principal (`GLib.idle_add`). Durante a cópia só o texto do visor e a barra são atualizados, para não roubar o foco do teclado.
5. Ao terminar, a pasta de música é relida em segundo plano (`Carregador.reler`) e o disco novo ("Disco N") aparece na estante. Fechar o app durante a cópia a cancela e apaga a pasta provisória; sobras de uma cópia interrompida à força são apagadas na próxima.
6. "Abrir a gaveta" usa o `Gio.VolumeMonitor` (sem dependência nova). Se não conseguir, a frase é calma: "Aperte o botão do próprio leitor".

## Alternativas rejeitadas

B (painel), C (lugar vazio), D (aviso automático) e E (passo a passo): ver o preview. A D pode voltar como extra depois, se o XFCE avisar de forma confiável.

## Consequências

- **Não testado com disco real:** a leitura do sumário do CD, a gaveta (`eject` pelo Gio no XFCE), o tempo de cópia num HD mecânico e discos riscados. Precisa ser feito no notebook.
- **Em aberto:** se o idoso pode ouvir música durante a cópia (em HD mecânico pode engasgar) e se a cópia deve impedir a suspensão do notebook (hoje não impede).
- O nome "Disco N" vem do M7; renomear é com "Mexendo no disco" ou, com internet, pelo M6.
