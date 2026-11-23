#!/usr/bin/env python3
"""Gerador do Todos os Rios — Agenda cultural do Rio de Janeiro.

Lê a base de uma edição (dados/edicoes/<id>/eventos.json) e, se existir, o relatório
do conferente (conferencia.json). Aplica as conferências mecânicas e gera:
  docs/index.html            site (um único arquivo, sem rastreadores)
  docs/calendarios/*.ics     calendários assináveis (geral, por área, por região, grátis)
  docs/dados/eventos.json    dados abertos (ODbL)
  docs/dados/eventos.csv
  dados/edicoes/<id>/relatorio.md  relatório de exceções da edição
Uso: python3 ferramentas/gerar.py 2026-11-15
"""
import hashlib, csv, json, os, re, sys, unicodedata, datetime as dt
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AREAS = ["Música", "Teatro", "Artes Visuais", "Cinema", "Livros & Debates", "Festas & Feiras", "Infantil"]
REGIOES = ["Centro", "Zona Sul", "Zona Sudoeste", "Zona Norte", "Zona Oeste"]
POPULAR = 40  # teto do preço popular (inteira), decisão editorial de 15/11/2026


def slug(s):
    s = unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def faixa(e):
    if e["gratis"]:
        return "gratis"
    if e["preco_max"] is None:
        return "nao_informado"
    inteira = e["preco_max"]
    if inteira <= POPULAR:
        return "popular"
    return "ate80" if inteira <= 80 else "acima80"


def conferencia_mecanica(ed, eventos):
    """Regras sem IA. Devolve lista de (id, problema, gravidade)."""
    ini, fim = ed["inicio"], ed["fim"]
    probs, vistos = [], {}
    for e in eventos:
        i = e["id"]
        if not e["endereco"] or not e["bairro"]:
            probs.append((i, "Endereço ou bairro ausente", "alta"))
        if e["regiao"] not in REGIOES:
            probs.append((i, "Região inválida ou ausente", "alta"))
        if not set(e["areas"]) <= set(AREAS):
            probs.append((i, f"Área fora do padrão: {e['areas']}", "alta"))
        if e["tipo"] == "evento":
            if not e["sessoes"]:
                probs.append((i, "Evento sem sessões", "alta"))
            for s in e["sessoes"]:
                if not (ini <= s["data"] <= fim):
                    probs.append((i, f"Sessão fora da edição: {s['data']}", "alta"))
                if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", s["hora"] or ""):
                    probs.append((i, f"Horário inválido: {s['hora']}", "alta"))
                elif not ("08:00" <= s["hora"] <= "23:59"):
                    probs.append((i, f"Horário incomum: {s['hora']}", "media"))
        if e["gratis"] and (e["preco_max"] or 0) > 0:
            probs.append((i, "Marcado como grátis, mas tem preço", "alta"))
        if not e["gratis"] and e["preco_max"] is None:
            probs.append((i, "Preço não informado na fonte", "baixa"))
        if e["preco_min"] is not None and e["preco_max"] is not None and e["preco_min"] > e["preco_max"]:
            probs.append((i, "Preço mínimo maior que o máximo", "alta"))
        if not e["link"].startswith("http"):
            probs.append((i, "Link oficial ausente", "media"))
        chave = (slug(e["titulo"]), slug(e["local"]))
        if chave in vistos:
            probs.append((i, f"Possível duplicata de {vistos[chave]}", "alta"))
        vistos[chave] = i
    return probs


PUBLICOS = ("municipal", "Municipal", "Arena", "Areninha", "Biblioteca", "Muhcab", "Museu", "Memorial",
            "Centro Cultural", "Centro Municipal", "Centro da Música", "Centro Coreográfico", "Cidade das Artes",
            "Teatro de", "Sesc", "CCBB", "Espaço Cultural")


# "A boa" (decisão de 23/11/2026): 3 destaques por dia, cada um numa vaga
#   1. o show do dia: o melhor de Música, pela força da atração, sem amarra de preço ou região;
#   2. na rua: uma atividade ao ar livre ou em espaço público, de qualquer seção;
#   3. a seção da vez: roda, dia a dia, entre as outras seções (ordem abaixo); se a seção do dia
#      não tem opção conferida, passa para a seguinte.
# Território: pelo menos um dos três fora do eixo Centro–Zona Sul, quando o dia oferece.
MAX_BOA = 3
RODIZIO = ("Teatro", "Artes Visuais", "Cinema", "Livros & Debates", "Festas & Feiras", "Infantil")
EIXO = ("Centro", "Zona Sul")
MES_MIN, MES_MAX = 3, 4  # "As boas do mês" (22/11/2026): 3 ou 4 grandes nomes e eventos de compra antecipada
MES_MAX_DATAS = 4  # (23/11/2026) só atrações com poucas apresentações; temporada longa não entra


