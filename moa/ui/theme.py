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

from typing import NamedTuple

from moa.core.covers import contrast_ratio

# --- Cores --------------------------------------------------------------------------

_NORMAL = {
    "bg": "#FAF5E9", "ink": "#1E1913", "ink2": "#4A4036", "card": "#FFFFFF",
    "line": "#CDBFA6", "wood": "#4A2A12", "wood2": "#7A4A21", "green": "#1F4D2B",
    "amber": "#FFD27A", "blue": "#14407A", "warn": "#FFF1B8", "warnb": "#B58B00",
    "visor": "#FFE9A8", "lampon": "#B7E4A8", "focus": "#0B3D91", "danger": "#7A1F1F",
    "selbg": "#EAF5E4", "white": "#FFFFFF", "dark": "#2B2118", "btnradio": "#F6E9D2",
    "hint": "#F3E6CC", "lampoff": "#4A3B2C", "disabled": "#E4DCCB",
    # Materiais do nível 3 (ADR-0024). "_hi" é o trecho mais claro do degradê, "_lo" o mais escuro.
    "wood_hi": "#5E3518", "wood_lo": "#3D220F",                    # madeira do gabinete e da estante
    "brass_hi": "#E8CF8A", "brass": "#D6B25C", "brass_lo": "#9C7A2A",   # latão: o escuro só em moldura sem texto
    "metal_hi": "#EDEAE2", "metal_lo": "#B9B3A6",                  # metal escovado
    "key_hi": "#FFFFFF", "key_lo": "#E4D4AE",                      # face da tecla
    "visor_hi": "#FFF1C8", "visor_lo": "#F2CF76",                  # vidro do visor
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
                       "disabled": "#FFFFFF",
                       # no preto e branco os materiais são só preto ou branco (relevo por contorno)
                       "wood_hi": "#000000", "wood_lo": "#000000",
                       "brass_hi": "#FFFFFF", "brass": "#FFFFFF", "brass_lo": "#000000",
                       "metal_hi": "#FFFFFF", "metal_lo": "#FFFFFF",
                       "key_hi": "#FFFFFF", "key_lo": "#FFFFFF",
                       "visor_hi": "#FFFFFF", "visor_lo": "#FFFFFF"},
}

