#!/usr/bin/env python3
"""Agendas dedicadas da ronda diária (desde 22/11/2026): Sesc RJ, Arte que Acontece, (desde 24/11/2026) Revista CONCERTO
e (desde 25/11/2026) o calendário oficial da Riotur (FAGENDA_riotur.txt, radar de fatos; cache em riotur-cache.json),
a Bilheteria Digital (FPLAT_bilheteriadigital.txt), o AllEvents (FAGENDA_allevents.txt, radar) e o feed do Visit Rio
(FAGENDA_visitrio.txt, radar).

Por decisão editorial, os eventos dessas duas fontes entram por padrão na rotina da redação.
Este programa comum (sem IA) lê as agendas e grava, na pasta da ronda, dois arquivos que a
peneira e a redação leem como qualquer outra fonte:

  FAGENDA_sesc.txt          programação das unidades do Sesc na cidade do Rio, uma linha por sessão,
                            com dia, hora, unidade, preços e o começo da sinopse oficial
  FAGENDA_arteacontece.txt  exposições em cartaz no Rio segundo o Arte que Acontece, uma linha por
                            exposição, com período, lugar e link (radar de fatos: a ficha se escreve
                            a partir da fonte oficial do espaço, sem copiar texto do portal)
  FAGENDA_concerto.txt      concertos, recitais, óperas e balés na cidade do Rio segundo o roteiro diário da
                            Revista CONCERTO, uma linha por apresentação, com dia, hora, local, endereço, ingressos
                            e o programa (radar de fatos, como o Arte que Acontece)

Boas maneiras: identifica-se como TodosOsRiosBot, só lê páginas públicas sem login, com pausa entre
visitas; os sites permitem a leitura nas suas regras para robôs. Nunca guarda dado de pessoas.
Uso: python3 agendas.py <pasta da ronda>
"""
import datetime as dt
import html
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plataformas import baixar, decodificar_next  # noqa: E402

PAUSA = 3
HOJE = dt.date.today()
JANELA_SESC = 62          # dias à frente lidos na agenda do Sesc (o site mostra até dois meses)
# Unidades do Sesc dentro do município do Rio (as demais ficam no estado: Niterói, Petrópolis etc.)
SESC_RIO = {
    "Arte Sesc": ("Flamengo", "Zona Sul"),
    "Sesc Botafogo - Biblioteca Machado de Assis": ("Botafogo", "Zona Sul"),
    "Sesc Cocotá - Biblioteca Euclides da Cunha": ("Ilha do Governador", "Zona Norte"),
    "Sesc Copacabana": ("Copacabana", "Zona Sul"),
    "Sesc Ginástico": ("Centro", "Centro"),
    "Sesc Madureira": ("Madureira", "Zona Norte"),
    "Sesc Ramos": ("Ramos", "Zona Norte"),
    "Sesc Tijuca": ("Tijuca", "Zona Norte"),
    "Sesc Engenho de Dentro": ("Engenho de Dentro", "Zona Norte"),
    "Sesc Campo Grande": ("Campo Grande", "Zona Oeste"),
}
FORA_DO_RIO = re.compile(r"vassouras|niter[oó]i|petr[oó]polis|s[aã]o paulo|belo horizonte|bras[ií]lia|salvador|"
                         r"curitiba|recife|porto alegre|inhotim|paraty|búzios|buzios|teres[oó]polis", re.I)


def limpo(t, n=None):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t or ""))
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n] if n else t


def edicao_fim(d):
    """Quarta-feira que fecha a edição (quinta a quarta) que contém o dia d."""
    return d + dt.timedelta(days=(2 - d.weekday()) % 7)


# ------------------------------------------------------------------ Sesc RJ
def _eventos_da_pagina(texto):
    dec = json.JSONDecoder()
    i = texto.find('"eventos":[')
    if i < 0:
        return [], None
    try:
        lista, _ = dec.raw_decode(texto, i + len('"eventos":'))
    except ValueError:
        return [], None
    m = re.search(r'"totalPages":(\d+)', texto)
    return lista, int(m.group(1)) if m else None


