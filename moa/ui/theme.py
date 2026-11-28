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
    "bg": "#F2F2EF", "ink": "#16181A", "ink2": "#3C4146", "card": "#FFFFFF",
    "line": "#B9BBBD", "case": "#26282B", "case2": "#4A4D52", "green": "#1F4D2B",
    "amber": "#FFD27A", "blue": "#14407A", "warn": "#FFF1B8", "warnb": "#B58B00",
    "visor": "#1F2327", "visor_texto": "#FFFFFF", "lampon": "#B7E4A8", "focus": "#0B3D91", "danger": "#7A1F1F",
    "selbg": "#EAF5E4", "white": "#FFFFFF", "dark": "#1E2023", "btnradio": "#C6C6C2",
    "hint": "#E6E7E8", "lampoff": "#4A4F54", "disabled": "#DCDCD8",
    # Tema hi-fi (ADR-0025): teclas de metal cinza com bisel em bandejas pretas, gabinete grafite
    # com friso prateado. "_hi" é o trecho mais claro do degradê, "_lo" o mais escuro.
    "case_hi": "#3A3D41", "case_lo": "#1E2023",                          # gabinete e fundo da estante
    "plate_hi": "#E6E7E9", "plate": "#C9CBCE", "plate_lo": "#7B7E82",    # prata: friso, plaquinhas, parafusos
    "metal_hi": "#EDEDEA", "metal_lo": "#B4B4B0",                        # metal escovado
    "key_hi": "#F0F0ED", "key_lo": "#C6C6C2", "key_edge": "#F8F8F6",     # tecla solta: face e bisel claro
    "keyon_hi": "#565652", "keyon": "#4C4C48", "keyon_lo": "#3F3F3B",    # tecla afundada
    "tray": "#0F1011", "tray_edge": "#5A5D62",                           # bandeja preta que segura as teclas
    "visor_hi": "#2B3136", "visor_lo": "#171A1D",                        # vidro do visor: escuro e neutro, letra branca
}