# Nome mostrado ao usuário para cada paleta (sem jargão) e as três cores da amostra.
ROTULOS_DAS_PALETAS = {
    "normal": "Cores padrão",
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


# --- Materiais e contraste no pior ponto (ADR-0024) -------------------------------------
# Um degradê não tem UMA cor de fundo: o texto precisa de 7:1 em todos os pontos dele. Cada
# `Material` diz qual texto fica sobre quais trechos do degradê e que camadas translúcidas (brilho,
# veio) cobrem a zona do texto. Esta tabela é a ÚNICA fonte das opacidades: o gerador de CSS usa os
# mesmos números que o teste confere (KTD8).

ALFA_BRILHO_DA_TECLA = 0.30     # brilho branco, só na faixa de cima da tecla (nunca atrás da letra)
ALFA_REALCE_DA_TECLA = 0.90     # fio claro no topo da tecla
ALFA_SOMBRA_DA_TECLA = 0.18     # sombreado no pé da tecla
ALFA_TECLA_TRAVADA = 0.14       # a tecla baixada fica um pouco mais escura
ALFA_VEIO_CLARO = 0.03          # veios claros da madeira (máx. 10%, KTD2)
ALFA_VEIO_ESCURO = 0.10         # veios escuros da madeira


class Material(NamedTuple):
    """Um texto sobre um degradê. É como uma `interface` de TypeScript: só descreve os dados."""
    nome: str
    texto: str                              # token do texto
    fundos: tuple[str, ...]                 # tokens dos trechos do degradê sob o texto
    camadas: tuple[tuple[str, float], ...]  # (cor ou token, opacidade) que cobrem a zona do texto


MATERIAIS = [
    Material("madeira do gabinete com rótulo branco", "white", ("wood_hi", "wood_lo"),
             (("white", ALFA_VEIO_CLARO),)),
    Material("latão claro da plaquinha com texto", "ink", ("brass_hi", "brass"), ()),
    Material("vidro do visor com texto", "ink", ("visor_hi", "visor_lo"), ()),
    Material("face da tecla com texto", "ink", ("key_hi", "key_lo"), (("black", ALFA_SOMBRA_DA_TECLA),)),
    Material("tecla travada com texto", "ink", ("key_hi", "key_lo"), (("black", ALFA_TECLA_TRAVADA),)),
    Material("tecla verde Tocar (letra abaixo do brilho)", "white", ("green",),
             (("black", ALFA_SOMBRA_DA_TECLA),)),
    Material("tecla âmbar Pausar com texto", "ink", ("amber",), (("black", ALFA_SOMBRA_DA_TECLA),)),
    Material("tecla escolhida com texto", "white", ("blue",), (("black", ALFA_SOMBRA_DA_TECLA),)),
]


def misturar(base: str, topo: str, alfa: float) -> str:
    """A cor `base` com uma camada translúcida `topo` por cima (como um `rgba` do CSS)."""
    b, t = base.lstrip("#"), topo.lstrip("#")
    canais = []
    for i in (0, 2, 4):
        mistura = int(b[i:i + 2], 16) * (1 - alfa) + int(t[i:i + 2], 16) * alfa
        canais.append(f"{round(mistura):02X}")
    return "#" + "".join(canais)


_FIXAS = {"black": "#000000"}      # "white" já é um token de cada paleta


def _cor(paleta: str, nome_ou_hex: str) -> str:
    """Resolve um token da paleta, uma cor fixa (`black`) ou um `#RRGGBB` direto."""
    if nome_ou_hex.startswith("#"):
        return nome_ou_hex
    if nome_ou_hex in PALETAS[paleta]:
        return PALETAS[paleta][nome_ou_hex]
    return _FIXAS[nome_ou_hex]


def contraste_no_pior_ponto(paleta: str, material: Material) -> float:
    """O menor contraste do texto do `material` sobre qualquer trecho do degradê."""
    texto = _cor(paleta, material.texto)
    piores = []
    for fundo in material.fundos:
        cor = _cor(paleta, fundo)
        for camada, alfa in material.camadas:
            cor = misturar(cor, _cor(paleta, camada), alfa)
        piores.append(contrast_ratio(texto, cor))
    return min(piores)


# No preto e branco o relevo é contorno duplo e sombra, sem tons (KTD3).
RELEVO_POR_PALETA = {"preto-e-branco": "contorno"}


def relevo(paleta: str) -> str:
    return RELEVO_POR_PALETA.get(paleta, "tons")


# --- Teclas com curso (KTD5): sem `transform` no GTK 3, a tecla "desce" trocando borda por espaço ---

BORDA_PX = 3
ALTURA_DA_TECLA_PX = 6          # a "altura": borda de baixo extra, que faz o papel de sombra rígida
PADDING_TOPO_PX = 8             # espaço entre o topo da tecla e o rótulo
FAIXA_DO_BRILHO_PX = 8          # o brilho termina aqui, acima do rótulo (<= PADDING_TOPO_PX)


def _rgba(hexa: str, alfa: float) -> str:
    h = hexa.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alfa})"


