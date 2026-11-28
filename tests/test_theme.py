# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes do tema (M3): contraste de 7:1 e tamanhos mínimos."""

import re

import pytest

from moa.ui import theme


@pytest.mark.parametrize("paleta", list(theme.PALETAS))
def test_todo_par_de_texto_e_fundo_tem_contraste_de_7_para_1(paleta):
    ruins = [(t, f, round(theme.contraste(paleta, t, f), 2))
             for t, f in theme.PARES_DE_CONTRASTE
             if theme.contraste(paleta, t, f) < theme.CONTRASTE_MINIMO]
    assert not ruins, f"{paleta}: {ruins}"


def test_as_quatro_paletas_e_as_tres_letras_existem():
    assert list(theme.PALETAS) == ["normal", "vermelho-verde", "azul-amarelo", "preto-e-branco"]
    assert list(theme.ESCALAS) == ["normal", "grande", "maior"]


def _tamanhos(css, propriedade):
    return [int(v) for v in re.findall(rf"{propriedade}:\s*(\d+)px", css)]


@pytest.mark.parametrize("paleta", list(theme.PALETAS))
def test_na_escala_normal_nenhum_texto_tem_menos_de_20px_e_nenhum_botao_menos_de_64px(paleta):
    css = theme.gerar_css(paleta, "normal")
    assert min(_tamanhos(css, "font-size")) >= 20
    botoes = re.findall(r"button\.moa-\w+ \{[^}]*?min-height:\s*(\d+)px", css)
    assert botoes and min(int(b) for b in botoes) >= 64


def test_nas_escalas_grande_e_maior_a_letra_so_cresce():
    normal, grande, maior = (max(_tamanhos(theme.gerar_css("normal", e), "font-size"))
                             for e in ("normal", "grande", "maior"))
    assert normal < grande < maior
    base = lambda e: _tamanhos(theme.gerar_css("normal", e), "font-size")[0]
    assert base("normal") == 20 < base("grande") < base("maior")


def test_o_css_trocou_de_cor_ao_trocar_de_paleta():
    assert theme.gerar_css("normal") != theme.gerar_css("preto-e-branco")
    assert "#14407A" in theme.gerar_css("vermelho-verde")


def test_o_css_e_aceito_pelo_gtk():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    for paleta in theme.PALETAS:
        for letra in theme.ESCALAS:
            provedor = Gtk.CssProvider()
            provedor.load_from_data(theme.gerar_css(paleta, letra).encode("utf-8"))


# -- materiais do nível 3 (ADR-0024): tokens e contraste no pior ponto -------------------------

TOKENS_DE_MATERIAL = ("wood_hi", "wood_lo", "brass_hi", "brass", "brass_lo", "metal_hi", "metal_lo",
                      "key_hi", "key_lo", "visor_hi", "visor_lo")


@pytest.mark.parametrize("paleta", list(theme.PALETAS))
def test_os_tokens_de_material_existem_nas_quatro_paletas(paleta):
    for token in TOKENS_DE_MATERIAL:
        cor = theme.PALETAS[paleta][token]
        assert re.fullmatch(r"#[0-9A-Fa-f]{6}", cor), (paleta, token, cor)


def test_no_preto_e_branco_os_materiais_so_tem_preto_ou_branco():
    for token in TOKENS_DE_MATERIAL:
        assert theme.PALETAS["preto-e-branco"][token].upper() in ("#000000", "#FFFFFF"), token


def test_relevo_por_contorno_so_no_preto_e_branco():
    assert theme.relevo("preto-e-branco") == "contorno"
    assert {theme.relevo(p) for p in theme.PALETAS if p != "preto-e-branco"} == {"tons"}


def test_misturar_uma_camada_translucida_sobre_uma_cor():
    assert theme.misturar("#000000", "#FFFFFF", 0.5) in ("#7F7F7F", "#808080")
    assert theme.misturar("#1F4D2B", "#FFFFFF", 0.0) == "#1F4D2B"
    assert theme.misturar("#1F4D2B", "#FFFFFF", 1.0) == "#FFFFFF"


@pytest.mark.parametrize("paleta", list(theme.PALETAS))
def test_todo_material_tem_7_para_1_no_pior_ponto_do_degrade(paleta):
    ruins = [(m.nome, round(theme.contraste_no_pior_ponto(paleta, m), 2))
             for m in theme.MATERIAIS if theme.contraste_no_pior_ponto(paleta, m) < theme.CONTRASTE_MINIMO]
    assert not ruins, f"{paleta}: {ruins}"


def test_o_brilho_cobrindo_a_letra_do_botao_verde_falha_e_a_checagem_enxerga():
    """A armadilha do preview: brilho translúcido atrás da letra derruba o contraste."""
    armadilha = theme.Material("brilho atrás da letra", "white", ("green",), (("white", 0.30),))
    assert theme.contraste_no_pior_ponto("normal", armadilha) < theme.CONTRASTE_MINIMO


