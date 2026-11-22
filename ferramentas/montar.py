#!/usr/bin/env python3
"""O robô do Todos os Rios: monta a edição do dia e o site, sem inteligência artificial.

Roda todo dia no GitHub, depois da ronda das fontes, e de novo sempre que chegam fichas novas.
1. Descobre a edição de hoje (quinta a quarta). Às quintas a edição nova abre sozinha.
2. Tira da base (dados/fichas.json) tudo o que cai na edição, de hoje em diante: sessões que já
   passaram saem e exposições encerradas somem.
3. Lê da Sympla os eventos de data única da rede municipal que reconhece com segurança (robo_sympla.py).
4. Refaz a grade de cinema a partir da extração da Ingresso.com, quando ela vem junto.
5. Completa "A boa" dos dias sem destaque escolhido pela redação, com uma regra fixa e pública.
6. Gera o site, os calendários, os dados abertos e o relatório (ferramentas/gerar.py).

Uso: python3 ferramentas/montar.py [caminho do plataformas.json]
"""
import datetime as dt
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base  # noqa: E402

# Decisão editorial de 22/11/2026: toda ficha de evento é redigida e conferida pela redação (Claude).
# As fichas automáticas (robo_sympla.py: rede municipal na Sympla e palcos públicos na Fever) ficam
# desligadas e só voltam como último recurso, se a redação ficar inviável pelo limite de uso.
# O robô continua cuidando do mecânico: coleta, grade de cinema, montagem, publicação e "A boa" de reserva.
FICHAS_DO_ROBO = False
import gerar  # noqa: E402

PUBLICOS = gerar.PUBLICOS


def da_edicao(e, ed, desde):
    """Cópia da ficha só com o que cai na edição de 'desde' até o fim; None se nada cair."""
    e = dict(e)
    if e["tipo"] == "evento":
        e["sessoes"] = [s for s in e.get("sessoes", []) if desde <= s["data"] <= ed["fim"]]
        return e if e["sessoes"] else None
    c = e.get("cartaz") or {}
    if (c.get("fim") and c["fim"] < desde) or (c.get("inicio") and c["inicio"] > ed["fim"]):
        return None
    return e


def status(e, conf, graves):
    pend = [r for r in conf if r["id"] == e["id"] and not r.get("resolucao")]
    return "a_confirmar" if (pend or e["id"] in graves) else "conferido"


def porque_automatico(e):
    """Linha factual para um destaque escolhido pela regra (sem adjetivo, só o que a ficha diz)."""
    onde = e["bairro"] or e["local"]
    if e["gratis"]:
        return (f"De graça, em {onde}.", f"Free, in {onde}.", f"Gratis, en {onde}.")
    if gerar.faixa(e) == "popular":
        return (f"A preço popular, em {onde}.", f"Low-priced, in {onde}.", f"A precio popular, en {onde}.")
    return (f"Em {onde}.", f"In {onde}.", f"En {onde}.")


REGIOES_BOA = ("Centro", "Zona Sul", "Zona Norte", "Zona Oeste")  # decisão de 22/11/2026: 4 por dia, uma em cada


def escolher_destaques(eventos, dia, n=4):
    """Regra fixa para os dias sem destaque da redação (decisão de 22/11/2026): 4 destaques, um no Centro,
    um na Zona Sul, um na Zona Norte e um na Zona Oeste. Dentro de cada região, prioridade para o grátis e o
    barato e para os espaços públicos, variando as áreas. Região sem opção é completada por outra (Sudoeste antes)."""
    pool = [e for e in eventos if e["tipo"] == "evento" and not e.get("automatica") and not e.get("robo") and e["status"] == "conferido"
            and any(s["data"] == dia for s in e["sessoes"])]

    def nota(e):
        return (e["faixa"] in ("gratis", "popular")) * 4 + any(k in e["local"] for k in PUBLICOS) * 2
    pool.sort(key=lambda e: (-nota(e), e["id"]))
    esc, areas, locais = [], set(), set()

    def pega(cands):
        for exigir_area_nova in (True, False):
            for e in cands:
                if e in esc or e["local"] in locais:
                    continue
                if exigir_area_nova and set(e["areas"]) <= areas:
                    continue
                esc.append(e); areas.update(e["areas"]); locais.add(e["local"])
                return True
        return False
    for r in REGIOES_BOA:
        pega([e for e in pool if e["regiao"] == r])
    for r in ("Zona Sudoeste",) + REGIOES_BOA:  # completa o que faltou
        while len(esc) < n and pega([e for e in pool if e["regiao"] == r]):
            pass
    return esc[:n]


