"""
Radar de Freelas
----------------
Procura projetos novos no 99Freelas e no Workana, filtra pelas palavras-chave
do config.json e manda os que interessam para o seu Telegram.

Uso:
    python buscador.py          -> busca e envia para o Telegram
    python buscador.py --teste  -> busca e só mostra no terminal (não envia nada
                                   e não marca os projetos como vistos)
"""

import html
import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

PASTA = Path(__file__).parent
ARQUIVO_CONFIG = PASTA / "config.json"
ARQUIVO_VISTOS = PASTA / "vistos.json"

# O GitHub Actions roda em UTC; o Brasil não tem mais horário de verão, então -3h fixo serve.
BRASILIA = timezone(timedelta(hours=-3))

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def normalizar(texto: str) -> str:
    """Deixa em minúsculas e tira acentos, para 'Automação' casar com 'automacao'."""
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def texto_limpo(fragmento_html: str) -> str:
    """Converte um trecho de HTML em texto simples."""
    return BeautifulSoup(fragmento_html or "", "html.parser").get_text(" ", strip=True)


def baixar(url: str) -> str:
    resposta = requests.get(url, headers=CABECALHOS, timeout=30)
    resposta.raise_for_status()
    return resposta.text


# ---------------------------------------------------------------------------
# 99Freelas
# ---------------------------------------------------------------------------

def preencher_datas_99freelas(info) -> None:
    """As datas vêm vazias, só com um timestamp em milissegundos no atributo 'cp-datetime'
    (no navegador, um JavaScript preenche o texto). Aqui fazemos isso em Python."""
    agora = datetime.now(BRASILIA)
    for tag in info.select("[cp-datetime]"):
        data = datetime.fromtimestamp(int(tag["cp-datetime"]) / 1000, BRASILIA)
        if "datetime-restante" in tag.get("class", []):
            dias = (data - agora).days
            tag.string = f"{dias} dias" if dias > 0 else "menos de 1 dia"
        else:
            tag.string = data.strftime("%d/%m %H:%M")


def ler_99freelas(html_pagina: str) -> list[dict]:
    """Extrai os projetos de uma página de listagem do 99Freelas."""
    sopa = BeautifulSoup(html_pagina, "html.parser")
    projetos = []
    for item in sopa.select("li.result-item"):
        link = item.select_one("h1.title a")
        if not link:
            continue
        descricao = item.select_one(".description")
        if descricao:
            for botao in descricao.select(".more-link, .less-link"):
                botao.decompose()
        info = item.select_one(".information")
        if info:
            preencher_datas_99freelas(info)
        habilidades = [a.get_text(strip=True) for a in item.select("a.habilidade")]
        projetos.append({
            "id": "99f-" + item.get("data-id", link["href"]),
            "site": "99Freelas",
            "titulo": link.get_text(strip=True),
            "link": "https://www.99freelas.com.br" + link["href"].split("?")[0],
            "descricao": descricao.get_text(" ", strip=True).replace(" …", "") if descricao else "",
            "info": " ".join(info.get_text(" ", strip=True).split()) if info else "",
            "habilidades": habilidades,
        })
    return projetos


def buscar_99freelas(categoria: str, paginas: int) -> list[dict]:
    projetos = []
    for pagina in range(1, paginas + 1):
        url = f"https://www.99freelas.com.br/projects?categoria={categoria}&page={pagina}"
        projetos += ler_99freelas(baixar(url))
        time.sleep(2)  # educação com o site: uma página a cada 2 segundos
    return projetos


# ---------------------------------------------------------------------------
# Workana
# ---------------------------------------------------------------------------

def ler_workana(html_pagina: str) -> list[dict]:
    """O Workana guarda os projetos como JSON no atributo ':results-initials' da tag <search>."""
    sopa = BeautifulSoup(html_pagina, "html.parser")
    tag = sopa.find("search")
    if not tag or not tag.get(":results-initials"):
        return []
    dados = json.loads(tag[":results-initials"])
    projetos = []
    for r in dados.get("results", []):
        slug = r.get("slug")
        if not slug:
            continue
        info = " | ".join(x for x in [
            r.get("budget") or "",
            texto_limpo(r.get("publishedDate", "")),
            texto_limpo(r.get("totalBids", "")),
        ] if x)
        # O título visível vem cortado ("..."); o completo fica no atributo title do <span>.
        span = BeautifulSoup(r.get("title", ""), "html.parser").find("span")
        titulo = span.get("title") if span and span.get("title") else texto_limpo(r.get("title", ""))
        projetos.append({
            "id": "wk-" + slug,
            "site": "Workana",
            "titulo": titulo,
            "link": f"https://www.workana.com/job/{slug}",
            "descricao": texto_limpo(r.get("description", "")),
            "info": info,
            "habilidades": [s.get("anchorText", "") for s in r.get("skills", [])],
        })
    return projetos


