#!/usr/bin/env python3
"""Coletor do Todos os Rios — ronda diária das fontes de programação.

O QUE FAZ
  Visita as fontes do cadastro (dados/fontes.csv) que têm site e guarda, para cada uma,
  um arquivo de texto com o que encontrou, descendo uma escada do mais limpo ao mais bruto:
    1. feed (RSS/Atom) do site;
    2. eventos em dados estruturados (as fichas que os sites embutem para os buscadores);
    3. calendário de eventos do WordPress, quando o site oferece;
    4. texto da página inicial, de até 3 páginas de programação ligadas a ela e de até 10
       páginas de eventos individuais ligadas a essas (onde costumam estar hora e preço).
  Não interpreta nada: só recolhe. A redação das fichas e a dupla checagem vêm depois.

O QUE NÃO FAZ
  Não instala nada, não apaga nada, não lê nenhum arquivo do computador além dos seus
  próprios, não envia dados a lugar nenhum. Só faz visitas de leitura a sites públicos e
  grava a pasta de saída e um arquivo .zip ao lado dela.

BOAS MANEIRAS
  Identifica-se como TodosOsRiosBot, com o endereço do projeto. Obedece às regras que cada site
  publica para leitores automáticos (robots.txt). Faz poucas visitas por site, com pausa.

USO
  Na nuvem (serviço de automação do GitHub), todo dia:
      python3 ferramentas/coleta/coletar.py
  No computador da coordenação editorial, para as fontes que recusam a nuvem:
      python coletar.py
  (sem nada mais: ele busca sozinho a lista de fontes pendentes no repositório do projeto
  e deixa um arquivo coleta-todososrios-pc-AAAA-MM-DD.zip na mesma pasta do script)

  Opções:  --todas         visita todas as fontes, não só as pendentes (no computador)
           --so F019,F051  visita só as fontes indicadas
Só usa a biblioteca padrão do Python (3.9 ou mais recente).
"""
import argparse, csv, html, io, json, os, re, ssl, sys, time, zipfile
import urllib.error, urllib.request, urllib.robotparser
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse

AGENTE = "TodosOsRiosBot/0.3 (agenda cultural aberta do Rio de Janeiro; +https://todososrios.com.br/; abreterio@gmail.com)"
REPO_BRUTO = "https://raw.githubusercontent.com/miguelbconde/todososrios/main/"
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
NO_REPOSITORIO = os.path.exists(os.path.join(RAIZ, "dados", "fontes.csv"))

ESPERA = 25              # segundos por visita
MAX_PAGINA = 14_000      # caracteres de texto guardados por página
MAX_PAGINAS_PROG = 3     # páginas de listagem (programação, agenda...) seguidas a partir da inicial
MAX_DETALHES = 10        # páginas de eventos individuais seguidas a partir das listagens
MAX_DETALHE = 6_000      # caracteres guardados por página de evento
MAX_ITENS = 40           # itens por feed ou por calendário
DIAS_FEED = 45           # itens de feed mais antigos que isso ficam de fora
PAUSA = 1.0              # segundos entre visitas ao mesmo site

# Endereços corrigidos em relação ao cadastro (o cadastro será acertado depois de confirmados)
CORRECOES = {
    "F158": "http://imperator.rj.gov.br/",
}
# Fontes que só entram com autorização expressa da coordenação editorial
EM_ESPERA = {
    "cultura.sescrio.org.br": "lido pela agenda dedicada (agendas.py), desde 22/11/2026",
    "sescrio.org.br": "lido pela agenda dedicada (agendas.py), desde 22/11/2026",
    "www.sescrio.org.br": "lido pela agenda dedicada (agendas.py), desde 22/11/2026",
}
PROG = re.compile(r"program|agenda|evento|espet[aá]culo|em[-_ ]?cartaz|exposi[cç]|shows?\b|calend[aá]rio|temporada|"
                  r"concerto|cinema|sess[oõ]es|o[-_ ]que[-_ ]fazer|acontece|atra[cç][oõ]es|ingressos|pe[cç]as|mostras?", re.I)