def _detalhe(texto):
    dec = json.JSONDecoder()
    i = texto.find('"schedule":[')
    sessoes = []
    if i >= 0:
        try:
            sched, _ = dec.raw_decode(texto, i + len('"schedule":'))
        except ValueError:
            sched = []
        for bloco in sched:
            for s in bloco.get("sessions", []):
                iso = (s.get("dateIso") or "").split("/")
                data, ate = iso[0][:10], (iso[-1][:10] if len(iso) > 1 else iso[0][:10])
                hora = (s.get("time") or "")[:5]
                precos = "; ".join(f"{x.get('tipo')}: R$ {x.get('preco')}" if str(x.get("preco")) not in ("0", "") else "grátis"
                                   for x in s.get("ingressos", []))
                sessoes.append({"data": data, "ate": ate or data, "hora": hora, "unidade": bloco.get("location") or "", "precos": precos,
                                "acessibilidade": ", ".join(s.get("acessibilidade") or [])})
    sin = ""
    j = texto.find('"sinopseMarkdown":"')
    if j >= 0:
        try:
            sin, _ = dec.raw_decode(texto, j + len('"sinopseMarkdown":'))
        except ValueError:
            sin = ""
    return sessoes, limpo(sin, 700)


def sesc(pasta):
    base = "https://cultura.sescrio.org.br"
    vistos, candidatos, falhas, pagina, total = set(), [], [], 1, None
    arquivo = 0  # eventos já encerrados que o site mantém na lista
    limite = HOJE + dt.timedelta(days=JANELA_SESC)
    while True:
        st, txt = baixar(f"{base}/programacao?page={pagina}")
        time.sleep(PAUSA)
        if st != 200:
            falhas.append(f"programação, página {pagina} (código {st})"); break
        lista, tp = _eventos_da_pagina(decodificar_next(txt))
        total = total or tp
        for e in lista:
            if e.get("slug") in vistos:
                continue
            vistos.add(e.get("slug"))
            if e.get("location") not in SESC_RIO:
                continue
            try:
                d = dt.datetime.strptime(e.get("date", ""), "%d/%m/%Y").date()
            except ValueError:
                d = None
            if d and d > limite:
                continue
            # A lista do site guarda o arquivo do ano inteiro; nela, a data de cada evento é a próxima sessão
            # (ou a última, se já acabou). Conferido em 24/11/2026: nenhum evento com data passada na lista tinha
            # sessão futura. Por isso não se abre a página dos antigos (economiza ~15 minutos da ronda).
            if d and d < HOJE - dt.timedelta(days=1):
                arquivo += 1
                continue
            candidatos.append(e)
        if not lista or (total and pagina >= total) or pagina >= 80:
            break
        pagina += 1
    linhas, motivos = [], {}
    for e in candidatos:
        url = f"{base}/programacao/{e['slug']}"
        st, txt = baixar(url)
        time.sleep(PAUSA)
        if st != 200:
            falhas.append(f"{e.get('title')} (código {st})"); continue
        sessoes, sin = _detalhe(decodificar_next(txt))
        tags = ", ".join(t.get("label", "") for t in e.get("tags", []))
        if not sessoes:
            motivos["sem sessões na página"] = motivos.get("sem sessões na página", 0) + 1
        for s in sessoes:
            if not s["data"] or s["ate"] < HOJE.isoformat():
                motivos["já passou"] = motivos.get("já passou", 0) + 1; continue
            if s["data"] > limite.isoformat():
                motivos["depois da janela"] = motivos.get("depois da janela", 0) + 1; continue
            unidade = s["unidade"] if s["unidade"] in SESC_RIO else e.get("location")
            if unidade not in SESC_RIO:
                motivos["unidade fora do Rio: " + s["unidade"]] = motivos.get("unidade fora do Rio: " + s["unidade"], 0) + 1; continue
            bairro, regiao = SESC_RIO[unidade]
            # sessão de um dia, ou período (exposição, temporada): o período aparece por inteiro
            quando = f"{s['data']} {s['hora']}" if s["ate"] == s["data"] else \
                f"de {s['data']} até {s['ate']}, {s['hora'] or 'horário na página'} (em cartaz na edição que termina em {edicao_fim(HOJE).isoformat()})"
            linhas.append(f"{quando} | {limpo(e.get('title'))} | {unidade} ({bairro}, {regiao}) | "
                          f"{s['precos'] or 'preço não informado'} | {tags}"
                          f"{' | acessibilidade: ' + s['acessibilidade'] if s['acessibilidade'] else ''} | {url} | sinopse oficial: {sin}")
    linhas.sort()
    with open(os.path.join(pasta, "FAGENDA_sesc.txt"), "w", encoding="utf-8") as f:
        f.write(f"FAGENDA_sesc | Sesc RJ — programação oficial das unidades na cidade do Rio (agenda dedicada do Todos os Rios) | {base}/programacao\n")
        f.write("## sessões, por data\n")
        f.write("\n".join(linhas) + "\n")
    return {"paginas": pagina, "eventos_no_rio_em_cartaz": len(candidatos), "eventos_no_rio_ja_encerrados": arquivo,
            "linhas": len(linhas), "fora": motivos, "falhas": falhas}


