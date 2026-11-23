#!/usr/bin/env python3
"""Diagnóstico de alcance das fontes do Todos os Rios.

Visita uma vez a página de cada fonte do Núcleo com site e anota, sem guardar conteúdo:
  - se o site responde a partir da nuvem;
  - o que as regras do próprio site (robots.txt) permitem a leitores automáticos;
  - quais "portas de dados" ele oferece: feed RSS/Atom, eventos em dados estruturados
    (JSON-LD), porta padrão do WordPress, calendário de eventos, arquivo de agenda (.ics), mapa do site.
Só usa a biblioteca padrão do Python. Identifica-se como TodosOsRiosBot e faz poucas visitas por site.
Resultado: dados/coleta/diagnostico.json e dados/coleta/diagnostico.md
"""
import csv, json, os, re, ssl, time, urllib.request, urllib.error, urllib.robotparser
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGENTE = "TodosOsRiosBot/0.3 (agenda cultural aberta do Rio de Janeiro; +https://todososrios.com.br/; abreterio@gmail.com)"
LIMITE = 600_000  # bytes lidos por página, no máximo


def baixar(url, limite=LIMITE, espera=20):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "*/*", "Accept-Language": "pt-BR,pt;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=espera, context=ssl.create_default_context()) as r:
            corpo = r.read(limite)
            return r.status, r.geturl(), r.headers.get("Content-Type", ""), corpo.decode(r.headers.get_content_charset() or "utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, url, "", ""
    except Exception as e:  # tempo esgotado, certificado, DNS...
        return 0, url, "", type(e).__name__ + ": " + str(e)[:120]


def examinar(fonte):
    url = fonte["url"].strip()
    if not url.startswith("http"):
        url = "https://" + url
    r = {"id": fonte["id"], "nome": fonte["nome"], "regiao": fonte["regiao"], "url": url}
    base = "{0.scheme}://{0.netloc}".format(urlparse(url))

    # 1. regras do próprio site
    st, _, _, txt = baixar(base + "/robots.txt", 100_000)
    r["robots_status"] = st
    permitido = None
    if st == 200 and "<html" not in txt[:300].lower():
        rp = urllib.robotparser.RobotFileParser(); rp.parse(txt.splitlines())
        permitido = rp.can_fetch("TodosOsRiosBot", url)
        r["robots_mapa"] = [l.split(":", 1)[1].strip() for l in txt.splitlines() if l.lower().startswith("sitemap:")][:3]
    r["robots_permite"] = permitido
    if permitido is False:
        r["conclusao"] = "site proíbe leitura automática"
        return r

    # 2. a página em si
    st, final, tipo, html = baixar(url)
    r["status"] = st; r["url_final"] = final
    if st != 200:
        r["erro"] = html if st == 0 else ""
        r["conclusao"] = "não respondeu da nuvem" if st == 0 else f"recusou (código {st})"
        return r
    r["tamanho"] = len(html)
    baixo = html.lower()
    portas = []

    feeds = re.findall(r'<link[^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]*>', html, re.I)
    hrefs = [m.group(1) for f in feeds for m in [re.search(r'href=["\']([^"\']+)', f)] if m]
    hrefs = [urljoin(final, h) for h in hrefs if "comments" not in h][:3]
    if hrefs:
        r["feeds"] = hrefs; portas.append("feed")

    blocos = re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.I | re.S)
    tipos = set()
    for b in blocos:
        tipos.update(re.findall(r'"@type"\s*:\s*"([A-Za-z]+)"', b))
    r["jsonld_tipos"] = sorted(tipos)[:12]
    if tipos & {"Event", "MusicEvent", "TheaterEvent", "ExhibitionEvent", "Festival", "ScreeningEvent", "DanceEvent", "ComedyEvent", "ChildrensEvent", "VisualArtsEvent", "LiteraryEvent"}:
        portas.append("eventos em dados estruturados")

    wp = "wp-content" in baixo or "wp-json" in baixo
    r["wordpress"] = wp
    if wp:
        st2, _, t2, j = baixar(base + "/wp-json/", 200_000)
        if st2 == 200 and "namespaces" in j:
            portas.append("porta do WordPress")
            r["wp_namespaces"] = re.findall(r'"((?:tribe|wp|mec|eventon|events?)[^"]{0,30})"', j)[:12]
            if "tribe/events" in j:
                st3, _, _, ev = baixar(base + "/wp-json/tribe/events/v1/events?per_page=5", 200_000)
                if st3 == 200 and '"events"' in ev:
                    portas.append("calendário de eventos (The Events Calendar)")
                    r["tribe_total"] = (re.search(r'"total"\s*:\s*(\d+)', ev) or [None, None])[1]
            for tipo_post in ("eventos", "evento", "events", "event", "programacao", "agenda", "espetaculos", "shows"):
                if f'"/wp/v2/{tipo_post}"' in j or f'/wp/v2/{tipo_post}"' in j:
                    r.setdefault("wp_tipos_evento", []).append(tipo_post)
            if r.get("wp_tipos_evento"):
                portas.append("lista de eventos pelo WordPress")
        if not hrefs:
            st4, f4, t4, x = baixar(base + "/feed/", 50_000)
            if st4 == 200 and "<rss" in x[:600].lower():
                r["feeds"] = [base + "/feed/"]; portas.append("feed")

    if re.search(r'href=["\'][^"\']+\.ics\b|webcal://', html, re.I):
        portas.append("arquivo de agenda (.ics)")
    if "__next_data__" in baixo or "__nuxt" in baixo:
        r["app_js"] = True
        if "__next_data__" in baixo:
            portas.append("dados embutidos na página (Next.js)")
    if not r.get("robots_mapa"):
        st5, _, _, sm = baixar(base + "/sitemap.xml", 20_000)
        if st5 == 200 and ("<urlset" in sm or "<sitemapindex" in sm):
            r["robots_mapa"] = [base + "/sitemap.xml"]
    if r.get("robots_mapa"):
        portas.append("mapa do site")
    # o texto da página menciona datas? (sinal de que a programação está no próprio HTML)
    r["datas_no_texto"] = len(re.findall(r'\b\d{1,2}/1[12](?:/20\d\d)?\b|\b\d{1,2} de (?:novembro|dezembro)\b', re.sub(r'<[^>]+>', ' ', html), re.I))
    r["portas"] = portas
    fortes = [p for p in portas if p not in ("mapa do site", "porta do WordPress")]
    r["conclusao"] = ("leitura limpa: " + ", ".join(fortes)) if fortes else (
        "só leitura da página (programação aparece no texto)" if r["datas_no_texto"] >= 3 else
        "página abre, mas a programação não está no texto (carregada depois, ou em outra página)")
    return r