PALETAS: dict[str, dict[str, str]] = {
    "normal": _NORMAL,
    "vermelho-verde": {**_NORMAL, "green": "#14407A", "lampon": "#A8D4FF", "selbg": "#E3EEFA"},
    "azul-amarelo": {**_NORMAL, "green": "#8A1538", "amber": "#FFC2B0", "lampon": "#FFD0DC",
                     "selbg": "#F9E3EA", "warn": "#FFE3D6", "warnb": "#8A1538"},
    "preto-e-branco": {**_NORMAL, "bg": "#FFFFFF", "green": "#000000", "amber": "#FFFFFF",
                       "lampon": "#FFFFFF", "selbg": "#FFFFFF", "warn": "#FFFFFF",
                       "warnb": "#000000", "visor": "#FFFFFF", "visor_texto": "#16181A", "case": "#000000",
                       "case2": "#000000", "line": "#000000", "blue": "#000000",
                       "disabled": "#FFFFFF", "btnradio": "#FFFFFF", "card": "#FFFFFF",
                       # no preto e branco os materiais são só preto ou branco (relevo por contorno)
                       "case_hi": "#000000", "case_lo": "#000000",
                       "plate_hi": "#FFFFFF", "plate": "#FFFFFF", "plate_lo": "#000000",
                       "metal_hi": "#FFFFFF", "metal_lo": "#FFFFFF",
                       "key_hi": "#FFFFFF", "key_lo": "#FFFFFF", "key_edge": "#FFFFFF",
                       "keyon_hi": "#000000", "keyon": "#000000", "keyon_lo": "#000000",
                       "tray": "#000000", "tray_edge": "#FFFFFF",
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
    ("white", "green"), ("ink", "amber"), ("visor_texto", "visor"), ("ink", "lampon"),
    ("white", "case"), ("hint", "case"), ("ink", "warn"), ("ink", "selbg"),
    ("ink2", "selbg"), ("white", "blue"), ("white", "danger"), ("ink", "btnradio"),
    ("white", "dark"), ("ink", "disabled"), ("white", "case2"),
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
ALFA_SOMBRA_DA_TECLA = 0.12     # sombreado no pé da tecla
ALFA_REALCE_NA_ESTANTE = 0.12   # realce de um disco sob o mouse, sobre o fundo escuro da estante
ALFA_ESCOVADO = 0.035           # estrias do metal escovado do gabinete (máx. 10%)


class Material(NamedTuple):
    """Um texto sobre um degradê. É como uma `interface` de TypeScript: só descreve os dados."""
    nome: str
    texto: str                              # token do texto
    fundos: tuple[str, ...]                 # tokens dos trechos do degradê sob o texto
    camadas: tuple[tuple[str, float], ...]  # (cor ou token, opacidade) que cobrem a zona do texto


MATERIAIS = [
    Material("gabinete grafite com rótulo branco", "white", ("case_hi", "case_lo"),
             (("white", ALFA_ESCOVADO),)),
    Material("prata da plaquinha com texto", "ink", ("plate_hi", "plate"), ()),
    Material("vidro do visor com texto", "visor_texto", ("visor_hi", "visor_lo"), ()),
    Material("tecla solta com texto", "ink", ("key_hi", "key_lo"), (("black", ALFA_SOMBRA_DA_TECLA),)),
    Material("tecla afundada com texto", "white", ("keyon_hi", "keyon", "keyon_lo"), ()),
    Material("tecla verde Tocar (letra abaixo do brilho)", "white", ("green",),
             (("black", ALFA_SOMBRA_DA_TECLA),)),
    Material("tecla âmbar com texto", "ink", ("amber",), (("black", ALFA_SOMBRA_DA_TECLA),)),
    Material("tecla escolhida com texto", "white", ("blue",), (("black", ALFA_SOMBRA_DA_TECLA),)),
    Material("rótulo branco no fundo da estante (com o realce do mouse)", "white", ("case_hi", "case_lo"),
             (("white", ALFA_REALCE_NA_ESTANTE),)),
    Material("cabeçalho de metal com título", "ink", ("metal_hi", "metal_lo"), ()),
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


def _css_do_aparelho(c: dict[str, str], modo: str) -> str:
    """Gabinete grafite, visor de vidro, bandeja preta das teclas, grade do alto-falante e plaquinha."""
    if modo == "contorno":      # preto e branco: contorno duplo, sem estrias nem degradê (KTD3)
        return f"""
.moa-radio {{ background-color: {c['case']}; background-image: none; border: 4px solid {c['white']};
              border-radius: 18px; padding: 18px;
              box-shadow: 0 0 0 3px {c['dark']}, inset 0 0 0 3px {c['dark']}, 0 6px 0 {c['dark']}; }}
.moa-radio label {{ color: {c['white']}; }}
.moa-radio .moa-dica {{ color: {c['hint']}; }}
.moa-visor {{ background-color: {c['visor']}; background-image: none; border: 5px solid {c['dark']};
              border-radius: 12px; padding: 12px; box-shadow: inset 0 0 0 3px {c['white']}; }}
.moa-visor label {{ color: {c['visor_texto']}; }}
.moa-bandeja, .moa-volume {{ background-color: {c['tray']}; border: 3px solid {c['tray_edge']}; border-radius: 14px;
              padding: 8px; box-shadow: inset 0 0 0 2px {c['tray']}; }}
.moa-grade {{ background-color: {c['dark']}; background-image: none; border: 3px solid {c['white']};
              border-radius: 10px; min-height: 28px; }}
.moa-plaquinha {{ background-color: {c['white']}; border: 3px solid {c['dark']}; border-radius: 8px;
                  padding: 0px 14px; }}
.moa-plaquinha label {{ color: {c['ink']}; font-weight: 800; letter-spacing: 4px; }}
"""
    estria = _rgba("#FFFFFF", ALFA_ESCOVADO)
    sem_estria = _rgba("#FFFFFF", 0)
    return f"""
.moa-radio {{ background-color: {c['case']};
    background-image: repeating-linear-gradient(to right, {estria} 0px, {estria} 1px,
                          {sem_estria} 2px, {sem_estria} 4px),
                      linear-gradient(to bottom, {_rgba(c['case_hi'], 1)} 0%, {_rgba(c['case_lo'], 1)} 100%);
    border: 4px solid {c['plate_lo']}; border-radius: 18px; padding: 22px;
    box-shadow: inset 0 2px 0 rgba(255,255,255,0.18), inset 0 0 0 2px {c['dark']},
                0 0 0 2px {c['dark']}, 0 6px 0 rgba(0,0,0,0.45); }}
.moa-radio label {{ color: {c['white']}; }}
.moa-radio .moa-dica {{ color: {c['hint']}; }}
.moa-visor {{ background-color: {c['visor']};
    background-image: linear-gradient(to bottom, {_rgba(c['visor_hi'], 1)} 0%, {_rgba(c['visor_lo'], 1)} 100%);
    border: 4px solid {c['dark']}; border-radius: 12px; padding: 12px;
    box-shadow: 0 0 0 2px {c['plate_lo']}, inset 0 0 14px rgba(0,0,0,0.30),
                inset 0 2px 0 rgba(255,255,255,0.22), inset 2px 0 0 rgba(255,255,255,0.10); }}
.moa-visor label {{ color: {c['visor_texto']}; }}
.moa-bandeja, .moa-volume {{ background-color: {c['tray']}; border: 2px solid {c['tray_edge']}; border-radius: 14px;
    padding: 7px; box-shadow: inset 0 2px 5px rgba(0,0,0,0.9), 0 1px 0 rgba(255,255,255,0.35); }}
.moa-grade {{ background-color: {c['dark']};
    background-image: repeating-linear-gradient(to right, rgba(255,255,255,0.14) 0px, rgba(255,255,255,0.14) 2px,
                          rgba(0,0,0,0) 3px, rgba(0,0,0,0) 6px),
                      repeating-linear-gradient(to bottom, rgba(255,255,255,0.10) 0px, rgba(255,255,255,0.10) 2px,
                          rgba(0,0,0,0) 3px, rgba(0,0,0,0) 6px);
    border: 3px solid {c['plate_lo']}; border-radius: 10px; min-height: 28px;
    box-shadow: inset 0 3px 8px rgba(0,0,0,0.6); }}
.moa-plaquinha {{ background-color: {c['plate']};
    background-image: linear-gradient(to bottom, {_rgba(c['plate_hi'], 1)} 0%, {_rgba(c['plate'], 1)} 100%);
    border: 2px solid {c['plate_lo']}; border-radius: 8px; padding: 0px 14px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.7); }}
.moa-plaquinha label {{ color: {c['ink']}; font-weight: 800; letter-spacing: 4px; }}
"""


def _css_do_movel(c: dict[str, str], modo: str) -> str:
    """Estante com profundidade, vão côncavo, placas de prata, cartões e painel (mesma luz)."""
    if modo == "contorno":
        return f"""
.moa-placa {{ background-color: {c['white']}; border: 3px solid {c['dark']}; border-radius: 8px; padding: 4px 24px;
              box-shadow: inset 0 0 0 2px {c['white']}, inset 0 0 0 4px {c['dark']}; }}
.moa-placa label {{ color: {c['ink']}; font-weight: 800; }}
.moa-tabua {{ background-color: {c['case']}; background-image: none; border-bottom: 16px solid {c['white']};
              padding: 18px 18px 14px 18px; box-shadow: 0 6px 0 {c['dark']}, inset 0 0 0 3px {c['white']}; }}
.moa-tabua button.moa-disco label {{ color: {c['white']}; font-weight: 800; }}
.moa-tabua button.moa-disco:hover {{ background-color: transparent; border-color: {c['white']}; }}
.moa-tabua button.moa-disco:focus {{ outline: 5px solid {c['white']}; outline-offset: 3px; }}
.moa-vazio {{ background-color: {c['dark']}; border: 4px solid {c['white']}; border-radius: 6px;
              box-shadow: inset 0 0 0 3px {c['dark']}; }}
.moa-vazio label {{ color: {c['white']}; font-weight: 800; }}
.moa-cartao {{ background-color: {c['card']}; border: 3px solid {c['ink']}; border-radius: 14px;
               padding: 14px 18px; box-shadow: 0 4px 0 {c['ink']}; }}
.moa-painel {{ background-color: {c['card']}; border: 4px solid {c['ink']}; border-radius: 16px; padding: 24px;
               box-shadow: 0 4px 0 {c['ink']}; }}
"""
    return f"""
.moa-placa {{ background-color: {c['plate']};
    background-image: linear-gradient(to bottom, {_rgba(c['plate_hi'], 1)} 0%, {_rgba(c['plate'], 1)} 100%);
    border: 2px solid {c['plate_lo']}; border-radius: 8px; padding: 4px 24px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.7), 0 2px 0 rgba(0,0,0,0.35); }}
.moa-placa label {{ color: {c['ink']}; font-weight: 800; }}
.moa-tabua {{ background-color: {c['case']};
    background-image: linear-gradient(to bottom, rgba(0,0,0,0.45) 0px, rgba(0,0,0,0.15) 14px, rgba(0,0,0,0) 40px),
                      linear-gradient(to bottom, {_rgba(c['case_lo'], 1)} 0%, {_rgba(c['case_hi'], 1)} 100%);
    border-bottom: 16px solid {c['plate_lo']}; padding: 18px 18px 14px 18px;
    box-shadow: 0 6px 0 rgba(0,0,0,0.40), inset 0 12px 16px rgba(0,0,0,0.45), inset 0 -2px 0 rgba(255,255,255,0.18); }}
.moa-tabua button.moa-disco label {{ color: {c['white']}; font-weight: 800; }}
.moa-tabua button.moa-disco:hover {{ background-color: rgba(255,255,255,{ALFA_REALCE_NA_ESTANTE}); }}
.moa-tabua button.moa-disco:focus {{ outline: 5px solid {c['white']}; outline-offset: 3px; }}
.moa-vazio {{ background-color: {c['dark']}; border: 3px solid rgba(0,0,0,0.6); border-radius: 6px;
    box-shadow: inset 0 8px 14px rgba(0,0,0,0.75), inset 0 -2px 0 rgba(255,255,255,0.14); }}
.moa-vazio label {{ color: {c['white']}; font-weight: 800; }}
.moa-cartao {{ background-color: {c['card']}; border: 2px solid {c['line']}; border-radius: 14px;
    padding: 14px 18px; box-shadow: 0 4px 0 rgba(0,0,0,0.18), inset 0 2px 0 rgba(255,255,255,0.7); }}
.moa-painel {{ background-color: {c['card']}; border: 5px solid {c['plate_lo']}; border-radius: 16px; padding: 24px;
    box-shadow: 0 4px 0 rgba(0,0,0,0.30), inset 0 2px 0 rgba(255,255,255,0.7), 0 0 0 2px {c['dark']}; }}
"""


def _css_da_rolagem(c: dict[str, str], modo: str) -> str:
    """Barra de rolagem como um trilho grafite com um cursor de prata (sempre visível)."""
    if modo == "contorno":
        return f"""
scrollbar {{ background-color: {c['white']}; border: 0 solid {c['dark']}; }}
scrollbar trough {{ background-color: {c['dark']}; background-image: none; min-width: 30px;
                    border: 3px solid {c['white']}; box-shadow: inset 0 0 0 3px {c['dark']}; }}
scrollbar slider {{ background-color: {c['white']}; background-image: none; min-width: 26px; min-height: 72px;
                    border: 4px solid {c['dark']}; border-radius: 10px; box-shadow: 0 0 0 2px {c['white']}; }}
scrollbar slider:hover, scrollbar slider:active {{ background-color: {c['white']}; border-width: 6px; }}
"""
    friso = "rgba(0,0,0,0.30)"
    return f"""
scrollbar {{ background-color: {c['case_lo']}; border: 0 solid {c['dark']}; }}
scrollbar trough {{ background-color: {c['case_lo']}; background-image: none; min-width: 30px;
                    border: 0 solid {c['dark']}; box-shadow: inset 4px 0 8px rgba(0,0,0,0.65), inset -2px 0 0 rgba(255,255,255,0.12); }}
scrollbar slider {{ background-color: {c['plate']};
    background-image: linear-gradient(to right, {_rgba(c['plate_hi'], 1)} 0%, {_rgba(c['plate'], 1)} 55%, {_rgba(c['plate_lo'], 1)} 100%),
                      repeating-linear-gradient(to bottom, rgba(0,0,0,0) 0px, rgba(0,0,0,0) 4px, {friso} 5px, rgba(0,0,0,0) 6px);
    min-width: 26px; min-height: 72px; margin: 2px; border: 2px solid {c['plate_lo']}; border-radius: 10px;
    box-shadow: inset 0 2px 0 rgba(255,255,255,0.7), 0 3px 0 rgba(0,0,0,0.5); }}
scrollbar slider:hover {{ background-color: {c['plate_hi']}; }}
scrollbar slider:active {{ box-shadow: inset 0 3px 0 rgba(0,0,0,0.3); margin-top: 4px; }}
"""


def _css_das_teclas(c: dict[str, str], modo: str) -> str:
    """CSS das teclas de metal com bisel (botões de ação, escolhas e marcações), das lâmpadas e das variantes."""
    b, h, p = BORDA_PX, ALTURA_DA_TECLA_PX, PADDING_TOPO_PX
    pe = ALVO_MINIMO_PX
    teclas = "button.moa-btn, button.moa-opcao, button.moa-marca"
    apertadas = ("button.moa-btn:active, button.moa-btn.moa-travada, button.moa-pausar, "
                 "button.moa-opcao.moa-escolhida, button.moa-marca.moa-marcada")
    rotulos_apertados = ("button.moa-btn:active label, button.moa-btn.moa-travada label, "
                         "button.moa-pausar label, button.moa-opcao.moa-escolhida label, "
                         "button.moa-marca.moa-marcada label")
    faixa = FAIXA_DO_BRILHO_PX
    repouso = (f"border-style: solid; border-width: {b}px {b}px {b + h}px {b}px; border-radius: 10px; "
               f"padding: {p}px 20px {p}px 20px;")
    apertada = f"border-width: {b}px {b}px {b + 1}px {b}px; padding-top: {p + h - 1}px;"
    if modo == "contorno":      # preto e branco: contorno duplo e sombra, sem tons (KTD3)
        bordas = f"border-color: {c['dark']};"
        face = (f"background-color: {c['key_lo']}; background-image: none; "
                f"box-shadow: inset 0 0 0 2px {c['white']}, inset 0 0 0 4px {c['dark']};")
        bordas_apertada = f"border-color: {c['dark']};"
        face_apertada = (f"background-color: {c['keyon']}; background-image: none; "
                         f"box-shadow: inset 0 0 0 3px {c['white']};")
        brilho_colorido = "background-image: none;"
    else:
        # bisel: a luz vem de cima e da esquerda (borda clara em cima e à esquerda, escura embaixo e à direita)
        bordas = f"border-color: {c['key_edge']} {c['plate_lo']} {c['dark']} {c['key_edge']};"
        face = (f"background-color: {c['key_lo']}; "
                f"background-image: linear-gradient(to bottom, rgba(255,255,255,{ALFA_REALCE_DA_TECLA}) 0px, "
                f"rgba(255,255,255,0) 60%), "
                f"linear-gradient(to bottom, rgba(0,0,0,0) 45%, rgba(0,0,0,{ALFA_SOMBRA_DA_TECLA}) 100%); "
                f"box-shadow: inset 0 1px 0 rgba(255,255,255,0.9), 0 2px 0 rgba(0,0,0,0.45);")
        # tecla afundada: mais escura, com o centro "para dentro" (sombra por dentro) e o bisel invertido
        bordas_apertada = f"border-color: {c['dark']} {c['key_edge']} {c['key_edge']} {c['dark']};"
        face_apertada = (f"background-color: {c['keyon']}; "
                         f"background-image: linear-gradient(to bottom, {_rgba(c['keyon_lo'], 1)} 0%, "
                         f"{_rgba(c['keyon'], 1)} 40%, {_rgba(c['keyon_hi'], 1)} 100%); "
                         f"box-shadow: inset 0 3px 6px rgba(0,0,0,0.6);")
        # tecla colorida: brilho só numa faixa fina no topo (acima da letra) e sombreado no pé (KTD2)
        brilho_colorido = (f"background-image: linear-gradient(to bottom, rgba(255,255,255,{ALFA_BRILHO_DA_TECLA}) 0px, "
                           f"rgba(255,255,255,{ALFA_BRILHO_DA_TECLA}) {faixa - 2}px, rgba(255,255,255,0) {faixa}px), "
                           f"linear-gradient(to bottom, rgba(0,0,0,0) 45%, rgba(0,0,0,{ALFA_SOMBRA_DA_TECLA}) 100%);")
    return f"""
/* teclas de metal com bisel e curso (ADR-0025): alvo de 64 px, foco bem visível */
{teclas} {{ min-height: {pe}px; min-width: {pe}px; font-weight: 800; color: {c['ink']};
    {repouso}
    {bordas}
    {face}
    text-shadow: none; }}
button.moa-btn label {{ color: inherit; font-weight: 800; }}
button.moa-btn:hover, button.moa-opcao:hover, button.moa-marca:hover {{ background-color: {c['key_hi']}; }}
{teclas.replace(', ', ':focus, ')}:focus {{ outline: 5px solid {c['focus']}; outline-offset: 3px; }}
{apertadas} {{ {apertada}
    {bordas_apertada}
    {face_apertada}
    color: {c['white']}; }}
{rotulos_apertados} {{ color: {c['white']}; }}
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
button.moa-marca {{ padding-left: 12px; padding-right: 12px; }}
button.moa-marca label {{ color: {c['ink']}; }}
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
    capada = round(LETRA_BASE_PX * min(e, 1.2))      # letra da barra do pé: no máximo "Grande"
    modo = relevo(paleta)
    return f"""
* {{ font-size: {base}px; }}
window.moa, .moa-fundo {{ background-color: {c['bg']}; color: {c['ink']}; }}
label {{ color: {c['ink']}; }}
.moa-titulo {{ font-size: {titulo}px; font-weight: 800; }}
.moa-grande {{ font-size: {grande}px; font-weight: 800; }}
.moa-forte {{ font-weight: 800; }}
.moa-nota {{ color: {c['ink2']}; font-weight: 600; }}

.moa-cabecalho {{ background-color: {c['card']}; border-bottom: 3px solid {c['case2']};
                  padding: 10px 20px; }}
.moa-mini {{ background-color: {c['case']}; border-top: 5px solid {c['plate_lo']}; padding: 8px 18px 4px 18px; }}
/* a barra do pé nunca passa da letra "Grande": o básico do rádio tem de caber mesmo em letra "Maior" */
.moa-mini label, .moa-mini button.moa-btn {{ font-size: {capada}px; }}
.moa-mini .moa-grande {{ font-size: {round(26 * min(e, 1.2))}px; }}
.moa-mini label {{ color: {c['white']}; }}
.moa-mini .moa-dica {{ color: {c['hint']}; font-weight: 700; }}
.moa-mini .moa-barra trough {{ min-height: 30px; border-radius: 15px; }}
.moa-mini .moa-barra progress {{ min-height: 30px; border-radius: 12px; }}

{_css_das_teclas(c, modo)}

/* estante */
{_css_do_movel(c, modo)}
{_css_da_rolagem(c, modo)}
button.moa-disco {{ min-height: {ALVO_MINIMO_PX}px; background-image: none; background-color: transparent;
                    border: 3px solid transparent; border-radius: 12px; padding: 6px; box-shadow: none; }}
button.moa-disco:hover {{ background-color: {c['selbg']}; }}
button.moa-disco:focus {{ outline: 5px solid {c['focus']}; outline-offset: 3px; }}
button.moa-disco label {{ color: {c['ink']}; font-weight: 800; }}
.moa-capa {{ border-radius: 6px; box-shadow: 0 3px 0 rgba(0,0,0,.35); }}
.moa-continuar {{ border: 3px solid {c['green']}; }}
.moa-aviso {{ background-color: {c['warn']}; border: 3px solid {c['warnb']}; border-radius: 14px;
              padding: 12px 16px; }}
.moa-aviso label {{ color: {c['ink']}; font-weight: 700; }}
.moa-perigo-caixa {{ background-color: {c['warn']}; border: 4px solid {c['danger']}; border-radius: 14px;
                     padding: 14px 18px; }}

/* rádio */
{_css_do_aparelho(c, modo)}
.moa-visor .moa-nota-visor {{ background-color: {c['white']}; color: {c['ink']}; border-radius: 6px; padding: 2px 8px;
                              font-weight: 700; }}
.moa-radio button.moa-tocar {{ background-color: {c['green']}; color: {c['white']}; min-height: 92px; font-size: {grande}px; }}
.moa-radio button.moa-tocar label {{ color: {c['white']}; }}
.moa-radio button.moa-pausar {{ min-height: 92px; font-size: {grande}px; }}
.moa-radio button.moa-clara-ligada {{ color: {c['white']}; }}
.moa-radio button.moa-btn:focus {{ outline: 5px solid {c['white']}; outline-offset: 3px; }}
.moa-barra trough {{ min-height: 26px; background-color: {c['white']}; border: 3px solid {c['dark']};
                     border-radius: 13px; }}
.moa-barra progress {{ min-height: 26px; background-color: {c['green']}; background-image: none;
                       border-radius: 10px; border-right: 8px solid {c['dark']}; }}
.moa-barra {{ background-color: {c['lampoff']}; border: 2px solid {c['white']}; border-radius: 4px;
              min-width: 14px; min-height: 34px; }}

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
