# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tema do Moa: paletas de cor e escalas de letra geradas em Python (KTD8).

Em vez de escrever o CSS à mão, guardamos as cores e os tamanhos como constantes
e geramos o CSS. Assim os testes conseguem conferir o contraste de 7:1 (WCAG AAA)
de cada par de cores e os tamanhos mínimos (letra 20 px, alvo 64 px) sem abrir
janela. As cores vêm do preview aprovado (`docs/preview/moa-preview.html`).

As paletas de daltonismo são uma primeira versão: o contraste foi conferido por
cálculo, mas NÃO com um simulador nem com uma pessoa daltônica (ADR-0006).
"""

from moa.core.covers import contrast_ratio

# --- Cores --------------------------------------------------------------------------

_NORMAL = {
    "bg": "#FAF5E9", "ink": "#1E1913", "ink2": "#4A4036", "card": "#FFFFFF",
    "line": "#CDBFA6", "wood": "#4A2A12", "wood2": "#7A4A21", "green": "#1F4D2B",
    "amber": "#FFD27A", "blue": "#14407A", "warn": "#FFF1B8", "warnb": "#B58B00",
    "visor": "#FFE9A8", "lampon": "#B7E4A8", "focus": "#0B3D91", "danger": "#7A1F1F",
    "selbg": "#EAF5E4", "white": "#FFFFFF", "dark": "#2B2118", "btnradio": "#F6E9D2",
    "hint": "#F3E6CC", "lampoff": "#4A3B2C", "disabled": "#E4DCCB",
}

PALETAS: dict[str, dict[str, str]] = {
    "normal": _NORMAL,
    "vermelho-verde": {**_NORMAL, "green": "#14407A", "lampon": "#A8D4FF", "selbg": "#E3EEFA"},
    "azul-amarelo": {**_NORMAL, "green": "#8A1538", "amber": "#FFC2B0", "lampon": "#FFD0DC",
                     "selbg": "#F9E3EA", "warn": "#FFE3D6", "warnb": "#8A1538"},
    "preto-e-branco": {**_NORMAL, "bg": "#FFFFFF", "green": "#000000", "amber": "#FFFFFF",
                       "lampon": "#FFFFFF", "selbg": "#FFFFFF", "warn": "#FFFFFF",
                       "warnb": "#000000", "visor": "#FFFFFF", "wood": "#000000",
                       "wood2": "#000000", "line": "#000000", "blue": "#000000",
                       "disabled": "#FFFFFF"},
}

# Nome mostrado ao usuário para cada paleta (sem jargão) e as três cores da amostra.
ROTULOS_DAS_PALETAS = {
    "normal": "Cores normais",
    "vermelho-verde": "Dificuldade com vermelho e verde",
    "azul-amarelo": "Dificuldade com azul e amarelo",
    "preto-e-branco": "Preto e branco, bem forte",
}


def amostra(paleta: str) -> tuple[str, str, str]:
    cores = PALETAS[paleta]
    return cores["green"], cores["amber"], cores["lampon"]


# Pares (texto, fundo) que aparecem juntos na tela. Todos precisam de 7:1 ou mais.
PARES_DE_CONTRASTE = [
    ("ink", "bg"), ("ink2", "bg"), ("ink", "card"), ("ink2", "card"),
    ("white", "green"), ("ink", "amber"), ("ink", "visor"), ("ink", "lampon"),
    ("white", "wood"), ("hint", "wood"), ("ink", "warn"), ("ink", "selbg"),
    ("ink2", "selbg"), ("white", "blue"), ("white", "danger"), ("ink", "btnradio"),
    ("white", "dark"), ("ink", "disabled"), ("white", "wood2"),
]

CONTRASTE_MINIMO = 7.0


def contraste(paleta: str, texto: str, fundo: str) -> float:
    cores = PALETAS[paleta]
    return contrast_ratio(cores[texto], cores[fundo])


# --- Escalas de letra -----------------------------------------------------------------

LETRA_BASE_PX = 20           # mínimo da restrição de acessibilidade
ALVO_MINIMO_PX = 64
ESCALAS = {"normal": 1.0, "grande": 1.2, "maior": 1.4}
ROTULOS_DAS_LETRAS = {"normal": "Normal", "grande": "Grande", "maior": "Maior"}


def gerar_css(paleta: str = "normal", letra: str = "normal") -> str:
    """Gera o CSS do GTK para a paleta e a escala escolhidas."""
    c = PALETAS[paleta]
    e = ESCALAS[letra]
    base = round(LETRA_BASE_PX * e)
    titulo = round(30 * e)
    grande = round(26 * e)
    return f"""
