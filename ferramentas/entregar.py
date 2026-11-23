#!/usr/bin/env python3
"""Entrega da redação: põe na base as fichas, conferências, destaques e traduções do dia.

A tarefa diária do Claude escreve um arquivo de entrega (JSON) e roda:
    python3 ferramentas/entregar.py <entrega.json>
Cada ficha passa por checagens automáticas. Ficha com problema grave é recusada (e explicada);
as outras entram. No fim, o programa monta a edição num teste e diz se o site sairia sem erro.
Quem publica é o robô do GitHub, quando a base chega ao repositório.

Para saber a seção da vez de "A boa" nos próximos 7 dias:
    python3 ferramentas/entregar.py vez

Para saber o código de uma ficha antes de entregar (útil nos apontamentos e destaques):
    python3 ferramentas/entregar.py id "<título>" "<local>"

Formato da entrega (todas as chaves são opcionais):
{
  "fichas": [ {ficha completa; sem "id" para ficha nova, com "id" para corrigir uma existente} ],
  "remover": [ {"id": "...", "motivo": "cancelado pela fonte em 22/11"} ],
  "vetar": [ {"id": "...", "motivo": "apresentação de escola"} ],   (fichas automáticas do robô, em dados/robo.json)
  "apontamentos": [ {"id": "...", "titulo": "...", "campo": "...", "veredito": "diverge|nao_encontrado|duvida",
                     "detalhe": "...", "resolucao": "Corrigido: ... | Mantido: ... | (vazio = a confirmar)"} ],
  "destaques": { "AAAA-MM-DD": [ {"id": "...", "porque": "..."} ] },
  "destaques_mes": [ {"id": "...", "porque": "..."} ],   ("As boas do mês": a lista inteira, que substitui a anterior)
  "traducoes": [ {"pt": "...", "en": "...", "es": "..."} ],
  "nota": "resumo de uma linha do que foi feito"
}
"""
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base  # noqa: E402
import gerar  # noqa: E402

OBRIG = ["titulo", "areas", "tipo", "local", "endereco", "bairro", "regiao", "sinopse", "fonte", "link", "trecho_fonte"]
PADRAO = {"cartaz": None, "sessoes": [], "preco_texto": "", "preco_min": None, "preco_max": None, "gratis": False,
          "classificacao": "", "acessibilidade": "", "na_rua": False, "nota_redacao": "", "aviso": ""}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def problemas(f, dia):
    p = []
    for k in OBRIG:
        if not f.get(k):
            p.append(f"falta {k}")
    if p:
        return p
    if not isinstance(f["areas"], list) or not set(f["areas"]) <= set(gerar.AREAS):
        p.append(f"área fora do padrão: {f['areas']} (use {', '.join(gerar.AREAS)})")
    if f["regiao"] not in gerar.REGIOES:
        p.append(f"região inválida: {f['regiao']}")
    if f["tipo"] == "evento":
        if not f.get("sessoes"):
            p.append("evento sem sessões")
        for s in f.get("sessoes", []):
            try:
                dt.date.fromisoformat(s["data"])
            except Exception:
                p.append(f"data inválida: {s}")
                continue
            if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", s.get("hora") or ""):
                p.append(f"hora inválida: {s}")
        if f.get("sessoes") and max(s["data"] for s in f["sessoes"]) < dia:
            p.append("todas as sessões já passaram")
    elif f["tipo"] == "cartaz":
        c = f.get("cartaz")
        if not isinstance(c, dict) or "horario" not in c:
            p.append('exposição sem "cartaz" {inicio, fim, horario}')
    else:
        p.append(f"tipo inválido: {f['tipo']}")
    if f.get("gratis") and (f.get("preco_max") or 0) > 0:
        p.append("marcada como grátis, mas tem preço")
    if not str(f["link"]).startswith("http"):
        p.append("link sem http")
    if f.get("aviso", "") not in ("", "dias"):
        p.append('aviso inválido: use "dias" (temporada sem os dias informados) ou deixe vazio')
    for k in ("sinopse", "trecho_fonte", "nota_redacao", "fonte"):
        if EMAIL.search(str(f.get(k) or "")):
            p.append(f"há um e-mail em {k}: dado pessoal não entra")
    if not 20 <= len(f["sinopse"]) <= 420:
        p.append("sinopse muito curta ou longa demais (20 a 420 caracteres)")
    return p