def secao_da_vez(dia, pool):
    """A seção do rodízio no dia; se ela não tem opção no dia, a seguinte que tiver."""
    i0 = dt.date.fromisoformat(dia).toordinal() % len(RODIZIO)
    for k in range(len(RODIZIO)):
        s = RODIZIO[(i0 + k) % len(RODIZIO)]
        if any(s in e["areas"] for e in pool):
            return s
    return None


def validar_destaques(eventos, destaques):
    """Regras públicas de curadoria. Uma regra só é cobrada se o dia oferece opções para cumpri-la."""
    por_id = {e["id"]: e for e in eventos}
    alertas = []
    for dia, lista in destaques["dias"].items():
        pool = [e for e in eventos if e["tipo"] == "evento" and e["status"] == "conferido"
                and any(x["data"] == dia for x in e["sessoes"])]
        esc = []
        for d in lista:
            e = por_id.get(d["id"])
            if not e:
                alertas.append((dia, f"ID inexistente: {d['id']}")); continue
            if e["status"] != "conferido":
                alertas.append((dia, f"“{e['titulo']}” não está conferido e não pode ser destaque"))
            if not any(x["data"] == dia for x in e["sessoes"]):
                alertas.append((dia, f"“{e['titulo']}” não tem sessão neste dia"))
            esc.append(e)
        if len(lista) > MAX_BOA:
            alertas.append((dia, f"{len(lista)} destaques; o máximo é {MAX_BOA}"))
        if any("Música" in e["areas"] for e in pool) and not any("Música" in e["areas"] for e in esc):
            alertas.append((dia, "Falta o show do dia (o dia tinha música)"))
        if any(e.get("na_rua") for e in pool) and not any(e.get("na_rua") for e in esc):
            alertas.append((dia, "Falta um destaque na rua (o dia oferecia)"))
        vez = secao_da_vez(dia, pool)
        if vez and not any(vez in e["areas"] for e in esc):
            alertas.append((dia, f"Falta a seção da vez: {vez}"))
        if any(e["regiao"] not in EIXO for e in pool) and esc and all(e["regiao"] in EIXO for e in esc):
            alertas.append((dia, "Nenhum destaque fora do eixo Centro–Zona Sul (o dia oferecia)"))
        locais = [e["local"] for e in esc]
        if len(set(locais)) < len(locais):
            alertas.append((dia, "Mais de um destaque no mesmo espaço"))
    mes = destaques.get("mes", [])
    if mes and not MES_MIN <= len(mes) <= MES_MAX:
        alertas.append(("mês", f"As boas do mês têm {len(mes)} escolhas; o padrão é de {MES_MIN} a {MES_MAX}"))
    for d in mes:
        e = por_id.get(d["id"])
        if e and e["status"] != "conferido":
            alertas.append(("mês", f"“{e['titulo']}” não está conferido e não pode estar nas boas do mês"))
        if e and e["tipo"] == "evento" and len({x["data"] for x in e["sessoes"]}) > MES_MAX_DATAS:
            alertas.append(("mês", f"“{e['titulo']}” tem {len({x['data'] for x in e['sessoes']})} datas: temporada longa não entra nas boas do mês"))
    return alertas