def main(plataformas=None):
    dia = base.hoje()
    ed = base.edicao_de(dia)
    pasta = os.path.join(base.DADOS, "edicoes", ed["id"])
    os.makedirs(pasta, exist_ok=True)

    if FICHAS_DO_ROBO and plataformas and os.path.exists(plataformas):  # fichas automáticas (desligadas: ver FICHAS_DO_ROBO)
        import robo_sympla
        try:
            robo_sympla.main(plataformas)
        except Exception as erro:  # o robô da Sympla nunca impede a publicação
            print("ALARME: o leitor automático da Sympla falhou:", erro)
    fichas = base.ler(base.ARQ_FICHAS, {"fichas": []})["fichas"]
    ids_base = {f["id"] for f in fichas}
    vetos = {v["id"] for v in base.ler(os.path.join(base.DADOS, "vetos.json"), {"vetos": []})["vetos"]}
    robo = [f for f in base.ler(os.path.join(base.DADOS, "robo.json"), {"fichas": []})["fichas"]
            if f["id"] not in ids_base and f["id"] not in vetos] if FICHAS_DO_ROBO else []  # a ficha da redação vale mais
    fichas = fichas + robo
    conf = base.ler(base.ARQ_CONF, {"resultado": []})["resultado"]
    dest_base = base.ler(base.ARQ_DEST, {"dias": {}})

    eventos = [x for x in (da_edicao(e, ed, dia) for e in fichas) if x]
    eventos.sort(key=lambda e: (e["sessoes"][0]["data"] + e["sessoes"][0]["hora"]) if e["sessoes"] else "0", reverse=False)
    ids = {e["id"] for e in eventos}
    base.gravar(os.path.join(pasta, "eventos.json"), {"edicao": ed, "eventos": eventos})
    base.gravar(os.path.join(pasta, "conferencia.json"),
                {"resultado": [r for r in conf if r["id"] in ids]})

    # cinema: refeito a cada ronda; sem extração nova, fica o da última ronda (com as sessões passadas cortadas)
    cine = os.path.join(pasta, "cinema.json")
    if plataformas and os.path.exists(plataformas):
        subprocess.run([sys.executable, "-I", os.path.join(base.RAIZ, "ferramentas", "redacao", "cinema.py"),
                        ed["id"], plataformas], check=True)
    elif os.path.exists(cine):
        c = base.ler(cine, {"fichas": []})
        c["fichas"] = [x for x in (da_edicao(f, ed, dia) for f in c["fichas"]) if x]
        base.gravar(cine, c)

    # "A boa": a escolha da redação vale; dia sem escolha recebe a regra fixa
    graves = {i for i, _, g in gerar.conferencia_mecanica(ed, eventos) if g == "alta"}
    for e in eventos:
        e["status"] = status(e, conf, graves)
        e["faixa"] = gerar.faixa(e)
    por_id = {e["id"]: e for e in eventos}
    dias, novas_trad, auto = {}, [], []
    d = dt.date.fromisoformat(dia)
    while d.isoformat() <= ed["fim"]:
        k = d.isoformat()
        lista = [x for x in dest_base["dias"].get(k, []) if x["id"] in por_id]
        if not lista:
            for e in escolher_destaques(eventos, k):
                pt, en, es = porque_automatico(e)
                lista.append({"id": e["id"], "porque": pt, "automatico": True})
                novas_trad.append({"pt": pt, "en": en, "es": es})
            if lista:
                auto.append(k)
        if lista:
            dias[k] = lista
        d += dt.timedelta(days=1)
    if novas_trad:
        sys.path.insert(0, os.path.join(base.RAIZ, "ferramentas", "redacao"))
        import traduzir
        traduzir.gravar(novas_trad)
    # "A boa do mês" (desde 22/11/2026): escolha da redação, só com o que ainda está por vir; sem escolha, não aparece
    mes = [x for x in dest_base.get("mes", []) if x["id"] in por_id]
    base.gravar(os.path.join(pasta, "destaques.json"),
                {"criterios_versao": dest_base.get("criterios_versao", "2026-11-15"), "dias": dias, "mes": mes, "automaticos": auto})

    gerar.main(ed["id"])
    print(f"Edição {ed['id']} montada para {dia}: {len(eventos)} fichas da redação"
          + f" (das quais {len([e for e in eventos if e.get('robo')])} automáticas da Sympla)"
          + (f"; A boa pela regra fixa em {', '.join(auto)}" if auto else ""))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