NAO_PROG = re.compile(r"\.(pdf|jpe?g|png|gif|zip|docx?|mp[34])($|\?)|/(tag|categoria|category|author|autor)/|wp-login|"
                      r"facebook\.|instagram\.|twitter\.|youtube\.|whatsapp|mailto:|tel:|#$|/feed/?$|politica|privacidade|"
                      r"contato|imprensa|trabalhe|edita(l|is)|licita|transpar|ouvidoria|loja|carrinho|login|cadastro", re.I)

try:  # no Windows, usa os certificados do sistema (evita CERTIFICATE_VERIFY_FAILED); opcional
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass
for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ------------------------------------------------------------------ rede
def _pedir(url, limite):
    req = urllib.request.Request(url, headers={
        "User-Agent": AGENTE, "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.6"})
    with urllib.request.urlopen(req, timeout=ESPERA, context=ssl.create_default_context()) as r:
        corpo = r.read(limite)
        return r.status, r.geturl(), r.headers.get("Content-Type", ""), corpo.decode(r.headers.get_content_charset() or "utf-8", "replace")


def baixar(url, limite=900_000):
    """Devolve (código, endereço final, tipo, texto). Código 0 = não houve resposta.
    Se o endereço não responde, tenta as variações com e sem "www."."""
    p = urlparse(url)
    variacoes = [url]
    if p.netloc.startswith("www."):
        variacoes.append(url.replace("://www.", "://", 1))
    else:
        variacoes.append(url.replace("://", "://www.", 1))
    erro = ""
    for n, u in enumerate(variacoes):
        try:
            return _pedir(u, limite)
        except urllib.error.HTTPError as e:
            return e.code, u, "", ""
        except Exception as e:
            erro = type(e).__name__ + ": " + str(e)[:140]
            if n == 0 and not any(k in erro for k in ("Name or service", "No address", "getaddrinfo", "CERTIFICATE", "timed out", "refused", "reset")):
                break
    return 0, url, "", erro


_ROBOTS = {}
def permitido(url):
    """True/False conforme o robots.txt do site; True se o site não publica regras."""
    base = "{0.scheme}://{0.netloc}".format(urlparse(url))
    if base not in _ROBOTS:
        st, _, _, txt = baixar(base + "/robots.txt", 200_000)
        rp = None
        if st == 200 and "<html" not in txt[:300].lower():
            rp = urllib.robotparser.RobotFileParser(); rp.parse(txt.splitlines())
        _ROBOTS[base] = rp
    rp = _ROBOTS[base]
    return True if rp is None else rp.can_fetch("TodosOsRiosBot", url)


# ------------------------------------------------------------------ leitura
def texto_limpo(h, limite=None):
    h = re.sub(r"<(script|style|noscript|svg|iframe|template)\b[^>]*>.*?</\1>", " ", h or "", flags=re.S | re.I)
    h = re.sub(r"<!--.*?-->", " ", h, flags=re.S)
    h = re.sub(r"<(br|/p|/div|/li|/h[1-6]|/tr|/section|/article|/header|/footer)\b[^>]*>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    h = html.unescape(h)
    linhas = [re.sub(r"[ \t\xa0​]+", " ", l).strip() for l in h.split("\n")]
    saida, anterior = [], None
    for l in linhas:
        if l and l != anterior:
            saida.append(l)
        anterior = l
    t = "\n".join(saida)
    if limite and len(t) > limite:
        t = t[:limite].rsplit("\n", 1)[0] + "\n[… cortado]"
    return t


def links_de_programacao(h, endereco):
    host = urlparse(endereco).netloc.replace("www.", "")
    vistos, achados = {endereco.rstrip("/")}, []
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', h, re.S | re.I):
        link = urljoin(endereco, html.unescape(m.group(1)).strip()).split("#")[0]
        rotulo = texto_limpo(m.group(2))[:80]
        if urlparse(link).netloc.replace("www.", "") != host or NAO_PROG.search(link):
            continue
        chave = link.rstrip("/")
        if chave in vistos:
            continue
        caminho = urlparse(link).path
        if PROG.search(caminho) or PROG.search(rotulo):
            vistos.add(chave)
            # páginas de listagem (caminho curto) primeiro; fichas individuais depois
            achados.append((caminho.strip("/").count("/"), len(caminho), link, rotulo))
    achados.sort()
    return [(l, r) for _, _, l, r in achados[:MAX_PAGINAS_PROG]]


def links_de_detalhe(h, endereco, ja_vistos):
    """Links para páginas de eventos individuais, na ordem em que aparecem na listagem."""
    host = urlparse(endereco).netloc.replace("www.", "")
    fundo = urlparse(endereco).path.strip("/").count("/")
    saida = []
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\']', h, re.I):
        link = urljoin(endereco, html.unescape(m.group(1)).strip()).split("#")[0]
        chave = link.rstrip("/")
        caminho = urlparse(link).path
        if urlparse(link).netloc.replace("www.", "") != host or NAO_PROG.search(link) or chave in ja_vistos:
            continue
        if caminho.strip("/").count("/") > fundo or (PROG.search(caminho) and len(caminho.strip("/")) > 12):
            ja_vistos.add(chave)
            saida.append(link)
    return saida