# ---------------------------------------------------------------- calendários
def ics_escape(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def ics_fold(linha):
    b = linha.encode("utf-8")
    if len(b) <= 74:
        return linha
    partes, atual = [], ""
    for ch in linha:
        if len((atual + ch).encode("utf-8")) > 73:
            partes.append(atual)
            atual = " " + ch
        else:
            atual += ch
    partes.append(atual)
    return "\r\n".join(partes)


def utc(data, hora):  # Rio: UTC−3, sem horário de verão
    t = dt.datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M") + dt.timedelta(hours=3)
    return t.strftime("%Y%m%dT%H%M%SZ")


def preco_legivel(e):
    if e["gratis"]:
        return e["preco_texto"] or "Grátis"
    return e["preco_texto"] or "Preço não informado"


def ics(nome, eventos, carimbo, so_sessoes=None):
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Todos os Rios//Agenda cultural do Rio de Janeiro//PT-BR",
         "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{ics_escape(nome)}",
         "X-WR-TIMEZONE:America/Sao_Paulo", "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
         "X-PUBLISHED-TTL:PT12H"]
    for e in eventos:
        if e["tipo"] != "evento":
            continue
        for k, s in enumerate(e["sessoes"]):
            if so_sessoes is not None and (e["id"], s["data"]) not in so_sessoes:
                continue
            ini = utc(s["data"], s["hora"])
            fim = (dt.datetime.strptime(ini, "%Y%m%dT%H%M%SZ") + dt.timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")
            desc = f"{e['sinopse']}\n\n{preco_legivel(e)}"
            if e["classificacao"]:
                desc += f" · {e['classificacao']}"
            if e.get("status") == "a_confirmar":
                desc += "\n\nATENÇÃO: informação a confirmar na fonte."
            if e.get("aviso") == "dias":
                desc += "\n\nATENÇÃO: a fonte não informa os dias exatos da temporada; listamos de quinta a domingo. Confira antes de ir."
            desc += f"\n\nFonte: {e['link']}\nTodos os Rios — agenda cultural aberta do Rio"
            L += ["BEGIN:VEVENT", f"UID:{e['id']}-{k}@todososrios.rio", f"DTSTAMP:{carimbo}",
                  f"DTSTART:{ini}", f"DTEND:{fim}", f"SUMMARY:{ics_escape(e['titulo'])}",
                  f"LOCATION:{ics_escape(e['local'] + ', ' + e['endereco'] + ' – ' + e['bairro'])}",
                  f"DESCRIPTION:{ics_escape(desc)}", f"URL:{e['link']}",
                  f"CATEGORIES:{ics_escape(','.join(e['areas']))}", "END:VEVENT"]
    L.append("END:VCALENDAR")
    return "\r\n".join(ics_fold(x) for x in L) + "\r\n"


# ---------------------------------------------------------------- buscadores
# Endereço público do site. Trocar aqui quando o domínio próprio estiver no ar.
SITE = "https://todososrios.com.br/"  # endereço principal desde 23/11/2026 (o .rio, quando sair, só encaminha para cá)
URL_LANG = {"pt": SITE, "en": SITE + "en/", "es": SITE + "es/"}
CAB = {
    "pt": ("Todos os Rios · O que fazer no Rio hoje — agenda cultural gratuita e aberta",
           "O que fazer no Rio de Janeiro hoje e nesta semana: shows, rodas de samba, teatro, exposições, cinema e programação infantil em todas as regiões da cidade. Grátis e a preço popular sempre sinalizados."),
    "en": ("Todos os Rios · What's on in Rio de Janeiro this week — free cultural events",
           "Things to do in Rio de Janeiro today and this week: live music, samba, theatre, exhibitions, cinema and family events across the whole city. Free and low-cost events clearly marked."),
    "es": ("Todos os Rios · Qué hacer en Río de Janeiro esta semana — agenda cultural gratuita",
           "Qué hacer en Río de Janeiro hoy y esta semana: conciertos, rodas de samba, teatro, exposiciones, cine y actividades para niños en toda la ciudad. Lo gratuito y lo barato, siempre señalado."),
}
TIPO_EVENTO = {"Música": "MusicEvent", "Teatro": "TheaterEvent", "Artes Visuais": "ExhibitionEvent", "Cinema": "ScreeningEvent",
               "Livros & Debates": "LiteraryEvent", "Festas & Feiras": "Festival", "Infantil": "ChildrensEvent"}


def eventos_jsonld(eventos, lang):
    """Marcação schema.org dos eventos da agenda (a grade de cinema fica de fora). Uma entrada por sessão."""
    itens = []
    for e in eventos:
        if e.get("automatica"):
            continue
        desc = (lang != "pt" and e.get("sinopse_" + lang)) or e.get("sinopse", "")
        base = {"@type": TIPO_EVENTO.get(e["areas"][0], "Event"), "name": e["titulo"], "description": desc,
                "eventStatus": "https://schema.org/EventScheduled",
                "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                "location": {"@type": "Place", "name": e["local"],
                             "address": {"@type": "PostalAddress", "streetAddress": e["endereco"], "addressLocality": "Rio de Janeiro",
                                         "addressRegion": "RJ", "addressCountry": "BR"}},
                "url": URL_LANG[lang], "inLanguage": "pt-BR"}
        if e["bairro"]:
            base["location"]["address"]["streetAddress"] = f"{e['endereco']}, {e['bairro']}".strip(", ")
        if e["gratis"]:
            base["isAccessibleForFree"] = True
            base["offers"] = {"@type": "Offer", "price": 0, "priceCurrency": "BRL", "url": e["link"] or URL_LANG[lang]}
        elif e.get("preco_min") is not None:
            base["offers"] = {"@type": "Offer", "price": e["preco_min"], "priceCurrency": "BRL", "url": e["link"] or URL_LANG[lang]}
        if e["tipo"] == "evento":
            for s in e["sessoes"]:
                itens.append({**base, "startDate": f"{s['data']}T{s['hora']}:00-03:00"})
        elif e["cartaz"] and e["cartaz"].get("inicio") and e["cartaz"].get("fim"):
            itens.append({**base, "startDate": e["cartaz"]["inicio"], "endDate": e["cartaz"]["fim"]})
    return itens