# ------------------------------------------------------------------ Arte que Acontece
def arte_que_acontece(pasta):
    base = "https://artequeacontece.com.br/wp-json/tribe/events/v1/events"
    fim_ed = edicao_fim(HOJE)
    expos, falhas, pagina, total = [], [], 1, 1
    while pagina <= total and pagina <= 20:
        st, txt = baixar(f"{base}?per_page=50&page={pagina}&categories=rio-de-janeiro"
                         f"&start_date={HOJE.year - 1}-01-01&end_date={HOJE.year + 1}-12-31")
        time.sleep(PAUSA)
        if st != 200:
            falhas.append(f"página {pagina} (código {st})"); break
        try:
            d = json.loads(txt)
        except ValueError:
            falhas.append(f"página {pagina} ilegível"); break
        total = int(d.get("total_pages") or 1)
        for e in d.get("events", []):
            ini, fim = (e.get("start_date") or "")[:10], (e.get("end_date") or "")[:10]
            if not fim or fim < HOJE.isoformat() or ini > (HOJE + dt.timedelta(days=62)).isoformat():
                continue
            v = e.get("venue") if isinstance(e.get("venue"), dict) else {}
            lugar = limpo(v.get("venue", ""))
            endereco = ", ".join(x for x in [limpo(v.get("address", "")), limpo(v.get("city", ""))] if x)
            titulo = limpo(e.get("title", ""))
            if (v.get("city") and "rio de janeiro" not in limpo(v.get("city")).lower()) or FORA_DO_RIO.search(titulo + " " + lugar + " " + endereco):
                continue
            expos.append((ini, fim, titulo, lugar, endereco, limpo(e.get("cost", "")), e.get("url", ""),
                          limpo(e.get("description", ""), 400)))
        pagina += 1
    expos = list({x[6] or x[2]: x for x in expos}.values())  # sem repetição
    expos.sort(key=lambda x: (x[1], x[2]))
    with open(os.path.join(pasta, "FAGENDA_arteacontece.txt"), "w", encoding="utf-8") as f:
        f.write("FAGENDA_arteacontece | Arte que Acontece — exposições em cartaz no Rio (radar de fatos: escreva a ficha a partir "
                "da fonte oficial do espaço; sem copiar texto do portal) | https://artequeacontece.com.br/eventos/category/rio-de-janeiro/\n")
        f.write("## exposições em cartaz\n")
        for ini, fim, titulo, lugar, endereco, custo, url, desc in expos:
            # a data de fechamento da edição faz a peneira enxergar a exposição em toda edição em que estiver aberta
            f.write(f"em cartaz na edição que termina em {fim_ed.isoformat()} | aberta de {ini} até {fim} | {titulo} | "
                    f"{lugar}{', ' + endereco if endereco else ''} | {custo or 'preço não informado'} | {url} | resumo do portal (só para localizar os fatos): {desc}\n")
    return {"exposicoes_no_rio": len(expos), "falhas": falhas}


# ------------------------------------------------------------------ Revista CONCERTO
CONCERTO = "https://www.concerto.com.br/roteiros"
JANELA_CONCERTO = 62   # a revista publica o roteiro com cerca de um mês de antecedência; lemos dois meses


def _campo_concerto(li, classe, rotulo):
    m = re.search(r'<span class="%s[^"]*">\s*<label>%s:\s*</label>(.*?)</span>' % (classe, rotulo), li, re.S)
    return limpo(m.group(1)) if m else ""