def test_latao_escuro_com_letra_falha_e_o_claro_passa():
    escuro = theme.Material("latão escuro com letra", "ink", ("brass_lo",), ())
    claro = theme.Material("latão claro com letra", "ink", ("brass_hi", "brass"), ())
    assert theme.contraste_no_pior_ponto("normal", escuro) < theme.CONTRASTE_MINIMO
    assert theme.contraste_no_pior_ponto("normal", claro) >= theme.CONTRASTE_MINIMO


def test_a_tabela_de_materiais_cobre_madeira_latao_vidro_e_as_teclas():
    nomes = " ".join(m.nome for m in theme.MATERIAIS).lower()
    for palavra in ("madeira", "latão", "visor", "tecla"):
        assert palavra in nomes


def test_as_opacidades_do_css_vem_da_tabela_unica():
    """KTD8: o número que o teste confere é o mesmo que vai para o CSS."""
    assert theme.ALFA_BRILHO_DA_TECLA == pytest.approx(0.30)
    assert 0 < theme.ALFA_VEIO_CLARO <= 0.10


# -- teclas com curso (U2, ADR-0024) -------------------------------------------------------------

@pytest.mark.parametrize("letra", list(theme.ESCALAS))
def test_o_brilho_da_tecla_termina_acima_do_rotulo_em_toda_escala(letra):
    """A faixa do brilho (px) cabe dentro do espaço de cima da tecla, então não cobre a letra."""
    assert theme.FAIXA_DO_BRILHO_PX <= theme.PADDING_TOPO_PX
    css = theme.gerar_css("normal", letra)
    faixas = {int(n) for n in re.findall(r"rgba\(255,255,255,0\)\s+(\d+)px", css)}
    assert theme.FAIXA_DO_BRILHO_PX in faixas
    assert all(f <= theme.PADDING_TOPO_PX for f in faixas)


def test_tecla_apertada_troca_borda_de_baixo_por_espaco_em_cima_sem_mudar_a_altura():
    css = theme.gerar_css("normal", "normal")
    repouso = theme.BORDA_PX + theme.ALTURA_DA_TECLA_PX
    apertada_borda = theme.BORDA_PX + 1
    assert f"border-bottom-width: {repouso}px" in css
    assert f"border-bottom-width: {apertada_borda}px" in css
    # a soma (borda de baixo + espaço de cima) é igual em repouso e apertada: altura constante
    assert (repouso + theme.PADDING_TOPO_PX
            == apertada_borda + theme.PADDING_TOPO_PX + theme.ALTURA_DA_TECLA_PX - 1)


def test_nenhum_degrade_opaco_esconde_a_cor_das_teclas():
    """KTD1: todo degradê de tecla é translúcido (rgba), nunca um #RRGGBB opaco em background-image."""
    for paleta in theme.PALETAS:
        css = theme.gerar_css(paleta, "normal")
        for bloco in re.findall(r"background-image:\s*([^;]+);", css):
            if "gradient" in bloco:
                assert "#" not in bloco, (paleta, bloco)


def test_no_preto_e_branco_as_teclas_nao_usam_degrade():
    css = theme.gerar_css("preto-e-branco", "normal")
    bloco = re.search(r"button\.moa-btn,[^{]*\{[^}]*\}", css).group(0)
    assert "gradient" not in bloco and "inset 0 0 0" in bloco       # contorno duplo e sombra


def test_a_tecla_travada_tem_a_mesma_geometria_da_apertada():
    css = theme.gerar_css("normal", "normal")
    for seletor in ("button.moa-btn.moa-travada", "button.moa-opcao.moa-escolhida",
                    "button.moa-marca.moa-marcada", "button.moa-btn:active"):
        assert seletor in css


def test_o_css_com_relevo_e_aceito_pelo_gtk_em_toda_combinacao():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    for paleta in theme.PALETAS:
        for letra in theme.ESCALAS:
            Gtk.CssProvider().load_from_data(theme.gerar_css(paleta, letra).encode("utf-8"))


# -- gabinete, visor, moldura de metal e grade (U3, ADR-0024) ------------------------------------

def _bloco(css: str, seletor: str) -> str:
    achou = re.search(re.escape(seletor) + r"\s*\{([^}]*)\}", css)
    assert achou, f"sem regra para {seletor}"
    return achou.group(1)


@pytest.mark.parametrize("paleta", [p for p in theme.PALETAS if p != "preto-e-branco"])
def test_gabinete_de_madeira_tem_veios_e_moldura_de_latao(paleta):
    bloco = _bloco(theme.gerar_css(paleta, "normal"), ".moa-radio")
    assert "repeating-linear-gradient" in bloco                          # veios
    assert theme.PALETAS[paleta]["brass"].lower() in bloco.lower()       # moldura de latão


def test_gabinete_no_preto_e_branco_nao_tem_veios_e_usa_contorno_duplo():
    bloco = _bloco(theme.gerar_css("preto-e-branco", "normal"), ".moa-radio")
    assert "gradient" not in bloco and "inset 0 0 0" in bloco