def cabeca(lang, ed, eventos):
    t, d = CAB[lang]
    h = html_esc = lambda x: x.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    alt = "".join(f'<link rel="alternate" hreflang="{hl}" href="{URL_LANG[l]}">\n' for l, hl in (("pt", "pt-BR"), ("en", "en"), ("es", "es")))
    alt += f'<link rel="alternate" hreflang="x-default" href="{URL_LANG["pt"]}">\n'
    site = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": "Todos os Rios", "url": SITE, "inLanguage": ["pt-BR", "en", "es"],
         "description": CAB[lang][1], "license": "https://opendatacommons.org/licenses/odbl/1-0/"}] + eventos_jsonld(eventos, lang)}
    jsonld = json.dumps(site, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return (f"<title>{h(t)}</title>\n<meta name=\"description\" content=\"{h(d)}\">\n"
            f'<link rel="canonical" href="{URL_LANG[lang]}">\n{alt}'
            f'<meta property="og:type" content="website">\n<meta property="og:site_name" content="Todos os Rios">\n'
            f'<meta property="og:title" content="{h(t)}">\n<meta property="og:description" content="{h(d)}">\n'
            f'<meta property="og:url" content="{URL_LANG[lang]}">\n'
            f'<meta property="og:locale" content="{ {"pt": "pt_BR", "en": "en_US", "es": "es_ES"}[lang] }">\n'
            f'<script type="application/ld+json">{jsonld}</script>')


def escrever_mapa_do_site(out):
    hoje = dt.date.today().isoformat()
    alts = "".join(f'<xhtml:link rel="alternate" hreflang="{hl}" href="{URL_LANG[l]}"/>' for l, hl in (("pt", "pt-BR"), ("en", "en"), ("es", "es")))
    urls = "".join(f"<url><loc>{URL_LANG[l]}</loc><lastmod>{hoje}</lastmod><changefreq>daily</changefreq>{alts}</url>" for l in ("pt", "en", "es"))
    open(os.path.join(out, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">' + urls + "</urlset>\n")
    open(os.path.join(out, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n")


# ---------------------------------------------------------------- principal
def main(edicao_id):
    pasta = os.path.join(RAIZ, "dados", "edicoes", edicao_id)
    base = json.load(open(os.path.join(pasta, "eventos.json"), encoding="utf-8"))
    ed, eventos = base["edicao"], base["eventos"]
    # traduções das sinopses (dados/traducoes.json, feitas por ferramentas/redacao/traduzir.py); o título nunca é traduzido
    trad_path = os.path.join(RAIZ, "dados", "traducoes.json")
    trad = json.load(open(trad_path, encoding="utf-8")) if os.path.exists(trad_path) else {}
    sem_traducao = []
    for e in eventos:
        t = trad.get(hashlib.sha1(" ".join(e.get("sinopse", "").split()).encode("utf-8")).hexdigest()[:16])
        if t:
            e["sinopse_en"], e["sinopse_es"] = t["en"], t["es"]
        elif e.get("sinopse"):
            sem_traducao.append(e["titulo"])
    cine_path = os.path.join(pasta, "cinema.json")  # fichas automáticas da Ingresso.com (ferramentas/redacao/cinema.py)
    if os.path.exists(cine_path):
        eventos = eventos + json.load(open(cine_path, encoding="utf-8"))["fichas"]

    conf_path = os.path.join(pasta, "conferencia.json")
    conf = json.load(open(conf_path, encoding="utf-8")) if os.path.exists(conf_path) else {"resultado": []}
    mec = conferencia_mecanica(ed, eventos)

    problemas_ia = {}
    for r in conf.get("resultado", []):
        problemas_ia.setdefault(r["id"], []).append(r)
    graves = {i for i, _, g in mec if g == "alta"}
    for e in eventos:
        e["faixa"] = faixa(e)
        ia = [r for r in problemas_ia.get(e["id"], []) if not r.get("resolucao")]
        e["status"] = "a_confirmar" if (ia or e["id"] in graves) else "conferido"

    dest_path = os.path.join(pasta, "destaques.json")
    destaques = json.load(open(dest_path, encoding="utf-8")) if os.path.exists(dest_path) else {"dias": {}}
    for l in list(destaques["dias"].values()) + [destaques.get("mes", [])]:  # o "por que ir" de cada destaque também tem tradução
        for d in l:
            t = trad.get(hashlib.sha1(" ".join(d.get("porque", "").split()).encode("utf-8")).hexdigest()[:16])
            if t:
                d["porque_en"], d["porque_es"] = t["en"], t["es"]
            elif d.get("porque"):
                sem_traducao.append("destaque: " + d["porque"][:40] + "…")
    alertas_dest = validar_destaques([e for e in eventos if not e.get("automatica")], destaques)  # fichas automáticas (cinema) não concorrem à A boa
    sess_dest = {(d["id"], dia) for dia, l in destaques["dias"].items() for d in l}

    out = os.path.join(RAIZ, "docs")
    os.makedirs(os.path.join(out, "calendarios"), exist_ok=True)
    os.makedirs(os.path.join(out, "dados"), exist_ok=True)
    carimbo = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # calendários para assinar: só dois (decisão de 19/11/2026): a boa e todos os eventos.
    # A grade de cinema fica fora dos calendários (seria centenas de sessões por dia).
    agenda = [e for e in eventos if not e.get("automatica")]
    for velho in os.listdir(os.path.join(out, "calendarios")):
        if velho.endswith(".ics") and velho not in ("todososrios-geral.ics", "todososrios-destaques.ics"):
            os.remove(os.path.join(out, "calendarios", velho))
    open(os.path.join(out, "calendarios", "todososrios-geral.ics"), "w", encoding="utf-8", newline="").write(
        ics("Todos os Rios · Todos os eventos", agenda, carimbo))
    open(os.path.join(out, "calendarios", "todososrios-destaques.ics"), "w", encoding="utf-8", newline="").write(
        ics("Todos os Rios · A boa (destaques)", eventos, carimbo, so_sessoes=sess_dest))
    feeds = {"todososrios-destaques.ics": ("Todos os Rios · A boa (destaques)", []), "todososrios-geral.ics": ("Todos os Rios · Todos os eventos", agenda)}

    # dados abertos
    publicos = [{k: v for k, v in e.items() if k != "nota_redacao"} for e in eventos]
    json.dump({"edicao": ed, "licenca": "ODbL 1.0 (dados) · CC BY-SA 4.0 (textos)", "eventos": publicos},
              open(os.path.join(out, "dados", "eventos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(out, "dados", "eventos.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "titulo", "areas", "tipo", "datas_horarios", "local", "endereco", "bairro", "regiao",
                    "preco", "faixa", "classificacao", "acessibilidade", "na_rua", "sinopse", "link", "fonte", "status"])
        for e in eventos:
            dh = " | ".join(f"{s['data']} {s['hora']}" for s in e["sessoes"]) if e["tipo"] == "evento" else \
                f"em cartaz até {e['cartaz']['fim'] or '—'} · {e['cartaz']['horario']}"
            w.writerow([e["id"], e["titulo"], " / ".join(e["areas"]), e["tipo"], dh, e["local"], e["endereco"],
                        e["bairro"], e["regiao"], preco_legivel(e), e["faixa"], e["classificacao"],
                        e["acessibilidade"], "sim" if e.get("na_rua") else "", e["sinopse"], e["link"], e["fonte"], e["status"]])

    # site
    modelo = open(os.path.join(RAIZ, "ferramentas", "modelo.html"), encoding="utf-8").read()
    site_ev = [{k: v for k, v in e.items() if not (e.get("automatica") and k in ("trecho_fonte", "fonte", "link_espaco"))} for e in publicos]
    dados_site = json.dumps({"edicao": ed, "eventos": site_ev, "destaques": destaques["dias"], "destaques_mes": destaques.get("mes", []),
                             "feeds": {k: v[0] for k, v in feeds.items()}}, ensure_ascii=False)
    dados_site = dados_site.replace("</", "<\\/")
    # três versões da página (português na raiz, inglês em en/, espanhol em es/), cada uma com título,
    # descrição e marcação de eventos para os buscadores no próprio idioma
    for lang, pasta_l, raiz in (("pt", "", ""), ("en", "en", "../"), ("es", "es", "../")):
        html = (modelo.replace("/*__DADOS__*/null", dados_site).replace("<!--__CABECA__-->", cabeca(lang, ed, eventos))
                .replace("__HTMLLANG__", {"pt": "pt-BR", "en": "en", "es": "es"}[lang])
                .replace("__RAIZ__", raiz).replace('"__LANG__"', f'"{lang}"'))
        os.makedirs(os.path.join(out, pasta_l), exist_ok=True)
        open(os.path.join(out, pasta_l, "index.html"), "w", encoding="utf-8").write(html)
    escrever_mapa_do_site(out)

    # relatório de exceções
    n_sess = sum(len(e["sessoes"]) for e in eventos)
    reg = Counter(e["regiao"] or "(sem região)" for e in eventos)
    linhas = [f"# Relatório da edição — {ed['titulo']}", "",
              f"- Eventos e exposições: **{len(eventos)}** ({sum(e['tipo']=='evento' for e in eventos)} eventos com "
              f"{n_sess} sessões; {sum(e['tipo']=='cartaz' for e in eventos)} em cartaz)",
              f"- Grátis: **{sum(e['gratis'] for e in eventos)}** · preço popular (até R$ {POPULAR}): "
              f"**{sum(e['faixa']=='popular' for e in eventos)}**",
              f"- Conferidos sem ressalva: **{sum(e['status']=='conferido' for e in eventos)}** · "
              f"a confirmar: **{sum(e['status']=='a_confirmar' for e in eventos)}**", "",
              "## Distribuição por região", ""]
    linhas += [f"- {r}: {reg.get(r, 0)}" for r in REGIOES + ["(sem região)"] if reg.get(r, 0)]
    linhas += ["", "## Conferente independente (IA)", ""]
    if conf.get("resultado"):
        for r in conf["resultado"]:
            res = f" → **{r['resolucao']}**" if r.get("resolucao") else " → **pendente (sai como “a confirmar”)**"
            linhas.append(f"- **{r['titulo']}** ({r['id']}) · {r['campo']} · *{r['veredito']}* — {r['detalhe']}{res}")
    else:
        linhas.append("- Nenhuma divergência registrada." if os.path.exists(conf_path) else "- Conferência ainda não executada.")
    linhas += ["", "## Conferência mecânica (regras)", ""]
    nomes = {e["id"]: e["titulo"] for e in eventos}
    linhas += [f"- [{g}] **{nomes[i]}** ({i}) — {p}" for i, p, g in mec] or ["- Nenhum problema."]
    linhas += ["", "## Destaques (A boa)", ""]
    for dia, l in destaques["dias"].items():
        linhas.append(f"- **{dia[8:10]}/{dia[5:7]}**: " + "; ".join(nomes.get(d["id"], d["id"]) for d in l))
    linhas += ["", "Regras de curadoria:"] + ([f"- ⚠️ {(d[8:10] + '/' + d[5:7]) if len(d) == 10 else d} — {a}" for d, a in alertas_dest] or ["- Todas as regras cumpridas."])
    linhas += ["", "## Traduções", ""]
    linhas += ([f"- Sem tradução (aparece em português no site em inglês e espanhol): {', '.join(sem_traducao)}"] if sem_traducao
               else ["- Todas as sinopses têm versão em inglês e espanhol."])
    linhas += ["", "## Notas de redação", ""]
    linhas += [f"- **{e['titulo']}** — {e['nota_redacao']}" for e in eventos if e.get("nota_redacao")]
    open(os.path.join(pasta, "relatorio.md"), "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    print(f"{len(eventos)} eventos · {len(feeds)} calendários · {len(mec)} alertas mecânicos · "
          f"{len(conf.get('resultado', []))} apontamentos do conferente · {len(sess_dest)} destaques · {len(alertas_dest)} alertas de curadoria")
    for a in alertas_dest:
        print("  curadoria:", *a)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-11-19")