def concerto(pasta):
    """Roteiro diário da Revista CONCERTO (desde 24/11/2026): uma página por dia, com todas as apresentações
    de música clássica do país. Ficam só as da cidade do Rio."""
    linhas, falhas, dias_lidos, dias_com_rio, vistos = [], [], 0, 0, set()
    for k in range(JANELA_CONCERTO + 1):
        dia = HOJE + dt.timedelta(days=k)
        url = f"{CONCERTO}/{dia.isoformat()}"
        st, txt = baixar(url)
        time.sleep(PAUSA)
        if st != 200:
            falhas.append(f"{dia.isoformat()} (código {st})")
            if len(falhas) >= 5:
                break
            continue
        dias_lidos += 1
        achou = False
        for li in re.findall(r'<li>\s*<span class="title">(.*?)</li>', txt, re.S):
            cidade = _campo_concerto(li, "premise", "Cidade")
            if not cidade.lower().startswith("rio de janeiro"):
                continue
            m = re.search(r'<label class="date-title">(.*?)</label>(.*?)</span>', li, re.S)
            hora = limpo(m.group(1)).replace("h", ":") if m else ""
            titulo = limpo(m.group(2)) if m else ""
            d = re.search(r'<span class="description">(.*?)</span>', li, re.S)
            programa = limpo(d.group(1), 900) if d else ""
            local = _campo_concerto(li, "premise", "Local")
            endereco = _campo_concerto(li, "address", "Endereço")
            ingressos = _campo_concerto(li, "ingressos", "Ingressos")
            chave = (dia, hora, titulo, local)
            if not titulo or chave in vistos:
                continue
            vistos.add(chave); achou = True
            linhas.append(f"{dia.isoformat()} {hora} | {titulo} | {local}{' — ' + endereco if endereco else ''} | "
                          f"ingressos: {ingressos or 'não informado'} | {url} | programa segundo a revista: {programa}")
        dias_com_rio += achou
    with open(os.path.join(pasta, "FAGENDA_concerto.txt"), "w", encoding="utf-8") as f:
        f.write("FAGENDA_concerto | Revista CONCERTO — roteiro de música clássica na cidade do Rio (radar de fatos: "
                "escreva a ficha com texto próprio; se houver fonte oficial do espaço na ronda, ela prevalece) | " + CONCERTO + "\n")
        f.write("## apresentações, por data\n")
        f.write("\n".join(linhas) + "\n")
    if dias_lidos and not linhas:
        falhas.append("nenhuma apresentação no Rio em dois meses (o formato da página pode ter mudado)")
    return {"dias_lidos": dias_lidos, "dias_com_rio": dias_com_rio, "apresentacoes_no_rio": len(linhas), "falhas": falhas}