def feeds_da_pagina(h, endereco):
    saida = []
    for tag in re.findall(r'<link\b[^>]+>', h, re.I):
        if re.search(r'application/(rss|atom)\+xml', tag, re.I):
            m = re.search(r'href=["\']([^"\']+)', tag)
            if m and "comments" not in m.group(1):
                saida.append(urljoin(endereco, html.unescape(m.group(1))))
    return list(dict.fromkeys(saida))[:2]


def _txt(no, *nomes):
    for n in nomes:
        for filho in no.iter():
            if filho.tag.split("}")[-1] == n and (filho.text or "").strip():
                return filho.text.strip()
    return ""


def itens_do_feed(xml):
    try:
        raiz = ET.fromstring(xml.encode("utf-8", "replace"))
    except ET.ParseError:
        return None
    limite = datetime.now(timezone.utc) - timedelta(days=DIAS_FEED)
    itens = []
    for no in raiz.iter():
        if no.tag.split("}")[-1] not in ("item", "entry"):
            continue
        titulo = texto_limpo(_txt(no, "title"))
        link = _txt(no, "link")
        if not link:
            for f in no:
                if f.tag.split("}")[-1] == "link" and f.get("href"):
                    link = f.get("href"); break
        quando = _txt(no, "pubDate", "published", "updated", "date")
        dt = None
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = datetime.strptime(quando[:31].strip(), fmt); break
            except ValueError:
                continue
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt and dt < limite:
            continue
        resumo = texto_limpo(_txt(no, "encoded", "description", "summary", "content"), 700).replace("\n", " ")
        if titulo:
            itens.append((dt.strftime("%Y-%m-%d") if dt else "sem data", titulo, link, resumo))
        if len(itens) >= MAX_ITENS:
            break
    return itens


def eventos_estruturados(h):
    achados = []
    def andar(x):
        if isinstance(x, dict):
            tipo = x.get("@type")
            tipos = tipo if isinstance(tipo, list) else [tipo]
            if any(isinstance(t, str) and t.endswith("Event") or t == "Festival" for t in tipos):
                local = x.get("location") or {}
                if isinstance(local, list):
                    local = local[0] if local else {}
                oferta = x.get("offers") or {}
                if isinstance(oferta, list):
                    oferta = oferta[0] if oferta else {}
                achados.append(" | ".join(str(v) for v in [
                    x.get("name", ""), "início " + str(x.get("startDate", "?")), "fim " + str(x.get("endDate", "?")),
                    (local.get("name", "") if isinstance(local, dict) else str(local)),
                    ("preço " + str(oferta.get("price", "?")) if isinstance(oferta, dict) else ""),
                    x.get("url", ""), texto_limpo(str(x.get("description", "")), 400).replace("\n", " ")] if v))
            for v in x.values():
                andar(v)
        elif isinstance(x, list):
            for v in x:
                andar(v)
    for bloco in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', h, re.I | re.S):
        try:
            andar(json.loads(bloco.strip()))
        except Exception:
            continue
    return list(dict.fromkeys(achados))[:MAX_ITENS]