def main():
    fontes = [f for f in csv.DictReader(open(os.path.join(RAIZ, "dados", "fontes.csv"), encoding="utf-8-sig"), delimiter=";")
              if f["camada"] == "Núcleo" and f["metodo"].startswith("Site")]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=12) as ex:
        res = list(ex.map(examinar, fontes))
    os.makedirs(os.path.join(RAIZ, "dados", "coleta"), exist_ok=True)
    json.dump({"feito_em": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "segundos": round(time.time() - t0), "fontes": res},
              open(os.path.join(RAIZ, "dados", "coleta", "diagnostico.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    grupos = Counter(r["conclusao"].split(":")[0] for r in res)
    linhas = ["# Diagnóstico de alcance das fontes", "", f"Feito em {time.strftime('%d/%m/%Y %H:%M', time.gmtime())} (UTC), em {round(time.time()-t0)} segundos, a partir do serviço de automação do GitHub.", "",
              "## Resumo", ""] + [f"- {k}: **{v}**" for k, v in grupos.most_common()] + ["", "## Fonte a fonte", "", "| Fonte | Região | Conclusão |", "|---|---|---|"]
    linhas += [f"| {r['nome']} | {r['regiao']} | {r['conclusao']} |" for r in sorted(res, key=lambda x: (x["conclusao"], x["nome"]))]
    open(os.path.join(RAIZ, "dados", "coleta", "diagnostico.md"), "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    print(len(res), "fontes;", dict(grupos))


if __name__ == "__main__":
    main()