def buscar_workana(categoria: str, paginas: int) -> list[dict]:
    projetos = []
    for pagina in range(1, paginas + 1):
        url = f"https://www.workana.com/jobs?category={categoria}&language=pt&page={pagina}"
        projetos += ler_workana(baixar(url))
        time.sleep(2)
    return projetos


# ---------------------------------------------------------------------------
# Filtro
# ---------------------------------------------------------------------------

def combina(projeto: dict, incluir: list[str], excluir: list[str]) -> list[str]:
    """Devolve as palavras-chave encontradas (lista vazia = não interessa)."""
    texto = normalizar(" ".join([
        projeto["titulo"], projeto["descricao"], " ".join(projeto["habilidades"])
    ]))

    def aparece(palavra: str) -> bool:
        # Palavra inteira: "api" casa com "API REST", mas não com "rápido".
        return re.search(r"(?<!\w)" + re.escape(normalizar(palavra)) + r"(?!\w)", texto) is not None

    if any(aparece(p) for p in excluir):
        return []
    return [p for p in incluir if aparece(p)]


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def montar_mensagem(projeto: dict, palavras: list[str]) -> str:
    descricao = projeto["descricao"]
    if len(descricao) > 600:
        descricao = descricao[:600].rsplit(" ", 1)[0] + "…"
    e = html.escape
    return (
        f"<b>[{e(projeto['site'])}] {e(projeto['titulo'])}</b>\n"
        f"<i>{e(projeto['info'])}</i>\n\n"
        f"{e(descricao)}\n\n"
        f"🔎 {e(', '.join(palavras))}\n"
        f"{e(projeto['link'])}"
    )


def enviar_telegram(token: str, chat_id: str, mensagem: str) -> None:
    resposta = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": mensagem,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        },
        timeout=30,
    )
    if not resposta.ok:
        # O Telegram explica o motivo no campo "description" (ex.: "chat not found").
        # Mostramos só ele, porque a URL do erro padrão contém o token.
        motivo = resposta.json().get("description", resposta.text)
        raise RuntimeError(f"Telegram recusou a mensagem ({resposta.status_code}): {motivo}")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main() -> None:
    modo_teste = "--teste" in sys.argv
    config = json.loads(ARQUIVO_CONFIG.read_text(encoding="utf-8"))
    vistos = set(json.loads(ARQUIVO_VISTOS.read_text())) if ARQUIVO_VISTOS.exists() else set()

    projetos = []
    fontes = [
        ("99Freelas", buscar_99freelas, config["99freelas"]),
        ("Workana", buscar_workana, config["workana"]),
    ]
    for nome, funcao, opcoes in fontes:
        if not opcoes.get("ativo", True):
            continue
        try:
            achados = funcao(opcoes["categoria"], opcoes.get("paginas", 2))
            print(f"{nome}: {len(achados)} projetos lidos")
            projetos += achados
        except Exception as erro:  # um site fora do ar não derruba o outro
            print(f"{nome}: erro ao buscar -> {erro}")

    novos = []
    for projeto in projetos:
        if projeto["id"] in vistos:
            continue
        vistos.add(projeto["id"])
        palavras = combina(projeto, config["palavras_incluir"], config["palavras_excluir"])
        if palavras:
            novos.append((projeto, palavras))

    print(f"{len(novos)} projetos novos que combinam com você")

    if modo_teste:
        for projeto, palavras in novos:
            print("\n" + "-" * 60)
            print(f"[{projeto['site']}] {projeto['titulo']}")
            print(projeto["info"])
            print("Palavras:", ", ".join(palavras))
            print(projeto["link"])
        return

    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        sys.exit("Defina TELEGRAM_TOKEN e TELEGRAM_CHAT_ID (ou rode com --teste).")

    limite = config.get("maximo_por_execucao", 15)
    for projeto, palavras in novos[:limite]:
        enviar_telegram(token, chat_id, montar_mensagem(projeto, palavras))
        time.sleep(1)
    if len(novos) > limite:
        enviar_telegram(token, chat_id, f"… e mais {len(novos) - limite} projetos. Ajuste as palavras-chave para filtrar melhor.")

    ARQUIVO_VISTOS.write_text(json.dumps(sorted(vistos), indent=0))


if __name__ == "__main__":
    main()
