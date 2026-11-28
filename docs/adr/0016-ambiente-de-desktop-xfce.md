# ADR-0016 — Ambiente de desktop do notebook: Linux Mint XFCE

- **Status:** Aceito. Pontos a conferir no notebook marcados como **não testados**.
- **Data:** 27/11/2026
- **Decisor:** o autor informou o ambiente (Linux Mint XFCE); a IA levantou o que pode mudar.

## Contexto

O projeto foi escrito pensando no Linux Mint com Cinnamon. O notebook do usuário roda o Linux Mint **XFCE**. O app usa GTK 3, GStreamer e `GLib`/`Gio`, que não dependem do ambiente de desktop, mas três pontos conversam com o desktop: a inibição da suspensão, a abertura automática e a aparência.

## Decisão

1. O ambiente-alvo passa a ser **Linux Mint XFCE** (CLAUDE.md e README atualizados). Os requisitos de Python 3.10+ e apt continuam iguais.
2. **Nenhuma mudança de código agora.** Os três pontos abaixo são conferidos no notebook real antes de qualquer ajuste.

| Ponto | Expectativa | Como conferir |
| --- | --- | --- |
| Impedir suspensão (`Gtk.Application.inhibit`) | Pode se comportar diferente no XFCE (`xfce4-session` / `xfce4-power-manager`). Se falhar, o `inibidor.py` só registra no log e a música continua. | Tocar um disco e esperar o tempo de descanso de tela. |
| Abertura automática (`~/.config/autostart/`) | Padrão freedesktop, o XFCE respeita. | Instalar o comando `moa`, abrir, sair da sessão e entrar de novo. |
| Aparência (`style.css`) | Tema GTK do XFCE difere do Cinnamon; botões de 64 px, foco grosso e contraste 7:1 devem ser revistos. | Olhar as telas no monitor real. |

## Alternativas

- **Manter Cinnamon como alvo e tratar o XFCE como "também funciona":** rejeitada, porque o alvo real é o XFCE.
- **Pedir a inibição direto ao `xfce4-power-manager` por D-Bus:** só se o teste mostrar que o `inhibit` do GTK não basta (seria um novo ADR).

## Consequências

- ADRs antigos que citam o Cinnamon (0001, 0006, 0011, 0013) ficam como estão, por serem registros da época. A escala de texto do ADR-0006 e o X da janela do ADR-0011 precisam ser revistos no XFCE.
- **Não testado:** nenhum dos três pontos acima, pois a máquina de desenvolvimento não é XFCE.