* {{ font-size: {base}px; }}
window.moa, .moa-fundo {{ background-color: {c['bg']}; color: {c['ink']}; }}
label {{ color: {c['ink']}; }}
.moa-titulo {{ font-size: {titulo}px; font-weight: 800; }}
.moa-grande {{ font-size: {grande}px; font-weight: 800; }}
.moa-forte {{ font-weight: 800; }}
.moa-nota {{ color: {c['ink2']}; font-weight: 600; }}

.moa-cabecalho {{ background-color: {c['card']}; border-bottom: 3px solid {c['wood2']};
                  padding: 10px 20px; }}
.moa-mini {{ background-color: {c['wood']}; padding: 8px 20px; }}
.moa-mini label {{ color: {c['white']}; }}

/* botões: alvo de 64 px, borda grossa, foco bem visível */
button.moa-btn {{ min-height: {ALVO_MINIMO_PX}px; min-width: {ALVO_MINIMO_PX}px; padding: 10px 20px;
                  font-weight: 800; border: 3px solid {c['ink']}; border-radius: 14px;
                  background-image: none; background-color: {c['card']}; color: {c['ink']};
                  box-shadow: none; text-shadow: none; }}
button.moa-btn label {{ color: inherit; font-weight: 800; }}
button.moa-btn:hover {{ background-color: {c['selbg']}; }}
button.moa-btn:focus {{ outline: 5px solid {c['focus']}; outline-offset: 3px; }}
button.moa-pri {{ background-color: {c['green']}; border-color: {c['green']}; color: {c['white']}; }}
button.moa-pri:hover {{ background-color: {c['green']}; }}
button.moa-pri label {{ color: {c['white']}; }}
button.moa-grande {{ min-height: 76px; padding: 12px 26px; }}
button.moa-btn:disabled, button.moa-btn.moa-inativo {{ background-color: {c['disabled']};
                  color: {c['ink2']}; border-style: dashed; }}
button.moa-btn:disabled label, button.moa-btn.moa-inativo label {{ color: {c['ink2']}; }}
button.moa-perigo {{ border-color: {c['danger']}; }}

/* estante */
.moa-placa {{ background-color: {c['wood']}; border-radius: 8px; padding: 4px 16px; }}
.moa-placa label {{ color: {c['white']}; font-weight: 800; }}
.moa-tabua {{ border-bottom: 16px solid {c['wood2']}; padding-bottom: 14px; }}
button.moa-disco {{ min-height: {ALVO_MINIMO_PX}px; background-image: none; background-color: transparent;
                    border: 3px solid transparent; border-radius: 12px; padding: 6px; box-shadow: none; }}
button.moa-disco:hover {{ background-color: {c['selbg']}; }}
button.moa-disco:focus {{ outline: 5px solid {c['focus']}; outline-offset: 3px; }}
button.moa-disco label {{ color: {c['ink']}; font-weight: 800; }}
.moa-capa {{ border-radius: 6px; box-shadow: 0 3px 0 rgba(0,0,0,.35); }}
.moa-vazio {{ background-color: {c['dark']}; border: 4px dashed {c['ink2']}; border-radius: 6px; }}
.moa-vazio label {{ color: {c['white']}; font-weight: 800; }}
.moa-cartao {{ background-color: {c['card']}; border: 2px solid {c['line']}; border-radius: 14px;
               padding: 14px 18px; }}
.moa-continuar {{ border: 3px solid {c['green']}; }}
.moa-aviso {{ background-color: {c['warn']}; border: 3px solid {c['warnb']}; border-radius: 14px;
              padding: 12px 16px; }}
.moa-aviso label {{ color: {c['ink']}; font-weight: 700; }}
.moa-perigo-caixa {{ background-color: {c['warn']}; border: 4px solid {c['danger']}; border-radius: 14px;
                     padding: 14px 18px; }}

/* rádio */
.moa-radio {{ background-color: {c['wood']}; border: 4px solid {c['dark']}; border-radius: 22px;
              padding: 18px; }}
.moa-radio label {{ color: {c['white']}; }}
.moa-radio .moa-dica {{ color: {c['hint']}; }}
.moa-visor {{ background-color: {c['visor']}; border: 5px solid {c['dark']}; border-radius: 14px; padding: 12px; }}
.moa-visor label {{ color: {c['ink']}; }}
.moa-visor .moa-nota-visor {{ background-color: {c['white']}; border-radius: 6px; padding: 2px 8px;
                              font-weight: 700; }}
