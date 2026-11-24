#!/usr/bin/env python3
"""Agendas dedicadas da ronda diária (desde 22/11/2026): Sesc RJ, Arte que Acontece e (desde 24/11/2026) Revista CONCERTO.

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
    return {"paginas": pagina, "eventos_no_rio": len(candidatos), "linhas": len(linhas), "fora": motivos, "falhas": falhas}


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


def main(pasta):
    os.makedirs(pasta, exist_ok=True)
    resumo = {"feito_em": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    for nome, func in (("sesc", sesc), ("arte_que_acontece", arte_que_acontece), ("concerto", concerto)):
        try:
            resumo[nome] = func(pasta)
        except Exception as erro:  # uma agenda nunca derruba a ronda
            resumo[nome] = {"falhas": [f"erro: {type(erro).__name__}: {erro}"]}
    json.dump(resumo, open(os.path.join(pasta, "agendas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Agendas dedicadas:", json.dumps(resumo, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "coleta-bruta")