@pytest.mark.parametrize("paleta", [p for p in theme.PALETAS if p != "preto-e-branco"])
def test_visor_de_vidro_tem_degrade_sombra_interna_e_reflexo_so_na_borda(paleta):
    bloco = _bloco(theme.gerar_css(paleta, "normal"), ".moa-visor")
    assert "linear-gradient" in bloco and "inset" in bloco
    # o reflexo é um fio claro na borda (inset de poucos px), não uma camada sobre o texto
    assert "radial-gradient" not in bloco


def test_visor_no_preto_e_branco_e_branco_chapado_com_contorno():
    bloco = _bloco(theme.gerar_css("preto-e-branco", "normal"), ".moa-visor")
    assert "gradient" not in bloco


def test_existem_moldura_de_metal_grade_e_plaquinha_do_aparelho():
    css = theme.gerar_css("normal", "normal")
    for seletor in (".moa-metal", ".moa-grade", ".moa-plaquinha"):
        assert seletor in css



def test_a_nota_do_visor_continua_numa_caixinha_branca():
    assert "background-color: #FFFFFF" in _bloco(theme.gerar_css("normal", "normal"), ".moa-visor .moa-nota-visor")


# -- estante com profundidade e telas coerentes (U7, ADR-0024) -------------------------------------

@pytest.mark.parametrize("paleta", [p for p in theme.PALETAS if p != "preto-e-branco"])
def test_estante_tem_fundo_recuado_e_tampo_com_sombra(paleta):
    css = theme.gerar_css(paleta, "normal")
    fundo = _bloco(css, ".moa-tabua")
    assert "inset" in fundo                                   # o fundo recuado tem sombra por dentro
    assert "box-shadow" in fundo and "border-bottom" in fundo  # e o tampo tem quina e sombra por fora


def test_o_nome_do_disco_na_estante_e_branco_sobre_a_madeira_escura():
    css = theme.gerar_css("normal", "normal")
    assert "#FFFFFF" in _bloco(css, ".moa-tabua button.moa-disco label")


def test_o_vao_em_uso_no_radio_e_concavo():
    assert "inset" in _bloco(theme.gerar_css("normal", "normal"), ".moa-vazio")


def test_as_placas_dos_titulos_sao_de_latao_com_texto_escuro():
    css = theme.gerar_css("normal", "normal")
    assert theme.PALETAS["normal"]["brass"].lower() in _bloco(css, ".moa-placa").lower()
    assert theme.PALETAS["normal"]["ink"].lower() in _bloco(css, ".moa-placa label").lower()


def test_cartoes_e_painel_seguem_a_mesma_luz_do_aparelho():
    css = theme.gerar_css("normal", "normal")
    for seletor in (".moa-cartao", ".moa-painel"):
        bloco = _bloco(css, seletor)
        assert "inset 0 2px 0" in bloco and "0 4px 0" in bloco, seletor    # realce em cima, sombra rígida embaixo


def test_o_preto_e_branco_da_estante_nao_tem_tons():
    css = theme.gerar_css("preto-e-branco", "normal")
    for seletor in (".moa-tabua", ".moa-placa", ".moa-cartao"):
        assert "gradient" not in _bloco(css, seletor), seletor


def test_no_preto_e_branco_nenhum_token_de_fundo_de_tecla_tem_tom():
    for token in ("btnradio", "key_hi", "key_lo", "card", "disabled"):
        cor = theme.PALETAS["preto-e-branco"][token].lstrip("#")
        canais = [int(cor[i:i + 2], 16) for i in (0, 2, 4)]
        assert max(canais) - min(canais) <= 8, (token, cor)


# -- barra de rolagem temática (ADR-0024) ---------------------------------------------------------

@pytest.mark.parametrize("paleta", list(theme.PALETAS))
def test_a_barra_de_rolagem_e_larga_o_bastante_para_o_mouse(paleta):
    css = theme.gerar_css(paleta, "normal")
    largura = int(re.search(r"scrollbar slider \{[^}]*?min-width:\s*(\d+)px", css).group(1))
    assert largura >= 26
    assert int(re.search(r"scrollbar slider \{[^}]*?min-height:\s*(\d+)px", css).group(1)) >= theme.ALVO_MINIMO_PX


def test_a_canaleta_e_escura_e_o_cursor_e_de_latao():
    css = theme.gerar_css("normal", "normal")
    assert theme.PALETAS["normal"]["brass"].lower() in _bloco(css, "scrollbar slider").lower()
    assert "inset" in _bloco(css, "scrollbar trough")


def test_no_preto_e_branco_a_barra_nao_tem_degrade():
    css = theme.gerar_css("preto-e-branco", "normal")
    assert "gradient" not in _bloco(css, "scrollbar slider") and "gradient" not in _bloco(css, "scrollbar trough")

