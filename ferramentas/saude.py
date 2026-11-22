#!/usr/bin/env python3
"""Boletim de saúde do Todos os Rios (sem IA). Roda no fim da ronda diária.

Escreve dados/coleta/saude.md e, se algo estiver errado, imprime linhas que começam com "ALARME:".
O GitHub transforma essas linhas num aviso (issue), que chega por e-mail à coordenação.
Uso: python3 ferramentas/saude.py [caminho do plataformas.json]
"""
import datetime as dt
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base  # noqa: E402

MIN_FONTES = 40          # abaixo disso, a ronda quebrou
DIAS_SEM_REDACAO = 2     # a partir daí, a tarefa diária do Claude parou


def main(plat=None):
    dia = base.hoje()
    alarmes, linhas = [], [f"# Boletim de saúde — {dia}", ""]

    r = base.ler(os.path.join(base.DADOS, "coleta", "resumo.json"), {})
    sit = Counter((f.get("situacao") or "").split(" (")[0].split(":")[0] for f in r.get("fontes", []))
    lidas = sit.get("coletada", 0)
    linhas += ["## Ronda das fontes", "", f"- Feita em: {r.get('feito_em', '?')}",
               f"- Lidas com datas: **{lidas}** de {len(r.get('fontes', []))} visitadas"]
    linhas += [f"- {k}: {v}" for k, v in sit.most_common() if k != "coletada"]
    if not r.get("feito_em", "").startswith(dia):
        alarmes.append(f"a ronda das fontes não rodou hoje (a última é de {r.get('feito_em', '?')})")
    elif lidas < MIN_FONTES:
        alarmes.append(f"só {lidas} fontes lidas com datas na ronda de hoje (o normal é mais de {MIN_FONTES})")

    linhas += ["", "## Plataformas de ingresso", ""]
    p = base.ler(plat, {}) if plat else {}
    n_cine = len(p.get("ingresso", {}).get("sessoes", []))
    n_sym = len(p.get("sympla", {}).get("eventos", []))
    if plat:
        linhas += [f"- Ingresso.com: {n_cine} sessões de cinema", f"- Sympla: {n_sym} eventos no Rio",
                   f"- Fever: {len(p.get('fever', {}).get('eventos', []))} eventos no Rio"]
    else:  # rodada só de publicação (entrega da redação): não há extração nova para contar
        linhas += ["- Sem extração nesta rodada (publicação de fichas entregues). Números da última ronda em `dados/coleta/plataformas.md`."]
    if plat and n_cine == 0:
        alarmes.append("a grade de cinema da Ingresso.com veio vazia")
    if plat and n_sym == 0:
        alarmes.append("a extração da Sympla veio vazia")

    robo = base.ler(os.path.join(base.DADOS, "robo.json"), {"fichas": [], "sem_local": {}})
    linhas += ["", "## Fichas automáticas (sem IA)", "",
               f"- Fichas automáticas: {len(robo['fichas'])} (desligadas desde 22/11/2026; toda ficha é da redação)",
               "- Locais da Sympla que o robô ainda não reconhece: " + (", ".join(f"{k} ({v})" for k, v in robo.get("sem_local", {}).items()) or "nenhum")]
    linhas += ["", "## Redação (tarefa diária do Claude)", ""]
    ent = base.ler(base.ARQ_ENTREGAS, {"entregas": []})["entregas"]
    ultima = max((e["data"] for e in ent), default="nunca")
    linhas.append(f"- Última entrega: {ultima}")
    for e in ent[-7:]:
        linhas.append(f"  - {e['data']}: {e.get('novas', e.get('fichas', 0))} novas, {e.get('corrigidas', 0)} corrigidas, "
                      f"{len(e.get('recusadas', []))} recusadas{(' — ' + e['nota']) if e.get('nota') else ''}")
    if ultima == "nunca" or (dt.date.fromisoformat(dia) - dt.date.fromisoformat(ultima)).days >= DIAS_SEM_REDACAO:
        alarmes.append(f"a tarefa diária do Claude não entrega fichas desde {ultima}; o site segue no ar, "
                       "mas só com o que o robô monta sozinho")

    fichas = base.ler(base.ARQ_FICHAS, {"fichas": []})["fichas"]
    ed = base.edicao_de(dia)
    na_ed = [f for f in fichas if (f["tipo"] == "cartaz" and ((f.get("cartaz") or {}).get("fim") or "9999") >= dia)
             or any(dia <= s["data"] <= ed["fim"] for s in f.get("sessoes", []))]
    reg = Counter(f["regiao"] for f in na_ed)
    linhas += ["", "## Edição no ar", "", f"- Fichas da redação de hoje até {ed['fim']}: **{len(na_ed)}**",
               "- Por região: " + ", ".join(f"{k} {v}" for k, v in reg.most_common()),
               f"- Fora da Zona Sul: {round(100 * (1 - reg.get('Zona Sul', 0) / max(len(na_ed), 1)))}%",
               f"- Grátis: {sum(1 for f in na_ed if f.get('gratis'))}"]

    linhas += ["", "## Alarmes", ""] + ([f"- {a}" for a in alarmes] or ["- Nenhum."])
    open(os.path.join(base.DADOS, "coleta", "saude.md"), "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    for a in alarmes:
        print("ALARME:", a)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
