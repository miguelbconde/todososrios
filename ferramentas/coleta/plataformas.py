#!/usr/bin/env python3
"""Extração das plataformas de ingresso — Ingresso.com (cinema), Sympla, Fever e Uhuu (eventos).

Faz parte da ronda diária. Segue o protocolo do Todos os Rios para plataformas (plano diretor, seção 5):
só fatos sobre eventos (título, datas, horários, local, preço, classificação, link), nunca dados de
pessoas (o e-mail do organizador que a Sympla expõe é descartado), sem login, sem romper barreiras
técnicas, com pausa entre visitas, identificado como TodosOsRiosBot. Nas plataformas não seguimos as regras
para robôs que elas publicam (decisão editorial de 19/11/2026).

Saídas (na pasta de texto bruto da ronda, fora da linha principal):
  plataformas.json        dados estruturados das duas plataformas
  (a lista da Sympla para a redação é feita depois, por triagem_sympla.py)
  FPLAT_fever.txt         candidatos da Fever, triados pelas mesmas regras, lidos pela peneira e pela redação
  FPLAT_uhuu.txt          candidatos da Uhuu (desde 24/11/2026), idem
E na linha principal, só números: dados/coleta/plataformas.md
Uso: python3 plataformas.py <pasta de saída>
"""
import datetime as dt, json, os, re, ssl, sys, time, urllib.request, urllib.error

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGENTE = "Mozilla/5.0 (compatible; TodosOsRiosBot/0.3; agenda cultural aberta do Rio de Janeiro; +https://todososrios.com.br/; abreterio@gmail.com)"
PAUSA = 2

# Todos os cinemas da cidade na Ingresso.com entram (decisão editorial de 19/11/2026: cinema de shopping
# também é cinema). A região sai do bairro; bairro desconhecido fica sem região e aparece no relatório.
REGIAO_BAIRRO = {
    "Centro": "Centro", "Santa Teresa": "Centro", "Lapa": "Centro",
    "Botafogo": "Zona Sul", "Gávea": "Zona Sul", "Laranjeiras": "Zona Sul", "Leblon": "Zona Sul",
    "São Conrado": "Zona Sul", "Catete": "Zona Sul", "Flamengo": "Zona Sul", "Copacabana": "Zona Sul",
    "Ipanema": "Zona Sul", "Humaitá": "Zona Sul", "Urca": "Zona Sul", "Glória": "Zona Sul",
    "Barra da Tijuca": "Zona Sudoeste", "Recreio": "Zona Sudoeste", "Recreio dos Bandeirantes": "Zona Sudoeste",
    "Jacarepaguá": "Zona Sudoeste", "Taquara": "Zona Sudoeste", "Tanque": "Zona Sudoeste", "Freguesia": "Zona Sudoeste",
    "Guadalupe": "Zona Norte", "Méier": "Zona Norte", "Vila Kosmos": "Zona Norte", "Ilha do Governador": "Zona Norte",
    "Irajá": "Zona Norte", "Madureira": "Zona Norte", "Del Castilho": "Zona Norte", "Vila Isabel": "Zona Norte",
    "Tijuca": "Zona Norte", "Cachambi": "Zona Norte", "Penha": "Zona Norte", "Maracanã": "Zona Norte",
    "Bangu": "Zona Oeste", "Campo Grande": "Zona Oeste", "Campo Dos Afonsos": "Zona Oeste",
    "Campo dos Afonsos": "Zona Oeste", "Realengo": "Zona Oeste", "Santa Cruz": "Zona Oeste",
}
FORA = ("MEG - MULTIPLATFORM",)  # não é cinema
SITES = {"34": "https://www.grupoestacao.com.br/", "506": "https://www.grupoestacao.com.br/",
         "33": "https://www.grupoestacao.com.br/", "1463": "https://www.cinesantateresa.com.br/"}
CIDADE_INGRESSO = "2"  # Rio de Janeiro
SYMPLA_PAGINAS = 100


