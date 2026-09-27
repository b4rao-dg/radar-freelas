"""
Testes do Radar de Freelas.

Rodar:  python -m pytest

Os HTMLs em tests/exemplos/ são inventados, mas copiam a estrutura das páginas
reais. Assim os testes não dependem de internet e sempre dão o mesmo resultado.
"""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from buscador import (
    combina,
    ler_99freelas,
    ler_workana,
    montar_mensagem,
    normalizar,
    preencher_datas_99freelas,
)

EXEMPLOS = Path(__file__).parent / "exemplos"


def ler_exemplo(nome: str) -> str:
    return (EXEMPLOS / nome).read_text(encoding="utf-8")


def projeto(titulo="", descricao="", habilidades=None) -> dict:
    """Cria um projeto de mentira só com os campos que o filtro usa."""
    return {"titulo": titulo, "descricao": descricao, "habilidades": habilidades or []}


# ---------------------------------------------------------------------------
# normalizar
# ---------------------------------------------------------------------------

def test_normalizar_tira_acentos_e_deixa_minusculo():
    assert normalizar("Automação em PYTHON") == "automacao em python"


def test_normalizar_aceita_none():
    assert normalizar(None) == ""


# ---------------------------------------------------------------------------
# combina (o filtro de palavras-chave)
# ---------------------------------------------------------------------------

def test_combina_encontra_palavra_no_titulo_descricao_e_habilidades():
    p = projeto(titulo="Robô", descricao="usar selenium", habilidades=["Python"])
    assert combina(p, ["python", "selenium", "django"], []) == ["python", "selenium"]


def test_combina_ignora_acento_e_maiuscula():
    p = projeto(titulo="Preciso de AUTOMAÇÃO")
    assert combina(p, ["automacao"], []) == ["automacao"]


# parametrize roda o mesmo teste várias vezes, uma para cada linha da lista
@pytest.mark.parametrize("texto", ["Bot de WhatsApp", "Entrega rápida", "apiário"])
def test_combina_nao_casa_pedaco_de_palavra(texto):
    # "sap" está dentro de "whatsapp" e "api" dentro de "rápida"/"apiário",
    # mas não são a palavra inteira, então não devem contar.
    assert combina(projeto(titulo=texto), ["sap", "api"], []) == []


def test_combina_casa_palavra_colada_em_pontuacao():
    p = projeto(descricao="Integração com API/REST (python).")
    assert combina(p, ["api", "python"], []) == ["api", "python"]


def test_combina_expressao_com_mais_de_uma_palavra():
    p = projeto(titulo="Criar uma Landing Page")
    assert combina(p, ["landing page"], []) == ["landing page"]


def test_palavra_excluida_descarta_o_projeto():
    p = projeto(titulo="Bot em Python para WordPress")
    assert combina(p, ["python", "bot"], ["wordpress"]) == []


# ---------------------------------------------------------------------------
# 99Freelas
# ---------------------------------------------------------------------------

def test_ler_99freelas_extrai_os_campos():
    projetos = ler_99freelas(ler_exemplo("99freelas.html"))
    primeiro = projetos[0]

    assert primeiro["id"] == "99f-111"
    assert primeiro["site"] == "99Freelas"
    assert primeiro["titulo"] == "Robô em Python para planilhas"
    assert primeiro["habilidades"] == ["Python", "Excel"]


def test_ler_99freelas_limpa_link_e_descricao():
    primeiro = ler_99freelas(ler_exemplo("99freelas.html"))[0]

    # o "?fs=t" do fim do link é removido
    assert primeiro["link"] == "https://www.99freelas.com.br/project/robo-em-python-para-planilhas-111"
    # os botões "Expandir"/"Esconder" e as reticências somem da descrição
    assert primeiro["descricao"] == "Preciso automatizar uma planilha de Excel"


def test_ler_99freelas_preenche_as_datas():
    info = ler_99freelas(ler_exemplo("99freelas.html"))[0]["info"]
    # 1790000000000 ms = 21/09/2026 14:13 UTC = 11:13 em Brasília
    assert "Publicado: 21/09 11:13" in info
    assert "Propostas: 3" in info


def test_ler_99freelas_aceita_projeto_sem_info_e_ignora_sem_titulo():
    projetos = ler_99freelas(ler_exemplo("99freelas.html"))

    assert [p["id"] for p in projetos] == ["99f-111", "99f-222"]
    assert projetos[1]["info"] == ""
    assert projetos[1]["habilidades"] == []


def test_ler_99freelas_pagina_sem_projetos():
    assert ler_99freelas("<html><body>Nada aqui</body></html>") == []


def test_tempo_restante_que_ja_acabou():
    info = BeautifulSoup('<p><b class="datetime-restante" cp-datetime="0"></b></p>', "html.parser")
    preencher_datas_99freelas(info)
    assert info.get_text() == "menos de 1 dia"


# ---------------------------------------------------------------------------
# Workana
# ---------------------------------------------------------------------------

def test_ler_workana_extrai_os_campos():
    projetos = ler_workana(ler_exemplo("workana.html"))

    assert len(projetos) == 1  # o projeto sem slug é ignorado
    p = projetos[0]
    assert p["id"] == "wk-bot-de-precos-em-python"
    assert p["link"] == "https://www.workana.com/job/bot-de-precos-em-python"
    assert p["habilidades"] == ["Python", "Web Scraping"]


def test_ler_workana_usa_o_titulo_completo():
    # O texto visível vem cortado ("Merc..."); o completo está no atributo title.
    p = ler_workana(ler_exemplo("workana.html"))[0]
    assert p["titulo"] == "Bot de preços em Python para Mercado Livre e Amazon"


def test_ler_workana_transforma_html_em_texto():
    p = ler_workana(ler_exemplo("workana.html"))[0]
    assert p["descricao"] == "Quero um scraper que compare preços."
    assert p["info"] == "USD 50 - 100 | Publicado: há 2 horas | Propostas: 4"


def test_ler_workana_pagina_sem_a_tag_search():
    # Se o Workana mudar a página, o leitor devolve lista vazia em vez de quebrar.
    assert ler_workana("<html><body></body></html>") == []


# ---------------------------------------------------------------------------
# Mensagem do Telegram
# ---------------------------------------------------------------------------

def projeto_completo(**mudancas) -> dict:
    p = {
        "site": "Workana",
        "titulo": "Bot em Python",
        "info": "USD 50",
        "descricao": "Descrição curta",
        "link": "https://www.workana.com/job/bot",
        "habilidades": [],
    }
    p.update(mudancas)
    return p


def test_mensagem_tem_titulo_em_negrito_palavras_e_link():
    msg = montar_mensagem(projeto_completo(), ["python", "bot"])
    assert msg.startswith("<b>[Workana] Bot em Python</b>")
    assert "python, bot" in msg
    assert msg.endswith("https://www.workana.com/job/bot")


def test_mensagem_escapa_caracteres_de_html():
    # Um "<" solto quebraria o parse_mode=HTML do Telegram (erro 400).
    msg = montar_mensagem(projeto_completo(titulo="Site <HTML> & CSS"), [])
    assert "Site &lt;HTML&gt; &amp; CSS" in msg


def test_mensagem_corta_descricao_longa_sem_cortar_palavra():
    msg = montar_mensagem(projeto_completo(descricao="palavra " * 200), [])
    trecho = msg.split("\n\n")[1]
    assert len(trecho) <= 601
    assert trecho.endswith("palavra…")