# ------------------------------------------------------------------ Riotur (Calendário Oficial)
RIOTUR = "https://riotur.rio"
RIOTUR_MESES = 13          # páginas mexidas nos últimos 13 meses (o Clássicos do Brasil 2026 foi cadastrado em junho)
RIOTUR_MAX_BAIXAR = 300    # páginas novas ou alteradas baixadas por ronda; o resto fica para a próxima
RIOTUR_PAUSA = 1.0
RIOTUR_CACHE = "riotur-cache.json"
MESES_PT = {m: i + 1 for i, m in enumerate("janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split())}
MESES_PT["marco"] = 3
# Títulos quase sempre fora dos critérios (comércio, esporte, Natal de shopping): vão para um grupo à parte, só de títulos
RIOTUR_FORA = re.compile(r"shopping|\bmall\b|barrashopping|village ?mall|uptown|corrida|maratona|\bnfl\b|futebol|campeonato|"
                         r"brasileir[aã]o|libertadores|torneio|regata|\bsurf|v[oô]lei|beach tennis|\bufc\b|gran ?prix|"
                         r"black friday|outlet|bazar|breakfast|botecar|gastron[oô]mic|restaurante", re.I)


def _cache_anterior(pasta):
    """Lê o cache da ronda anterior (guardado no ramo temporário coleta-bruta, fora da linha principal)."""
    p = os.path.join(pasta, RIOTUR_CACHE)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    import subprocess
    for ref in ("origin/coleta-bruta", None):
        try:
            if ref is None:
                subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin", "coleta-bruta"], check=True, timeout=120,
                               capture_output=True)
                ref = "FETCH_HEAD"
            out = subprocess.run(["git", "show", f"{ref}:{RIOTUR_CACHE}"], check=True, capture_output=True, timeout=120).stdout
            return json.loads(out.decode("utf-8"))
        except Exception:
            continue
    return {}


def _texto_riotur(pagina):
    """Título e texto do evento numa página do calendário da Riotur (o miolo fica entre o botão de compartilhar e o rodapé)."""
    m = re.search(r'og:title" content="([^"]*)', pagina)
    titulo = limpo(m.group(1)) if m else ""
    corpo = re.sub(r"<script.*?</script>|<style.*?</style>", " ", pagina, flags=re.S)
    corpo = limpo(corpo)
    a, b = corpo.find("Meu rio -->"), corpo.find("Sobre o Rio O que faz")
    texto = corpo[a + 11:b].strip() if a >= 0 and b > a else ""
    return titulo, texto[:4000]


def _datas_riotur(texto, referencia):
    """Datas citadas no texto ("28 e 29 de novembro", "05/12", "de 15/02 a 2/03"). Sem ano, vale o ano que deixa a data
    mais perto da última atualização da página (no máximo 3 meses antes dela)."""
    t, achadas = texto.lower(), set()
    for d, m, a in re.findall(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", t):
        achadas.add((int(d), int(m), int(a) + (2000 if len(a) == 2 else 0) if a else None))
    meses = "|".join(MESES_PT)
    for grupo, mes, ano in re.findall(r"((?:\d{1,2}º?(?:\s*(?:,|e|a|até|-|–)\s*)?)+)\s+de\s+(" + meses + r")(?:\s+de\s+(\d{4}))?", t):
        for d in re.findall(r"\d{1,2}", grupo):
            achadas.add((int(d), MESES_PT[mes], int(ano) if ano else None))
    datas = set()
    for d, m, a in achadas:
        if not (1 <= m <= 12 and 1 <= d <= 31):
            continue
        anos = [a] if a else [referencia.year, referencia.year + 1]
        for ano in anos:
            try:
                x = dt.date(ano, m, d)
            except ValueError:
                continue
            if a or x >= referencia - dt.timedelta(days=90):
                datas.add(x)
                break
    return sorted(datas)


def _servico(texto):
    i = texto.find("Serviço")
    return texto[i:i + 700] if i >= 0 else texto[-500:]


def riotur(pasta):
    """Calendário oficial de eventos da Riotur (desde 25/11/2026). Radar de fatos: o calendário só monta a grade
    no navegador, mas cada evento tem página pública, listada nos mapas do site com a data da última alteração.
    O robô baixa só as páginas novas ou alteradas desde a ronda anterior (o resto vem do cache), tira as datas do
    texto e junta numa linha por evento (a Riotur costuma criar uma página por sessão)."""
    falhas, cache = [], _cache_anterior(pasta)
    st, indice = baixar(f"{RIOTUR}/sitemap_index.xml")
    time.sleep(RIOTUR_PAUSA)
    mapas = re.findall(r"<loc>([^<]*evento_calendario-sitemap\d*\.xml)</loc>", indice or "") if st == 200 else []
    if not mapas:
        falhas.append(f"índice do site sem os mapas do calendário (código {st})")
    paginas = {}
    for mapa in mapas:
        st, xml = baixar(mapa)
        time.sleep(RIOTUR_PAUSA)
        if st != 200:
            falhas.append(f"{mapa.rsplit('/', 1)[-1]} (código {st})"); continue
        for url, lm in re.findall(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", xml):
            paginas[url] = lm
    corte = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=31 * RIOTUR_MESES)).isoformat()
    recentes = {u: lm for u, lm in paginas.items() if lm >= corte}
    novo_cache, baixadas, adiadas = {}, 0, 0
    for url, lm in sorted(recentes.items(), key=lambda x: x[1], reverse=True):
        antigo = cache.get(url)
        if antigo and antigo.get("lastmod") == lm:
            novo_cache[url] = antigo; continue
        if baixadas >= RIOTUR_MAX_BAIXAR:
            adiadas += 1
            if antigo:
                novo_cache[url] = antigo
            continue
        st, txt = baixar(url)
        time.sleep(RIOTUR_PAUSA)
        baixadas += 1
        if st != 200:
            falhas.append(f"{url.rsplit('/', 2)[-2]} (código {st})")
            if antigo:
                novo_cache[url] = antigo
            continue
        titulo, texto = _texto_riotur(txt)
        novo_cache[url] = {"lastmod": lm, "titulo": titulo, "texto": texto}
    json.dump(novo_cache, open(os.path.join(pasta, RIOTUR_CACHE), "w", encoding="utf-8"), ensure_ascii=False)

    limite = HOJE + dt.timedelta(days=62)
    eventos, sem_data = {}, 0
    for url, c in novo_cache.items():
        ref = dt.date.fromisoformat(c["lastmod"][:10])
        datas = _datas_riotur(c["texto"], ref)
        if not datas:
            sem_data += 1; continue
        if datas[-1] < HOJE or datas[0] > limite:
            continue
        chave = re.sub(r"[^a-z0-9]", "", re.sub(r"^(espet[aá]culo|exposi[cç][aã]o)\s*", "", c["titulo"].lower()))[:40] or url
        ev = eventos.setdefault(chave, {"titulo": c["titulo"], "datas": set(), "paginas": []})
        ev["datas"].update(datas)
        ev["paginas"].append((url, c["texto"]))
    escopo, fora = [], []
    for ev in eventos.values():
        datas = sorted(ev["datas"])
        textos = " || ".join(f"{u} :: {_servico(t)}" for u, t in sorted(ev["paginas"]))
        linha = (f"datas citadas: {', '.join(d.isoformat() for d in datas)} | {ev['titulo']} | "
                 f"{len(ev['paginas'])} página(s) | serviço segundo a Riotur: {textos}")
        (fora if RIOTUR_FORA.search(ev["titulo"]) else escopo).append((datas[0], linha))
    with open(os.path.join(pasta, "FAGENDA_riotur.txt"), "w", encoding="utf-8") as f:
        f.write("FAGENDA_riotur | Riotur — calendário oficial de eventos da cidade (radar de fatos: confirme na fonte do espaço "
                "ou da produção; preço da Riotur só com confirmação; texto próprio) | " + RIOTUR + "/editorial/calendario-eventos/\n")
        f.write("## eventos, por data (datas tiradas do texto da página; confira)\n")
        f.write("\n".join(l for _, l in sorted(escopo)) + "\n")
        f.write("## provavelmente fora dos critérios (comércio, esporte, Natal de shopping): leia só os títulos\n")
        f.write("\n".join(l for _, l in sorted(fora)) + "\n")
    if mapas and not novo_cache:
        falhas.append("nenhuma página de evento lida (o formato do site pode ter mudado)")
    return {"paginas_no_site": len(paginas), "paginas_do_ultimo_ano": len(recentes), "baixadas_hoje": baixadas,
            "adiadas_para_a_proxima_ronda": adiadas, "sem_data_no_texto": sem_data, "eventos_na_janela": len(escopo),
            "provavelmente_fora": len(fora), "falhas": falhas[:20]}


# ------------------------------------------------------------------ Bilheteria Digital (desde 25/11/2026)
BD = "https://www.bilheteriadigital.com"


def _bd_texto(pagina):
    c = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", pagina, flags=re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ¦ ", c)))