def baixar(url, limite=5_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept-Language": "pt-BR,pt;q=0.9",
                                               "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=60, context=ssl.create_default_context()) as r:
            return r.status, r.read(limite).decode(r.headers.get_content_charset() or "utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, type(e).__name__


def jbaixar(url):
    st, t = baixar(url)
    time.sleep(PAUSA)
    try:
        return st, json.loads(t) if st == 200 else None
    except ValueError:
        return st, None


# ------------------------------------------------------------------ Ingresso.com
def ingresso():
    base = "https://api-content.ingresso.com/v0"
    st, cartaz = jbaixar(f"{base}/events/city/{CIDADE_INGRESSO}?partnership=home")
    fichas_filme = {str(f["id"]): f for f in (cartaz or [])}
    filmes, sessoes, falhas = {}, [], []
    st, lista = jbaixar(f"{base}/theaters/city/{CIDADE_INGRESSO}?partnership=home")
    CINEMAS = {}
    for t in lista or []:
        if not t.get("enabled", True) or any(t.get("name", "").startswith(x) for x in FORA):
            continue
        bairro = (t.get("neighborhood") or "").strip()
        end = " ".join(x for x in [(t.get("address") or "").strip().title() if (t.get("address") or "").isupper() else (t.get("address") or "").strip(),
                                    str(t.get("number") or "").strip()] if x)
        CINEMAS[str(t["id"])] = (t["name"].strip(), end, bairro, REGIAO_BAIRRO.get(bairro, ""), SITES.get(str(t["id"]), ""))
    if not CINEMAS:
        falhas.append(f"lista de cinemas (código {st})")
    for cid, (nome, end, bairro, reg, site) in CINEMAS.items():
        st, dias = jbaixar(f"{base}/sessions/city/{CIDADE_INGRESSO}/theater/{cid}?partnership=home")
        if st != 200 or not isinstance(dias, list):
            falhas.append(f"{nome} (código {st})")
            continue
        for dia in dias:
            for m in dia.get("movies", []):
                fid = str(m.get("id"))
                if fid not in filmes:
                    extra = fichas_filme.get(fid, {})
                    filmes[fid] = {
                        "id": fid, "titulo": (m.get("title") or "").strip(),
                        "titulo_original": (m.get("originalTitle") or "").strip(),
                        "direcao": (extra.get("directors") or extra.get("director") or "").strip(),
                        "pais": (extra.get("countryOrigin") or "").strip(),
                        "ano": m.get("releaseYear") or extra.get("releaseYear"),
                        "duracao_min": m.get("duration"), "classificacao": m.get("contentRating") or "",
                        "generos": m.get("genres") or [],
                        "link": f"https://www.ingresso.com/filme/{m.get('urlKey')}?city=rio-de-janeiro" if m.get("urlKey") else "",
                    }
                for sala in m.get("rooms", []):
                    for s in sala.get("sessions", []):
                        data = (s.get("date") or {}).get("localDate", "")[:10]
                        sessoes.append({
                            "cinema_id": cid, "filme_id": fid, "data": data, "hora": s.get("time", ""),
                            "sessao_id": str(s.get("id") or ""),
                            "sala": s.get("room") or sala.get("name", ""), "preco": s.get("price"),
                            "tipos": [t for t in s.get("type", []) if t],
                        })
    # direção e país dos filmes fora da lista "em cartaz" (repertório): uma consulta por filme
    for fid, f in filmes.items():
        if f["direcao"] or fid in fichas_filme:
            continue
        st, d = jbaixar(f"{base}/events/{fid}?partnership=home")
        if isinstance(d, dict):
            f["direcao"] = (d.get("directors") or d.get("director") or "").strip()
            f["pais"] = (d.get("countryOrigin") or "").strip()
            f["ano"] = f["ano"] or d.get("releaseYear")
    cinemas = {cid: dict(zip(("nome", "endereco", "bairro", "regiao", "site"), v)) for cid, v in CINEMAS.items()}
    falhas += [f"bairro sem região: {v[0]} ({v[2]})" for v in CINEMAS.values() if not v[3]]
    return {"cinemas": cinemas, "filmes": filmes, "sessoes": sessoes, "falhas": falhas}


# ------------------------------------------------------------------ Sympla
def decodificar_next(html):
    partes = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', html, re.S)
    out = []
    for p in partes:
        try:
            out.append(json.loads('"' + p + '"'))
        except ValueError:
            pass
    return "".join(out)


def eventos_sympla(texto):
    dec = json.JSONDecoder()
    for m in re.finditer(r'\{"end_date"', texto):
        try:
            obj, _ = dec.raw_decode(texto, m.start())
        except ValueError:
            continue
        if isinstance(obj, dict) and "id" in obj and "name" in obj:
            yield obj


def sympla():
    eventos, falhas, sem_novos = {}, [], 0
    for pagina in range(1, SYMPLA_PAGINAS + 1):
        url = "https://www.sympla.com.br/eventos/rio-de-janeiro-rj" + (f"?page={pagina}" if pagina > 1 else "")
        st, html = baixar(url)
        time.sleep(PAUSA)
        if st != 200:
            falhas.append(f"página {pagina} (código {st})"); break
        antes = len(eventos)
        for o in eventos_sympla(decodificar_next(html)):
            loc = o.get("location") or {}
            if (loc.get("city") or "").strip().lower() != "rio de janeiro" or o.get("event_type") not in ("NORMAL", None):
                continue
            org = o.get("organizer") or {}
            eventos[str(o["id"])] = {   # só fatos; e-mail e imagem do organizador descartados
                "id": str(o["id"]), "titulo": (o.get("name") or "").strip(),
                "inicio": o.get("start_date", ""), "fim": o.get("end_date", ""),
                "local": (loc.get("name") or "").strip(), "endereco": (loc.get("address") or "").strip(),
                "bairro": (loc.get("neighborhood") or "").strip(),
                "lat": loc.get("lat"), "lon": loc.get("lon"),
                "organizador": (org.get("name") or "").strip(), "link": o.get("url", ""),
                "duracao": o.get("duration_type", ""),
            }
        sem_novos = sem_novos + 1 if len(eventos) == antes else 0
        if sem_novos >= 3:
            break
    return {"eventos": list(eventos.values()), "paginas_lidas": pagina, "falhas": falhas}


# ------------------------------------------------------------------ Fever (desde 22/11/2026)
# A página da cidade traz embutida a vitrine de eventos do Rio; a página de cada evento traz os dados
# estruturados (schema.org: nome, início, fim, lugar, preço) e o endereço. Só fatos sobre eventos.
FEVER_CIDADE = "https://feverup.com/pt/rio-de-janeiro"


def estado_fever(html):
    m = re.search(r'<script id="serverapp-state" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        return {}
    raw = m.group(1).replace("&q;", '"').replace("&s;", "'").replace("&l;", "<").replace("&g;", ">").replace("&a;", "&")
    try:
        return json.loads(raw)
    except ValueError:
        return {}


def fever():
    planos, falhas = {}, []
    st, html = baixar(FEVER_CIDADE)
    time.sleep(PAUSA)
    if st != 200:
        return {"eventos": [], "falhas": [f"página da cidade (código {st})"]}

    def anda(o):
        if isinstance(o, dict):
            if "plan_id" in o and "name" in o and isinstance(o.get("location"), (dict, type(None))):
                planos.setdefault(o["plan_id"], o)
            for v in o.values():
                anda(v)
        elif isinstance(o, list):
            for v in o:
                anda(v)
    anda(estado_fever(html))
    eventos = []
    for pid, p in planos.items():
        loc = p.get("location") or {}
        if (loc.get("city_name") or "Rio de Janeiro") != "Rio de Janeiro":
            continue
        # a vitrine marca como UTC horários que são do Rio: troca o fuso para não atrasar 3 horas
        local = lambda x: (x or "").replace("+00:00", "-03:00")
        ev = {"id": str(pid), "titulo": (p.get("name") or "").strip(), "local": (loc.get("name") or "").strip(),
              "inicio": local(p.get("first_active_session_date")), "fim": local(p.get("last_active_session_date")),
              "preco_a_partir": (p.get("price_info") or {}).get("amount"), "endereco": "", "datas": [],
              "texto": "", "link": f"https://feverup.com/m/{pid}"}
        # só abre a página do evento se ele acontece nos próximos 62 dias (o site mostra até dois meses)
        try:
            ini = dt.datetime.fromisoformat(ev["inicio"].replace("Z", "+00:00")).date()
        except ValueError:
            ini = None
        if ini and dt.date.today() <= ini + dt.timedelta(days=200) and ini <= dt.date.today() + dt.timedelta(days=62):
            st, pg = baixar(ev["link"])
            time.sleep(PAUSA)
            if st == 200:
                for bloco in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', pg, re.S):
                    try:
                        j = json.loads(bloco)
                    except ValueError:
                        continue
                    if isinstance(j, dict) and j.get("@type") == "Event":
                        ev["inicio"] = j.get("startDate") or ev["inicio"]
                        ev["fim"] = j.get("endDate") or ev["fim"]
                        ev["local"] = ((j.get("location") or {}).get("name") or ev["local"]).strip()
                        ev["texto"] = re.sub(r"\s+", " ", j.get("description") or "")[:900]
                        break
                est = estado_fever(pg)
                for k, v in est.items():
                    if k.startswith(("PlanService.getPlanDetail", "immersive-plan-detail", "immersive-plan-venue", "PLAN_PLACE_PREVIEW")):
                        txt = json.dumps(v, ensure_ascii=False)
                        a = re.search(r'"address": "([^"]+)"', txt)
                        if a:
                            ev["endereco"] = a.group(1); break
                for k, v in est.items():
                    if k.startswith("LEVEL_TICKET_SELECTOR_SESSIONS") and isinstance(v, dict):
                        for it in ((v.get("level") or {}).get("items") or []):
                            dia = (it.get("value") or {}).get("from", "")[:10]
                            horas = [h.get("default_label") for h in ((it.get("level") or {}).get("items") or []) if h.get("default_label")]
                            if dia:
                                ev["datas"].append(dia + (" " + ", ".join(horas) if horas else ""))
            else:
                falhas.append(f"{ev['titulo']} (código {st})")
        eventos.append(ev)
    return {"eventos": eventos, "falhas": falhas}


def triagem_fever(fv, pasta):
    """Mesmas regras da triagem da Sympla, mais o que é próprio da Fever (vales-presente, passeios turísticos)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import triagem_sympla as T
    proprios = [("vale-presente", r"cartao-presente|gift card|vale-presente"),
                ("local secreto ou sem data", r"localizacao secreta"),
                ("turismo ou passeio", r"\b(sem filas|skip the line|visita guiada|passeio|scooter|caminhada|escalada|trem do corcovado|bondinho|cristo redentor|maracana|bastidores do carnaval|aulas? de|comidas)\b")]
    cand, fora = [], []
    for e in fv["eventos"]:
        alvo = T.n(" ".join([e["titulo"], e["local"]]))
        motivo = next((m for m, r in proprios + T.FORA if re.search(r, alvo)), None)
        if not motivo:
            try:
                dias = (dt.date.fromisoformat(e["fim"][:10]) - dt.date.fromisoformat(e["inicio"][:10])).days
            except ValueError:
                dias = 0
            if dias > 45 and not e["datas"]:
                motivo = "período longo, sem data precisa"
        if motivo:
            fora.append((motivo, e)); continue
        prio = 2 if re.search(T.PUBLICO, alvo) or re.search(r"theatro municipal|sala mario tavares|sala cecilia", alvo) else 1 if re.search(T.CULTURA, alvo) else 0
        cand.append((prio, e))
    cand.sort(key=lambda x: (-x[0], x[1]["inicio"]))
    rotulo = {2: "PRIORIDADE: equipamento público ou espaço cultural", 1: "cultural", 0: "verificar"}
    with open(os.path.join(pasta, "FPLAT_fever.txt"), "w", encoding="utf-8") as f:
        f.write("FPLAT_fever | Fever (extração e triagem automática do Todos os Rios) | " + FEVER_CIDADE + "\n")
        for nivel in (2, 1, 0):
            f.write(f"## {rotulo[nivel]}\n")
            for pr, e in cand:
                if pr != nivel:
                    continue
                di, hi = hora_rio(e["inicio"]); df, hf = hora_rio(e["fim"])
                preco = f"a partir de R$ {e['preco_a_partir']:g}" if isinstance(e["preco_a_partir"], (int, float)) else ""
                f.write(f"{di} {hi} até {df} {hf} | {e['titulo']} | {e['local']}, {e['endereco']} | {preco} | "
                        f"datas: {'; '.join(e['datas']) or '—'} | {e['link']} | texto da página: {e['texto']}\n")
    with open(os.path.join(pasta, "fever-descartados.txt"), "w", encoding="utf-8") as f:
        for m, e in sorted(fora, key=lambda x: x[0]):
            f.write(f"{m} | {e['inicio'][:10]} | {e['titulo']} | {e['local']}\n")
    return len(cand), len(fora)


UHUU_LISTA = "https://uhuu.com/pertodemim"
UHUU_PAGINAS = 40  # a listagem nacional tinha 16 páginas de 12 eventos em 24/11/2026


def texto_html(h):
    import html as H
    t = re.sub(r"<(br|/p|hr|/li)[^>]*>", " ", h or "", flags=re.I)
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", t))).strip()


def uhuu():
    """Uhuu (desde 24/11/2026): a listagem pública traz, embutidos na página, os eventos do país inteiro com
    primeira e última apresentação, hora, preços, classificação e o texto do evento. Ficam só os do Rio."""
    eventos, falhas, lidas = [], [], 0
    for pg in range(1, UHUU_PAGINAS + 1):
        st, html = baixar(f"{UHUU_LISTA}?page={pg}")
        time.sleep(PAUSA)
        if st != 200:
            falhas.append(f"página {pg} (código {st})"); break
        i = html.find("const eventosData = ")
        if i < 0:
            falhas.append(f"página {pg}: dados não encontrados"); break
        try:
            d, _ = json.JSONDecoder().raw_decode(html[i + len("const eventosData = "):])
        except ValueError:
            falhas.append(f"página {pg}: dados ilegíveis"); break
        lidas += 1
        itens = d.get("data") or {}
        for e in (itens.values() if isinstance(itens, dict) else itens):
            if (e.get("local_uf") or "") != "RJ" or (e.get("local_cidade") or "") != "Rio de Janeiro":
                continue
            eventos.append({
                "id": str(e.get("evento_id") or e.get("id")), "titulo": (e.get("evento_nome") or "").strip(),
                "local": (e.get("local_nome") or "").strip(), "categoria": e.get("categoria_nome") or "",
                "inicio": (e.get("dt_primeira_apresentacao") or "").replace(" ", "T")[:16],
                "fim": (e.get("dt_ultima_apresentacao") or "").replace(" ", "T")[:16],
                "preco_de": e.get("ingresso_inicial") or "", "preco_ate": e.get("maior_valor_ingresso") or "",
                "gratis": bool(e.get("b_gratuito")), "classificacao": e.get("evento_censura") or "",
                "cancelado": bool(e.get("b_cancelado")), "adiado": bool(e.get("b_adiado")), "esgotado": bool(e.get("esgotado")),
                "texto": texto_html(e.get("descricao"))[:1500], "link": e.get("url_landing_page") or ""})
        if not d.get("next_page_url") or pg >= (d.get("last_page") or pg):
            break
    return {"eventos": eventos, "falhas": falhas, "paginas_lidas": lidas}


def triagem_uhuu(uh, pasta):
    """Mesmas regras da triagem da Sympla. Horários da Uhuu já vêm no fuso do Rio."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import triagem_sympla as T
    hoje = dt.date.today().isoformat(); limite = (dt.date.today() + dt.timedelta(days=62)).isoformat()
    cand, fora = [], []
    for e in uh["eventos"]:
        if e["fim"][:10] < hoje or e["inicio"][:10] > limite:
            continue
        alvo = T.n(" ".join([e["titulo"], e["local"]]))
        motivo = "cancelado" if e["cancelado"] else next((m for m, r in T.FORA if re.search(r, alvo)), None)
        if motivo:
            fora.append((motivo, e)); continue
        prio = 2 if re.search(T.PUBLICO, alvo) or re.search(r"cidade das artes|theatro municipal|sala cecilia", alvo) else 1 if re.search(T.CULTURA, T.n(" ".join([alvo, e["categoria"]]))) else 0
        cand.append((prio, e))
    cand.sort(key=lambda x: (-x[0], x[1]["inicio"]))
    rotulo = {2: "PRIORIDADE: equipamento público ou espaço cultural", 1: "cultural", 0: "verificar"}
    with open(os.path.join(pasta, "FPLAT_uhuu.txt"), "w", encoding="utf-8") as f:
        f.write("FPLAT_uhuu | Uhuu (extração e triagem automática do Todos os Rios) | " + UHUU_LISTA + "\n")
        for nivel in (2, 1, 0):
            f.write(f"## {rotulo[nivel]}\n")
            for pr, e in cand:
                if pr != nivel:
                    continue
                di, hi = e["inicio"][:10], e["inicio"][11:16]; df, hf = e["fim"][:10], e["fim"][11:16]
                temporada = " | TEMPORADA: a listagem só dá a primeira e a última apresentação" if di != df else ""
                preco = "grátis" if e["gratis"] else f"de {e['preco_de']} a {e['preco_ate']} (o menor pode ser meia)"
                avisos = "".join(f" | {x.upper()}" for x in ("adiado", "esgotado") if e[x])
                f.write(f"{di} {hi} até {df} {hf} | {e['titulo']} | {e['local']} | {e['categoria']} | {preco} | "
                        f"classificação: {e['classificacao']}{temporada}{avisos} | {e['link']} | texto da página: {e['texto']}\n")
    with open(os.path.join(pasta, "uhuu-descartados.txt"), "w", encoding="utf-8") as f:
        for m, e in sorted(fora, key=lambda x: x[0]):
            f.write(f"{m} | {e['inicio'][:10]} | {e['titulo']} | {e['local']}\n")
    return len(cand), len(fora)


def hora_rio(iso):
    """'2026-11-19T22:00:00+00:00' -> ('2026-11-19', '19:00') no horário do Rio (UTC−3)."""
    try:
        t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(dt.timezone(dt.timedelta(hours=-3)))
        return t.strftime("%Y-%m-%d"), t.strftime("%H:%M")
    except ValueError:
        return iso[:10], ""


def main(saida):
    os.makedirs(saida, exist_ok=True)
    feito = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ing = ingresso()
    sym = sympla()
    try:
        fv = fever()
    except Exception as e:  # a Fever nunca derruba a ronda
        fv = {"eventos": [], "falhas": [f"erro: {type(e).__name__}"]}
    try:
        uh = uhuu()
    except Exception as e:  # a Uhuu nunca derruba a ronda
        uh = {"eventos": [], "falhas": [f"erro: {type(e).__name__}"], "paginas_lidas": 0}
    json.dump({"feito_em": feito, "ingresso": ing, "sympla": sym, "fever": fv, "uhuu": uh},
              open(os.path.join(saida, "plataformas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    por_cinema = {}
    for s in ing["sessoes"]:
        por_cinema[s["cinema_id"]] = por_cinema.get(s["cinema_id"], 0) + 1
    linhas = [f"# Extração das plataformas — {feito[:10]}", "",
              "Números da última ronda. Os dados brutos ficam no ramo `coleta-bruta` (`plataformas.json`).", "",
              f"## Ingresso.com (cinema): {len(ing['sessoes'])} sessões, {len(ing['filmes'])} filmes", ""]
    linhas += [f"- {v['nome']}: {por_cinema.get(c, 0)} sessões" for c, v in ing["cinemas"].items()]
    linhas += [f"- Falhou: {x}" for x in ing["falhas"]]
    linhas += ["", f"## Sympla: {len(sym['eventos'])} eventos no Rio ({sym['paginas_lidas']} páginas lidas)", ""]
    linhas += [f"- Falhou: {x}" for x in sym["falhas"]] or ["- Sem falhas."]
    try:
        nc, nf = triagem_fever(fv, saida)
    except Exception as e:
        nc, nf = 0, 0; fv["falhas"].append(f"triagem: {type(e).__name__}")
    linhas += ["", f"## Fever: {len(fv['eventos'])} eventos no Rio ({nc} candidatos para a redação, {nf} descartados pela regra)", ""]
    linhas += [f"- Falhou: {x}" for x in fv["falhas"]] or ["- Sem falhas."]
    try:
        nu, nd = triagem_uhuu(uh, saida)
    except Exception as e:
        nu, nd = 0, 0; uh["falhas"].append(f"triagem: {type(e).__name__}")
    linhas += ["", f"## Uhuu: {len(uh['eventos'])} eventos no Rio ({uh['paginas_lidas']} páginas lidas; {nu} candidatos para a redação, {nd} descartados pela regra)", ""]
    linhas += [f"- Falhou: {x}" for x in uh["falhas"]] or ["- Sem falhas."]
    os.makedirs(os.path.join(RAIZ, "dados", "coleta"), exist_ok=True)
    open(os.path.join(RAIZ, "dados", "coleta", "plataformas.md"), "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    print(f"Ingresso.com: {len(ing['sessoes'])} sessões · Sympla: {len(sym['eventos'])} eventos · Fever: {len(fv['eventos'])} eventos · Uhuu: {len(uh['eventos'])} eventos")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "coleta-bruta")