def calendario_wordpress(base):
    hoje = date.today().isoformat()
    st, _, _, j = baixar(f"{base}/wp-json/tribe/events/v1/events?per_page={MAX_ITENS}&start_date={hoje}", 1_500_000)
    if st != 200:
        return None
    try:
        dados = json.loads(j)
    except Exception:
        return None
    saida = []
    for e in dados.get("events", []):
        lugar = e.get("venue") or {}
        saida.append(" | ".join(str(v) for v in [
            texto_limpo(e.get("title", "")), "início " + str(e.get("start_date", "?")), "fim " + str(e.get("end_date", "?")),
            (lugar.get("venue", "") if isinstance(lugar, dict) else ""), "preço " + str(e.get("cost", "") or "não informado"),
            e.get("url", ""), texto_limpo(e.get("description", ""), 500).replace("\n", " ")] if v))
    return saida


# ------------------------------------------------------------------ uma fonte
def coletar(grupo):
    """grupo = fontes do cadastro que dividem o mesmo endereço (ex.: unidades de uma rede)."""
    f = grupo[0]
    url = CORRECOES.get(f["id"], f["url"].strip())
    if not url.startswith("http"):
        url = "https://" + url
    ids = ", ".join(x["id"] for x in grupo)
    nomes = "; ".join(x["nome"] for x in grupo)
    r = {"ids": [x["id"] for x in grupo], "nome": nomes, "url": url, "regioes": sorted({x["regiao"] for x in grupo}),
         "degraus": [], "caracteres": 0}
    partes = [f"# {ids} | {nomes}", f"# endereço: {url}", f"# coletado em {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC", ""]

    host = urlparse(url).netloc.replace("www.", "")
    if host in EM_ESPERA:
        r["situacao"] = "em espera: " + EM_ESPERA[host]
        return r, None
    if not permitido(url):
        r["situacao"] = "o site proíbe leitura automática (robots.txt)"
        return r, None
    st, final, tipo, h = baixar(url)
    if st != 200:
        r["situacao"] = ("não respondeu: " + h) if st == 0 else f"recusou a visita (código {st})"
        return r, None
    r["url_final"] = final
    base = "{0.scheme}://{0.netloc}".format(urlparse(final))

    # degrau 1: feed
    feeds = feeds_da_pagina(h, final)
    if not feeds and ("wp-content" in h or "wp-json" in h):
        feeds = [base + "/feed/"]
    for fd in feeds:
        time.sleep(PAUSA)
        if not permitido(fd):
            continue
        s2, _, _, x = baixar(fd, 1_500_000)
        itens = itens_do_feed(x) if s2 == 200 else None
        if itens:
            r["degraus"].append(f"feed ({len(itens)} itens)")
            partes += [f"## FEED {fd}"] + [f"- {d} | {t} | {l} | {res}" for d, t, l, res in itens] + [""]

    # degrau 2: eventos em dados estruturados
    ev = eventos_estruturados(h)

    # degrau 3: calendário de eventos do WordPress
    if "wp-content" in h or "wp-json" in h:
        time.sleep(PAUSA)
        cal = calendario_wordpress(base) if permitido(base + "/wp-json/tribe/events/v1/events") else None
        if cal:
            r["degraus"].append(f"calendário WordPress ({len(cal)} eventos)")
            partes += ["## EVENTOS (calendário do site)"] + ["- " + c for c in cal] + [""]

    # degrau 4: texto das páginas (inicial, listagens e eventos individuais)
    paginas = [(final, "página inicial", h, MAX_PAGINA)]
    vistos = {final.rstrip("/")}
    detalhes = []
    for link, rotulo in links_de_programacao(h, final):
        time.sleep(PAUSA)
        if link.rstrip("/") in vistos or not permitido(link):
            continue
        vistos.add(link.rstrip("/"))
        s3, f3, t3, h3 = baixar(link)
        if s3 == 200 and "html" in (t3 or "html").lower():
            paginas.append((f3, "listagem: " + (rotulo or "programação"), h3, MAX_PAGINA))
            ev += eventos_estruturados(h3)
            detalhes += links_de_detalhe(h3, f3, vistos)
    if len(paginas) == 1:      # nenhuma listagem achada: os eventos podem estar ligados direto na inicial
        detalhes = links_de_detalhe(h, final, vistos)
        detalhes = [l for l in detalhes if PROG.search(urlparse(l).path)]
    for link in detalhes[:MAX_DETALHES]:
        time.sleep(PAUSA)
        if not permitido(link):
            continue
        s4, f4, t4, h4 = baixar(link, 500_000)
        if s4 == 200 and "html" in (t4 or "html").lower():
            paginas.append((f4, "evento", h4, MAX_DETALHE))
            ev += eventos_estruturados(h4)
    ev = list(dict.fromkeys(ev))[:MAX_ITENS]
    if ev:
        r["degraus"].append(f"dados estruturados ({len(ev)} eventos)")
        partes += ["## EVENTOS (dados estruturados da página)"] + ["- " + e for e in ev] + [""]
    com_datas = 0
    # menu e rodapé: linhas da página inicial que se repetem em quase todas as páginas do site.
    # (Valores curtos como "Livre" ou "20h" podem se repetir entre eventos e NÃO são descartados por isso.)
    from collections import Counter
    textos = [texto_limpo(hh).split("\n") for _, _, hh, _ in paginas]
    frequencia = Counter(l for linhas in textos for l in set(linhas))
    da_inicial = set(textos[0])
    dado = re.compile(r"\d|livre|anos|r\$|gr[aá]t|gratuit|entrada|ingresso", re.I)   # isto nunca é descartado
    repetidas = {l for l, n in frequencia.items()
                 if l in da_inicial and n >= 0.9 * len(paginas) and len(l) < 200 and not dado.search(l)} if len(paginas) >= 3 else set()
    for (endereco, rotulo, hh, teto), linhas in zip(paginas, textos):
        primeira = endereco == paginas[0][0]
        novas = linhas if primeira else [l for l in linhas if l not in repetidas]
        t = "\n".join(novas)
        if len(t) > teto:
            t = t[:teto].rsplit("\n", 1)[0] + "\n[… cortado]"
        com_datas += len(re.findall(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b|\b\d{1,2} de (?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b|\b\d{1,2}h(?:\d{2})?\b", t, re.I))
        partes += [f"## PÁGINA ({rotulo}) — {endereco}", t, ""]
    r["degraus"].append(f"texto de {len(paginas)} página(s)")
    r["paginas"] = [p[0] for p in paginas]
    r["mencoes_de_data"] = com_datas
    texto = "\n".join(partes)
    r["caracteres"] = len(texto)
    tem_dado = any(not d.startswith("texto") for d in r["degraus"])
    r["situacao"] = "coletada" if (tem_dado or com_datas >= 4) else "coletada, mas sem datas à vista (a programação pode ser carregada depois)"
    return r, texto


# ------------------------------------------------------------------ principal
def carregar_fontes():
    if NO_REPOSITORIO:
        return list(csv.DictReader(open(os.path.join(RAIZ, "dados", "fontes.csv"), encoding="utf-8-sig"), delimiter=";"))
    st, _, _, t = baixar(REPO_BRUTO + "dados/fontes.csv", 2_000_000)
    if st != 200:
        sys.exit("Não consegui baixar a lista de fontes do repositório do projeto. Confira a internet e tente de novo.")
    return list(csv.DictReader(io.StringIO(t.lstrip("﻿")), delimiter=";"))


def pendentes_da_nuvem():
    """ids das fontes que a nuvem não conseguiu ler na última ronda."""
    st, _, _, t = baixar(REPO_BRUTO + "dados/coleta/resumo.json", 2_000_000)
    if st != 200:
        return None
    try:
        dados = json.loads(t)
    except Exception:
        return None
    return {i for r in dados["fontes"] if r["situacao"].startswith(("não respondeu", "recusou")) for i in r["ids"]}


def main():
    ap = argparse.ArgumentParser(description="Ronda semanal das fontes do Todos os Rios.")
    ap.add_argument("--todas", action="store_true", help="visita todas as fontes, não só as pendentes")
    ap.add_argument("--so", help="ids separados por vírgula, ex.: F019,F051")
    args = ap.parse_args()

    fontes = [f for f in carregar_fontes() if f["camada"] == "Núcleo" and f["metodo"].startswith("Site")]
    origem = "nuvem" if NO_REPOSITORIO and os.environ.get("GITHUB_ACTIONS") else "pc"
    if args.so:
        quero = {x.strip().upper() for x in args.so.split(",")}
        fontes = [f for f in fontes if f["id"] in quero]
    elif origem == "pc" and not args.todas:
        pend = pendentes_da_nuvem()
        if pend is None:
            print("Não achei o resumo da ronda da nuvem; vou visitar todas as fontes.")
        else:
            fontes = [f for f in fontes if f["id"] in pend]
            print(f"A nuvem não conseguiu ler {len(fontes)} fontes. Vou tentar essas a partir deste computador.")

    grupos = {}
    for f in fontes:
        grupos.setdefault(CORRECOES.get(f["id"], f["url"].strip()), []).append(f)
    hoje = date.today().isoformat()
    pasta = os.path.join(RAIZ if NO_REPOSITORIO else AQUI, "coleta-bruta" if origem == "nuvem" else f"coleta-todososrios-pc-{hoje}")
    os.makedirs(pasta, exist_ok=True)

    t0 = time.time()
    resultados = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        for n, (r, texto) in enumerate(ex.map(coletar, grupos.values()), 1):
            if texto:
                r["arquivo"] = r["ids"][0] + ".txt"
                open(os.path.join(pasta, r["arquivo"]), "w", encoding="utf-8").write(texto)
            resultados.append(r)
            print(f"  [{n:>3}/{len(grupos)}] {r['situacao'][:60]:<60} {r['nome'][:50]}", flush=True)

    resumo = {"origem": origem, "feito_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
              "segundos": round(time.time() - t0), "fontes": resultados}
    json.dump(resumo, open(os.path.join(pasta, "resumo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    from collections import Counter
    conta = Counter(r["situacao"].split(":")[0].split(" (")[0] for r in resultados)
    if origem == "nuvem":   # no repositório fica só o resumo, nunca o texto dos sites
        os.makedirs(os.path.join(RAIZ, "dados", "coleta"), exist_ok=True)
        json.dump(resumo, open(os.path.join(RAIZ, "dados", "coleta", "resumo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        linhas = ["# Ronda das fontes — resumo", "", f"Feita em {resumo['feito_em']}, em {resumo['segundos']} segundos, no serviço de automação do GitHub.",
                  "O texto recolhido dos sites não entra na linha principal do repositório nem no site: fica num ramo temporário (coleta-bruta), substituído a cada ronda, só para a redação das fichas.", "", "## Situação", ""]
        linhas += [f"- {k}: **{v}**" for k, v in conta.most_common()]
        linhas += ["", "## Fonte a fonte", "", "| Fonte | Situação | O que veio |", "|---|---|---|"]
        linhas += [f"| {r['nome'][:70]} | {r['situacao']} | {', '.join(r['degraus'])} |" for r in sorted(resultados, key=lambda x: (x["situacao"], x["nome"]))]
        open(os.path.join(RAIZ, "dados", "coleta", "resumo.md"), "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    else:
        destino = os.path.join(AQUI, f"coleta-todososrios-pc-{hoje}.zip")
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
            for nome in sorted(os.listdir(pasta)):
                z.write(os.path.join(pasta, nome), nome)
        print(f"\nPronto. Anexe este arquivo na conversa com o Claude:\n  {destino}")
    print("\nResumo:", dict(conta), f"· {resumo['segundos']} s")


if __name__ == "__main__":
    main()