def _css_do_aparelho(c: dict[str, str], grande: int, modo: str) -> str:
    """Gabinete de madeira, visor de vidro, moldura de metal, grade do alto-falante e plaquinha."""
    if modo == "contorno":      # preto e branco: contorno duplo, sem veios nem degradê (KTD3)
        return f"""
.moa-radio {{ background-color: {c['wood']}; background-image: none; border: 4px solid {c['white']};
              border-radius: 22px; padding: 18px;
              box-shadow: 0 0 0 3px {c['dark']}, inset 0 0 0 3px {c['dark']}, 0 6px 0 {c['dark']}; }}
.moa-radio label {{ color: {c['white']}; }}
.moa-radio .moa-dica {{ color: {c['hint']}; }}
.moa-visor {{ background-color: {c['visor']}; background-image: none; border: 5px solid {c['dark']};
              border-radius: 14px; padding: 12px; box-shadow: inset 0 0 0 3px {c['white']}; }}
.moa-visor label {{ color: {c['ink']}; }}
.moa-metal {{ background-color: {c['white']}; border: 3px solid {c['dark']}; border-radius: 16px;
              padding: 8px; box-shadow: inset 0 0 0 2px {c['white']}, inset 0 0 0 4px {c['dark']}; }}
.moa-grade {{ background-color: {c['dark']}; background-image: none; border: 3px solid {c['white']};
              border-radius: 10px; min-height: 28px; }}
.moa-plaquinha {{ background-color: {c['white']}; border: 3px solid {c['dark']}; border-radius: 8px;
                  padding: 0px 14px; }}
.moa-plaquinha label {{ color: {c['ink']}; font-weight: 800; letter-spacing: 4px; }}
"""
    veio_escuro = _rgba("#000000", ALFA_VEIO_ESCURO)
    veio_claro = _rgba("#FFFFFF", ALFA_VEIO_CLARO)
    return f"""
.moa-radio {{ background-color: {c['wood']};
    background-image: repeating-linear-gradient(to bottom, {veio_escuro} 0px, {veio_escuro} 1px,
                          {_rgba('#000000', 0)} 2px, {veio_claro} 5px, {_rgba('#FFFFFF', 0)} 7px,
                          {_rgba('#000000', 0)} 11px),
                      linear-gradient(to bottom, {_rgba(c['wood_hi'], 1)} 0%, {_rgba(c['wood_lo'], 1)} 100%);
    border: 5px solid {c['brass']}; border-radius: 22px; padding: 22px;
    box-shadow: inset 0 0 0 2px {c['brass_lo']}, inset 0 0 18px rgba(0,0,0,0.45),
                0 0 0 2px {c['dark']}, 0 6px 0 rgba(0,0,0,0.45); }}
.moa-radio label {{ color: {c['white']}; }}
.moa-radio .moa-dica {{ color: {c['hint']}; }}
.moa-visor {{ background-color: {c['visor']};
    background-image: linear-gradient(to bottom, {_rgba(c['visor_hi'], 1)} 0%, {_rgba(c['visor_lo'], 1)} 100%);
    border: 5px solid {c['brass']}; border-radius: 14px; padding: 12px;
    box-shadow: 0 0 0 2px {c['brass_lo']}, inset 0 0 14px rgba(0,0,0,0.30),
                inset 0 2px 0 rgba(255,255,255,0.70), inset 2px 0 0 rgba(255,255,255,0.35); }}
.moa-visor label {{ color: {c['ink']}; }}
.moa-metal {{ background-color: {c['metal_lo']};
    background-image: repeating-linear-gradient(to right, rgba(255,255,255,0.22) 0px, rgba(255,255,255,0.22) 1px,
                          rgba(255,255,255,0) 2px, rgba(0,0,0,0.06) 3px, rgba(0,0,0,0) 4px),
                      linear-gradient(to bottom, {_rgba(c['metal_hi'], 1)} 0%, {_rgba(c['metal_lo'], 1)} 100%);
    border: 3px solid {c['dark']}; border-radius: 16px; padding: 8px;
    box-shadow: inset 0 2px 0 rgba(255,255,255,0.8), inset 0 -3px 0 rgba(0,0,0,0.25); }}
.moa-grade {{ background-color: {c['dark']};
    background-image: repeating-linear-gradient(to right, rgba(255,255,255,0.14) 0px, rgba(255,255,255,0.14) 2px,
                          rgba(0,0,0,0) 3px, rgba(0,0,0,0) 6px),
                      repeating-linear-gradient(to bottom, rgba(255,255,255,0.10) 0px, rgba(255,255,255,0.10) 2px,
                          rgba(0,0,0,0) 3px, rgba(0,0,0,0) 6px);
    border: 3px solid {c['brass_lo']}; border-radius: 10px; min-height: 28px;
    box-shadow: inset 0 3px 8px rgba(0,0,0,0.6); }}
.moa-plaquinha {{ background-color: {c['brass']};
    background-image: linear-gradient(to bottom, {_rgba(c['brass_hi'], 1)} 0%, {_rgba(c['brass'], 1)} 100%);
    border: 2px solid {c['brass_lo']}; border-radius: 8px; padding: 0px 14px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.7); }}
.moa-plaquinha label {{ color: {c['ink']}; font-weight: 800; letter-spacing: 4px; }}
"""