def bilheteria_digital(pasta):
    """Ticketeira que vende grandes shows e festas do Rio (Clássicos do Brasil, Marina da Glória, quadras de samba).
    A lista do estado traz título, dia, cidade e lugar; a página de cada evento traz o texto de apresentação, com
    local, endereço, período e horário, e a tabela de preços. Plataforma: lida como as outras ticketeiras."""
    falhas = []
    st, lista = baixar(f"{BD}/RJ")
    time.sleep(PAUSA)
    if st != 200:
        return {"falhas": [f"lista do RJ (código {st})"]}
    itens = []
    for li in re.findall(r'<li class="box-li-evento.*?</li>', lista, re.S):
        campos = [x.strip() for x in html.unescape(re.sub(r"<[^>]+>", "|", li)).split("|") if x.strip()]
        link = re.search(r'href="(/[^"]+)"', li)
        if len(campos) >= 4 and link and campos[2].startswith("Rio de Janeiro"):
            itens.append({"titulo": campos[0], "dia": campos[1], "lugar": campos[3], "url": BD + link.group(1)})
    linhas = []
    for it in itens:
        st, pag = baixar(it["url"])
        time.sleep(PAUSA)
        if st != 200:
            falhas.append(f"{it['url'].rsplit('/', 1)[-1]} (código {st})"); continue
        t = _bd_texto(pag)
        a, b = t.find("¦ Informações ¦"), t.find("¦ Ver mais ¦")
        info = re.sub(r"(\s*¦\s*)+", " · ", t[a + 15:b] if a >= 0 and b > a else "").strip(" ·")
        precos = re.findall(r"¦ ([^¦]{2,60}?) ¦ (?:¦ )*LOTE[^¦]*¦ .*?VALOR ¦ (?:¦ )*R\$ ¦ ([\d.,]+)", t)
        tabela = "; ".join(f"{n.strip()}: R$ {v}" for n, v in precos[:8]) or "sem tabela de preços na página"
        linhas.append(f"{it['dia']} | {it['titulo']} | {it['lugar']} | {it['url']} | preços: {tabela} | {info[:1500]}")
    with open(os.path.join(pasta, "FPLAT_bilheteriadigital.txt"), "w", encoding="utf-8") as f:
        f.write("FPLAT_bilheteriadigital | Bilheteria Digital — eventos na cidade do Rio (venda oficial; texto de apresentação "
                "da produção: sinopse sempre própria) | " + BD + "/RJ\n")
        f.write("\n".join(linhas) + "\n")
    if not itens:
        falhas.append("nenhum evento na cidade do Rio na lista (o formato do site pode ter mudado)")
    return {"eventos_no_rj": len(re.findall(r'class="box-li-evento', lista)), "na_cidade_do_rio": len(itens),
            "lidos": len(linhas), "falhas": falhas[:20]}


