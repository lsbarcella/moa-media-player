from estante.core.textutil import fold, natural_key


def test_fold_tira_acentos_e_maiusculas():
    assert fold("Árvore") == "arvore"
    assert fold("AÇÃO") == "acao"
    assert fold("Zé") == "ze"


def test_ordem_natural_poe_2_antes_de_10():
    nomes = ["Faixa 10", "Faixa 2", "Faixa 1"]
    assert sorted(nomes, key=natural_key) == ["Faixa 1", "Faixa 2", "Faixa 10"]


def test_ordem_natural_ignora_acento_e_caixa():
    nomes = ["Zé", "álvaro", "Beto"]
    assert sorted(nomes, key=natural_key) == ["álvaro", "Beto", "Zé"]


def test_ordem_natural_com_numero_no_meio():
    nomes = ["Vol 10 Sucessos", "Vol 2 Sucessos"]
    assert sorted(nomes, key=natural_key) == ["Vol 2 Sucessos", "Vol 10 Sucessos"]


def test_texto_vazio_nao_quebra():
    assert natural_key("") == [""]