def _css_das_teclas(c: dict[str, str], grande: int, modo: str) -> str:
    """CSS das teclas (botões de ação, escolhas e marcações), das lâmpadas e das variantes."""
    b, h, p = BORDA_PX, ALTURA_DA_TECLA_PX, PADDING_TOPO_PX
    pe = ALVO_MINIMO_PX
    repouso = (f"border: {b}px solid {c['dark']}; border-bottom-width: {b + h}px; "
               f"border-radius: 14px; padding: {p}px 20px {p}px 20px;")
    apertada = f"border-bottom-width: {b + 1}px; padding-top: {p + h - 1}px;"
    teclas = "button.moa-btn, button.moa-opcao, button.moa-marca"
    apertadas = ("button.moa-btn:active, button.moa-btn.moa-travada, "
                 "button.moa-opcao.moa-escolhida, button.moa-marca.moa-marcada")
    faixa = FAIXA_DO_BRILHO_PX
    if modo == "contorno":      # preto e branco: contorno duplo e sombra, sem tons (KTD3)
        face = (f"background-color: {c['key_lo']}; background-image: none; "
                f"box-shadow: inset 0 0 0 2px {c['white']}, inset 0 0 0 4px {c['dark']};")
        face_apertada = (f"background-image: none; "
                         f"box-shadow: inset 0 0 0 2px {c['white']}, inset 0 0 0 6px {c['dark']};")
        brilho_colorido = "background-image: none;"
    else:
        face = (f"background-color: {c['key_lo']}; "
                f"background-image: linear-gradient(to bottom, rgba(255,255,255,{ALFA_REALCE_DA_TECLA}) 0px, "
                f"rgba(255,255,255,0) 60%), "
                f"linear-gradient(to bottom, rgba(0,0,0,0) 45%, rgba(0,0,0,{ALFA_SOMBRA_DA_TECLA}) 100%); "
                f"box-shadow: inset 0 2px 0 rgba(255,255,255,{ALFA_REALCE_DA_TECLA});")
        face_apertada = (f"background-image: linear-gradient(to bottom, rgba(0,0,0,{ALFA_TECLA_TRAVADA}) 0px, "
                         f"rgba(0,0,0,0.02) 60%); box-shadow: inset 0 3px 0 rgba(0,0,0,0.28);")
        # tecla colorida: brilho só numa faixa fina no topo (acima da letra) e sombreado no pé (KTD2)
        brilho_colorido = (f"background-image: linear-gradient(to bottom, rgba(255,255,255,{ALFA_BRILHO_DA_TECLA}) 0px, "
                           f"rgba(255,255,255,{ALFA_BRILHO_DA_TECLA}) {faixa - 2}px, rgba(255,255,255,0) {faixa}px), "
                           f"linear-gradient(to bottom, rgba(0,0,0,0) 45%, rgba(0,0,0,{ALFA_SOMBRA_DA_TECLA}) 100%);")
    return f"""
/* teclas: alvo de 64 px, relevo com curso (ADR-0024), foco bem visível */
{teclas} {{ min-height: {pe}px; min-width: {pe}px; font-weight: 800; color: {c['ink']};
    {repouso}
    {face}
    text-shadow: none; }}
button.moa-btn label {{ color: inherit; font-weight: 800; }}
button.moa-btn:hover {{ background-color: {c['selbg']}; }}
{teclas.replace(', ', ':focus, ')}:focus {{ outline: 5px solid {c['focus']}; outline-offset: 3px; }}
{apertadas} {{ {apertada}
    {face_apertada} }}
button.moa-pri {{ background-color: {c['green']}; color: {c['white']}; {brilho_colorido} }}
button.moa-pri:hover {{ background-color: {c['green']}; }}
button.moa-pri label {{ color: {c['white']}; }}
button.moa-grande {{ min-height: 76px; padding-left: 26px; padding-right: 26px; }}
button.moa-btn:disabled, button.moa-btn.moa-inativo {{ background-color: {c['disabled']};
                  color: {c['ink2']}; border-style: dashed dashed solid dashed; }}
button.moa-btn:disabled label, button.moa-btn.moa-inativo label {{ color: {c['ink2']}; }}
button.moa-perigo {{ border-color: {c['danger']}; }}
button.moa-opcao {{ padding-left: 16px; padding-right: 16px; }}
button.moa-opcao label {{ color: {c['ink']}; font-weight: 800; }}
button.moa-opcao:hover, button.moa-marca:hover {{ background-color: {c['selbg']}; }}
button.moa-opcao.moa-escolhida {{ border-color: {c['green']}; background-color: {c['selbg']}; }}
button.moa-marca {{ padding-left: 12px; padding-right: 12px; }}
button.moa-marca label {{ color: {c['ink']}; }}
button.moa-marca.moa-marcada {{ border-color: {c['green']}; background-color: {c['selbg']}; }}
button.moa-btn.moa-escolhida {{ background-color: {c['blue']}; color: {c['white']}; {brilho_colorido} }}
button.moa-btn.moa-escolhida label {{ color: {c['white']}; }}

/* lâmpadas-piloto com lente: brilho no canto, aro e halo quando acesas */
.moa-lampada, .moa-luz {{ background-color: {c['lampoff']}; border: 3px solid {c['metal_lo']}; border-radius: 50px;
    box-shadow: 0 0 0 2px {c['dark']}, inset 0 -2px 0 rgba(0,0,0,0.35);
    background-image: radial-gradient(circle at 35% 30%, rgba(255,255,255,0.55) 0px, rgba(255,255,255,0) 40%); }}
.moa-lampada {{ min-width: 22px; min-height: 22px; }}
.moa-luz {{ min-width: 16px; min-height: 16px; }}
.moa-lampada.moa-acesa, .moa-luz.moa-acesa {{ background-color: {c['lampon']};
    box-shadow: 0 0 0 2px {c['dark']}, 0 0 12px {c['lampon']};
    background-image: radial-gradient(circle at 35% 30%, rgba(255,255,255,0.85) 0px, rgba(255,255,255,0) 45%); }}
"""


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
    modo = relevo(paleta)
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