# ------------------------------------------------------------------ AllEvents (desde 25/11/2026)
AE = "https://allevents.in/rio-de-janeiro"
AE_PAGINAS = 6
AE_CATEGORIAS = ("live-music", "theatre", "exhibitions", "art", "performances", "festivals", "dance", "parties",
                 "comedy", "kids", "workshops")
# Fever (Candlelight, Ballet of Lights, Jazz Room) já é lida direto; congressos, negócios e esporte não entram
AE_JA_LIDO = re.compile(r"candlelight|ballet of lights|jazz room|\bfever\b", re.I)
AE_FORA = re.compile(r"conference|confer[eê]ncia|congresso|summit|f[oó]rum|semin[aá]rio|webinar|networking|happy hour|"
                     r"recruitment|feira de (?:neg|emprego)|expo\b|investid|startup|empreendedor|\bia para|marketing|"
                     r"run ?club|running|corrida|maratona|trail|trein[aã]o|retreat|bazar|outlet|curso\b|mentoria|imers[aã]o|\[oficina\]|"
                     r"meetup|hackathon|builders|yoga|coffe+ office|sem filas|excurs[aã]o|confraterniza|grand opening|sales\b|"
                     r"palpiteiros|gest[aã]o|consult[oó]rio|pacientes", re.I)


def _ae_eventos(pagina):
    achados = []
    for bloco in re.findall(r'<script type="application/ld\+json">(.*?)</script>', pagina, re.S):
        try:
            d = json.loads(bloco)
        except ValueError:
            continue
        for it in (d if isinstance(d, list) else [d]):
            lista = [x.get("item", {}) for x in it.get("itemListElement", [])] if it.get("@type") == "ItemList" else [it]
            achados += [e for e in lista if isinstance(e, dict) and e.get("@type") == "Event"]
    return achados


def allevents(pasta):
    """Agregador internacional de eventos (radar de fatos). As páginas da cidade trazem os eventos em dados
    estruturados (nome, datas, lugar, link, começo da descrição), sem horário. Muito comércio e muita coisa
    corporativa: o robô separa o que a Fever já cobre e o que parece congresso ou negócio."""
    falhas, eventos = [], {}
    enderecos = [f"{AE}/all?page={n}" for n in range(1, AE_PAGINAS + 1)] + [f"{AE}/{c}" for c in AE_CATEGORIAS]
    for url in enderecos:
        st, pag = baixar(url)
        time.sleep(PAUSA)
        if st != 200:
            falhas.append(f"{url.rsplit('/', 1)[-1]} (código {st})"); continue
        for e in _ae_eventos(pag):
            eventos.setdefault(e.get("url") or e.get("name"), e)
    limite = HOJE + dt.timedelta(days=62)
    escopo, fora, ja_lido, fora_da_cidade = [], [], 0, 0
    for e in eventos.values():
        ini, fim = (e.get("startDate") or "")[:10], (e.get("endDate") or e.get("startDate") or "")[:10]
        try:
            d0, d1 = dt.date.fromisoformat(ini), dt.date.fromisoformat(fim)
        except ValueError:
            continue
        if d1 < HOJE or d0 > limite:
            continue
        lugar = e.get("location") if isinstance(e.get("location"), dict) else {}
        end = lugar.get("address") if isinstance(lugar.get("address"), dict) else {}
        local_txt = " ".join(str(end.get(k, "")) for k in ("streetAddress", "addressLocality"))
        if FORA_DO_RIO.search(local_txt) or re.search(r"s[aã]o jo[aã]o de meriti|duque de caxias|nova igua[cç]u|"
                                                        r"s[aã]o gon[cç]alo|maric[aá]|cabo frio", local_txt, re.I):
            fora_da_cidade += 1; continue
        nome = limpo(e.get("name"))
        if AE_JA_LIDO.search(nome):
            ja_lido += 1; continue
        linha = (f"{ini}{' a ' + fim if fim != ini else ''} | {nome} | {limpo(lugar.get('name'))} — "
                 f"{limpo(end.get('streetAddress'))} | {e.get('url', '')} | {limpo(e.get('description'), 400)}")
        (fora if AE_FORA.search(nome) else escopo).append((ini, linha))
    with open(os.path.join(pasta, "FAGENDA_allevents.txt"), "w", encoding="utf-8") as f:
        f.write("FAGENDA_allevents | AllEvents — agregador de eventos no Rio (radar de fatos: sem horário; confirme tudo na "
                "fonte do espaço, da produção ou da venda oficial; texto próprio) | " + AE + "\n")
        f.write("## eventos, por data\n" + "\n".join(l for _, l in sorted(escopo)) + "\n")
        f.write("## provavelmente fora dos critérios (congresso, negócios, esporte, cursos): leia só os títulos\n")
        f.write("\n".join(l for _, l in sorted(fora)) + "\n")
    if not eventos:
        falhas.append("nenhum evento lido (o formato do site pode ter mudado)")
    return {"eventos_lidos": len(eventos), "na_janela": len(escopo), "provavelmente_fora": len(fora),
            "ja_lidos_pela_fever": ja_lido, "fora_da_cidade": fora_da_cidade, "falhas": falhas[:20]}