.moa-radio button.moa-btn {{ background-color: {c['btnradio']}; border-color: {c['dark']}; color: {c['ink']}; }}
.moa-radio button.moa-btn label {{ color: {c['ink']}; }}
.moa-radio button.moa-tocar {{ background-color: {c['green']}; color: {c['white']}; border-radius: 40px;
                               min-height: 92px; font-size: {grande}px; }}
.moa-radio button.moa-tocar label {{ color: {c['white']}; }}
.moa-radio button.moa-pausar {{ background-color: {c['amber']}; color: {c['ink']}; border-radius: 12px;
                                min-height: 92px; font-size: {grande}px; }}
.moa-radio button.moa-pausar label {{ color: {c['ink']}; }}
.moa-radio button.moa-clara-ligada {{ background-color: {c['lampon']}; }}
.moa-radio button.moa-btn:focus {{ outline: 5px solid {c['white']}; outline-offset: 3px; }}
.moa-volume {{ background-color: {c['dark']}; border-radius: 12px; padding: 10px; }}
.moa-lampada {{ background-color: {c['dark']}; border: 3px solid {c['white']}; border-radius: 11px;
                min-width: 22px; min-height: 22px; }}
.moa-lampada.moa-acesa {{ background-color: {c['lampon']}; box-shadow: 0 0 10px {c['lampon']}; }}
.moa-barra {{ background-color: {c['lampoff']}; border: 2px solid {c['white']}; border-radius: 4px;
              min-width: 14px; min-height: 34px; }}
.moa-barra.moa-acesa {{ background-color: {c['lampon']}; box-shadow: 0 0 6px {c['lampon']}; }}

/* lista de músicas */
.moa-linha {{ background-color: {c['card']}; border: 2px solid {c['line']}; border-radius: 12px; padding: 6px; }}
.moa-linha.moa-agora {{ border: 4px solid {c['green']}; background-color: {c['selbg']}; }}
button.moa-faixa {{ min-height: {ALVO_MINIMO_PX}px; background-image: none; background-color: transparent;
                    border: none; box-shadow: none; padding: 4px 8px; }}
button.moa-faixa:hover {{ background-color: {c['selbg']}; }}
button.moa-faixa:focus {{ outline: 5px solid {c['focus']}; outline-offset: 3px; }}
button.moa-faixa label {{ color: {c['ink']}; }}

/* escolhas (configurações, capas) */
button.moa-opcao {{ min-height: {ALVO_MINIMO_PX}px; padding: 8px 16px; font-weight: 800;
                    background-image: none; background-color: {c['card']}; color: {c['ink']};
                    border: 3px solid {c['ink']}; border-radius: 14px; box-shadow: none; }}
button.moa-opcao label {{ color: {c['ink']}; font-weight: 800; }}
button.moa-opcao:focus {{ outline: 5px solid {c['focus']}; outline-offset: 3px; }}
button.moa-opcao.moa-escolhida {{ border: 5px solid {c['green']}; background-color: {c['selbg']}; }}
.moa-amostra {{ border: 2px solid {c['ink']}; border-radius: 6px; min-width: 26px; min-height: 26px; }}
.moa-exemplo {{ background-color: {c['card']}; border: 2px solid {c['line']}; border-radius: 10px;
                padding: 10px 14px; font-weight: 700; }}
entry {{ min-height: {ALVO_MINIMO_PX}px; padding: 8px 14px; border: 3px solid {c['ink']};
         border-radius: 12px; background-color: {c['card']}; color: {c['ink']}; }}
entry:focus {{ outline: 5px solid {c['focus']}; outline-offset: 3px; }}
"""


_provedor = None


def aplicar(paleta: str, letra: str) -> None:
    """Carrega o CSS na tela inteira do app (troca o anterior, se houver)."""
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, Gtk

    global _provedor
    tela = Gdk.Screen.get_default()
    if tela is None:
        return
    if _provedor is not None:
        Gtk.StyleContext.remove_provider_for_screen(tela, _provedor)
    _provedor = Gtk.CssProvider()
    _provedor.load_from_data(gerar_css(paleta, letra).encode("utf-8"))
    Gtk.StyleContext.add_provider_for_screen(tela, _provedor, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