{_css_das_teclas(c, grande, modo)}

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
{_css_do_aparelho(c, grande, modo)}
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
.moa-barra trough {{ min-height: 26px; background-color: {c['white']}; border: 3px solid {c['dark']};
                     border-radius: 13px; }}
.moa-barra progress {{ min-height: 26px; background-color: {c['green']}; background-image: none;
                       border-radius: 10px; }}
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

/* playlist: caixas de marcar */
.moa-caixinha {{ background-color: {c['card']}; border: 4px solid {c['ink']}; border-radius: 8px;
                 min-width: 40px; min-height: 40px; }}
button.moa-marcada .moa-caixinha {{ background-color: {c['green']}; border-color: {c['green']}; }}
button.moa-marcada .moa-caixinha label {{ color: {c['white']}; }}

/* painel do "+" */
.moa-veu {{ background-color: rgba(30, 25, 19, 0.6); padding: 20px; }}
.moa-painel {{ background-color: {c['card']}; border: 4px solid {c['ink']}; border-radius: 16px; padding: 20px; }}
.moa-novo {{ background-color: {c['card']}; border: 4px dashed {c['ink']}; border-radius: 6px; }}
.moa-mais-grande {{ font-size: {round(48 * e)}px; font-weight: 800; }}

/* escolhas (configurações, capas) */
.moa-amostra {{ border: 2px solid {c['ink']}; border-radius: 6px; min-width: 26px; min-height: 26px; }}
.moa-exemplo {{ background-color: {c['card']}; border: 2px solid {c['line']}; border-radius: 10px;
                padding: 10px 14px; font-weight: 700; }}
entry {{ min-height: {ALVO_MINIMO_PX}px; padding: 8px 14px; border: 3px solid {c['ink']};
         border-radius: 12px; background-color: {c['card']}; color: {c['ink']}; }}
entry:focus {{ outline: 5px solid {c['focus']}; outline-offset: 3px; }}
"""


_provedor = None


_paleta_atual = "normal"


def definir_paleta_atual(paleta: str) -> None:
    """Guarda a paleta em uso para as peças em Cairo, que a leem na hora de desenhar (KTD12)."""
    global _paleta_atual
    _paleta_atual = paleta if paleta in PALETAS else "normal"


def paleta_atual() -> str:
    return _paleta_atual


def aplicar(paleta: str, letra: str) -> None:
    """Carrega o CSS na tela inteira do app (troca o anterior, se houver)."""
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, Gtk

    global _provedor
    definir_paleta_atual(paleta)
    tela = Gdk.Screen.get_default()
    if tela is None:
        return
    if _provedor is not None:
        Gtk.StyleContext.remove_provider_for_screen(tela, _provedor)
    _provedor = Gtk.CssProvider()
    _provedor.load_from_data(gerar_css(paleta, letra).encode("utf-8"))
    Gtk.StyleContext.add_provider_for_screen(tela, _provedor, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