# ------------------------------------------------------------------ Visit Rio (desde 25/11/2026)
VISITRIO = "https://visitrio.com.br"
VISITRIO_PAGINAS = 4       # 10 matérias por página do feed: cobre mais ou menos o último mês e meio
VISITRIO_FORA = re.compile(r"padaria|restaurante|bares?\b|gastron|hot[eé]is|hotel|breakfast|takeaway|janelinhas|"
                           r"botecar|praias?\b|trilha|passeio de barco|shopping|uphill|corrida|maratona|onde (?:ficar|comer)", re.I)


def visitrio(pasta):
    """Portal de turismo do Rio (radar de fatos). As páginas do site barram robôs, mas o feed de notícias é aberto e
    traz o texto inteiro de cada matéria (Réveillon, Árvore da Lagoa, turnês que passam pela cidade)."""
    falhas, itens = [], {}
    for n in range(1, VISITRIO_PAGINAS + 1):
        st, xml = baixar(f"{VISITRIO}/feed/" + (f"?paged={n}" if n > 1 else ""))
        time.sleep(PAUSA)
        if st != 200:
            if n == 1:
                falhas.append(f"feed (código {st})")
            break
        for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
            link = re.search(r"<link>([^<]+)</link>", it)
            titulo = re.search(r"<title>(.*?)</title>", it, re.S)
            data = re.search(r"<pubDate>([^<]+)</pubDate>", it)
            corpo = re.search(r"<content:encoded><!\[CDATA\[(.*?)\]\]>", it, re.S)
            if link and titulo:
                itens[link.group(1)] = (limpo(titulo.group(1)), data.group(1)[5:16] if data else "",
                                         limpo(corpo.group(1) if corpo else "", 2500))
    escopo, fora = [], []
    for url, (titulo, data, texto) in itens.items():
        datas = _datas_riotur(texto, HOJE - dt.timedelta(days=60))
        futuras = [d for d in datas if HOJE <= d <= HOJE + dt.timedelta(days=62)]
        linha = (f"publicada em {data} | {titulo} | {url} | datas citadas: "
                 f"{', '.join(d.isoformat() for d in futuras) or 'nenhuma à frente'} | {texto}")
        (escopo if futuras and not VISITRIO_FORA.search(titulo) else fora).append(linha)
    with open(os.path.join(pasta, "FAGENDA_visitrio.txt"), "w", encoding="utf-8") as f:
        f.write("FAGENDA_visitrio | Visit Rio — matérias do portal de turismo (radar de fatos: confirme na fonte oficial; "
                "texto próprio) | " + VISITRIO + "\n")
        f.write("## matérias com datas nos próximos dois meses\n" + "\n".join(escopo) + "\n")
        f.write("## guias de turismo, gastronomia e matérias sem data à frente: leia só os títulos\n")
        f.write("\n".join(l.split(" | datas citadas")[0] for l in fora) + "\n")
    if not itens and not falhas:
        falhas.append("feed sem matérias (o formato do site pode ter mudado)")
    return {"materias_lidas": len(itens), "com_datas_a_frente": len(escopo), "falhas": falhas[:20]}


def main(pasta):
    os.makedirs(pasta, exist_ok=True)
    resumo = {"feito_em": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    for nome, func in (("sesc", sesc), ("arte_que_acontece", arte_que_acontece), ("concerto", concerto), ("riotur", riotur),
                       ("bilheteria_digital", bilheteria_digital), ("allevents", allevents), ("visitrio", visitrio)):
        try:
            resumo[nome] = func(pasta)
        except Exception as erro:  # uma agenda nunca derruba a ronda
            resumo[nome] = {"falhas": [f"erro: {type(erro).__name__}: {erro}"]}
    json.dump(resumo, open(os.path.join(pasta, "agendas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Agendas dedicadas:", json.dumps(resumo, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "coleta-bruta")