def main(caminho):
    dia = base.hoje()
    ent = json.load(open(caminho, encoding="utf-8"))
    dados = base.ler(base.ARQ_FICHAS, {"fichas": []})
    por_id = {f["id"]: f for f in dados["fichas"]}
    conf = base.ler(base.ARQ_CONF, {"resultado": []})
    dest = base.ler(base.ARQ_DEST, {"dias": {}})
    log = {"data": dia, "novas": 0, "corrigidas": 0, "recusadas": [], "removidas": 0}

    for f in ent.get("fichas", []):
        if f.get("id") and f["id"] in por_id:  # correção: vale o que veio, por cima do que havia
            alvo = dict(por_id[f["id"]]); alvo.update(f)
            p = problemas(alvo, dia)
            if p:
                log["recusadas"].append({"titulo": f.get("titulo") or alvo["titulo"], "motivos": p}); continue
            alvo["atualizado_em"] = dia
            por_id[f["id"]] = alvo; log["corrigidas"] += 1
            continue
        g = dict(PADRAO); g.update(f)
        p = problemas(g, dia)
        if p:
            log["recusadas"].append({"titulo": f.get("titulo", "(sem título)"), "motivos": p}); continue
        g["id"] = base.novo_id(g["titulo"], g["local"])
        if g["id"] in por_id:  # já existia: junta as sessões em vez de duplicar
            velho = por_id[g["id"]]
            if g["tipo"] == "evento":
                g["sessoes"] = sorted({(s["data"], s["hora"]) for s in velho.get("sessoes", []) + g["sessoes"]})
                g["sessoes"] = [{"data": d, "hora": h} for d, h in g["sessoes"]]
            g["entrou_em"] = velho.get("entrou_em", dia); g["atualizado_em"] = dia
            log["corrigidas"] += 1
        else:
            g["entrou_em"] = dia; log["novas"] += 1
        por_id[g["id"]] = g

    for r in ent.get("remover", []):
        if r.get("id") in por_id:
            por_id.pop(r["id"]); log["removidas"] += 1

    if ent.get("vetar"):
        arq = os.path.join(base.DADOS, "vetos.json")
        v = base.ler(arq, {"vetos": []})
        v["vetos"] += [dict(x, data=dia) for x in ent["vetar"] if x.get("id")]
        base.gravar(arq, v); log["vetadas"] = len(ent["vetar"])

    robo_ids = {f["id"] for f in base.ler(os.path.join(base.DADOS, "robo.json"), {"fichas": []})["fichas"]}
    novos_ap = [a for a in ent.get("apontamentos", []) if a.get("id") in por_id or a.get("id") in robo_ids]
    chaves = {(a["id"], a.get("campo")) for a in novos_ap}
    conf["resultado"] = [a for a in conf["resultado"] if (a["id"], a.get("campo")) not in chaves] + novos_ap
    ignorados = [a for a in ent.get("apontamentos", []) if a.get("id") not in por_id]

    for k, l in ent.get("destaques", {}).items():
        if k >= dia:
            dest["dias"][k] = [x for x in l if x.get("id") in por_id or x.get("id") in robo_ids]

    if "destaques_mes" in ent:  # "As boas do mês": o que vale planejar com antecedência (lista inteira, substitui a anterior)
        dest["mes"] = [x for x in ent["destaques_mes"] if x.get("id") in por_id]

    if ent.get("traducoes"):
        sys.path.insert(0, os.path.join(base.RAIZ, "ferramentas", "redacao"))
        import traduzir
        traduzir.gravar(ent["traducoes"])

    # a base guarda até 60 dias depois do fim de cada ficha
    limite = (dt.date.fromisoformat(dia) - dt.timedelta(days=60)).isoformat()
    def fim(f):
        if f["tipo"] == "evento":
            return max((s["data"] for s in f.get("sessoes", [])), default="0")
        return (f.get("cartaz") or {}).get("fim") or "9999"
    dados["fichas"] = sorted((f for f in por_id.values() if fim(f) >= limite), key=lambda f: f["id"])
    base.gravar(base.ARQ_FICHAS, dados)
    base.gravar(base.ARQ_CONF, conf)
    dest["dias"] = {k: v for k, v in sorted(dest["dias"].items()) if k >= limite}
    base.gravar(base.ARQ_DEST, dest)
    reg = base.ler(base.ARQ_ENTREGAS, {"entregas": []})
    log["nota"] = ent.get("nota", "")
    reg["entregas"] = (reg["entregas"] + [log])[-120:]
    base.gravar(base.ARQ_ENTREGAS, reg)

    print(f"Entrega de {dia}: {log['novas']} novas, {log['corrigidas']} corrigidas, {log['removidas']} removidas, "
          f"{len(log['recusadas'])} recusadas, {log.get('vetadas', 0)} automáticas vetadas.")
    for r in log["recusadas"]:
        print("  RECUSADA:", r["titulo"], "—", "; ".join(r["motivos"]))
    for a in ignorados:
        print("  apontamento sem ficha correspondente:", a.get("id"), a.get("titulo"))
    print("Teste de montagem do site:")
    import montar
    montar.main(None)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "id":
        print(base.novo_id(sys.argv[2], sys.argv[3]))
    elif len(sys.argv) == 2 and sys.argv[1] == "vez":  # a seção da vez de "A boa" nos próximos 7 dias
        fichas = base.ler(base.ARQ_FICHAS, {"fichas": []})["fichas"]
        hoje = dt.date.today()
        for i in range(1, 8):
            k = (hoje + dt.timedelta(days=i)).isoformat()
            pool = [f for f in fichas if f["tipo"] == "evento" and any(s["data"] == k for s in f.get("sessoes", []))]
            print(k, gerar.secao_da_vez(k, pool) or "(nenhuma seção com evento)")
    else:
        main(sys.argv[1])
