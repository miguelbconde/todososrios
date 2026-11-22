#!/usr/bin/env python3
"""Fichas de cinema montadas sem IA, a partir da extração da Ingresso.com.

Lê o plataformas.json da ronda (ramo coleta-bruta) e grava dados/edicoes/<edição>/cinema.json:
uma ficha por filme e por cinema, com as sessões que caem dentro da edição. A ficha só traz fatos
(título, direção, país, ano, duração, classificação, datas, horários, sala, preço) e uma linha
descritiva montada desses fatos; nenhum texto da plataforma é copiado. O gerador do site junta
estas fichas às da redação.
Uso: python3 cinema.py <edição AAAA-MM-DD> <caminho do plataformas.json>
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def reais(v):
    return ("R$ %.2f" % v).replace(".", ",").replace(",00", "")


def descricao(f):
    partes = []
    if f.get("direcao"):
        partes.append(f"Direção de {f['direcao']}.")
    dados = [x for x in (f.get("pais"), str(f["ano"]) if f.get("ano") else "",
                         f"{f['duracao_min']} min" if f.get("duracao_min") else "") if x]
    if dados:
        partes.append(", ".join(dados) + ".")
    if f.get("titulo_original") and f["titulo_original"].lower() != f["titulo"].lower():
        partes.insert(0, f"Título original: {f['titulo_original']}.")
    return " ".join(partes) or "Sessões de cinema."


PAISES = {  # nomes de país como vêm da plataforma -> (inglês, espanhol); os que faltarem ficam em português
    "Brasil": ("Brazil", "Brasil"), "Estados Unidos": ("United States", "Estados Unidos"), "EUA": ("United States", "Estados Unidos"),
    "França": ("France", "Francia"), "Itália": ("Italy", "Italia"), "Alemanha": ("Germany", "Alemania"),
    "Reino Unido": ("United Kingdom", "Reino Unido"), "Inglaterra": ("England", "Inglaterra"), "Espanha": ("Spain", "España"),
    "Portugal": ("Portugal", "Portugal"), "Argentina": ("Argentina", "Argentina"), "México": ("Mexico", "México"),
    "Japão": ("Japan", "Japón"), "Coreia do Sul": ("South Korea", "Corea del Sur"), "China": ("China", "China"),
    "Canadá": ("Canada", "Canadá"), "Austrália": ("Australia", "Australia"), "Bélgica": ("Belgium", "Bélgica"),
    "Irlanda": ("Ireland", "Irlanda"), "Índia": ("India", "India"), "Chile": ("Chile", "Chile"), "Colômbia": ("Colombia", "Colombia"),
    "Arábia Saudita": ("Saudi Arabia", "Arabia Saudita"), "Dinamarca": ("Denmark", "Dinamarca"), "Suécia": ("Sweden", "Suecia"),
    "Noruega": ("Norway", "Noruega"), "Polônia": ("Poland", "Polonia"), "Irã": ("Iran", "Irán"), "Rússia": ("Russia", "Rusia"),
    "Holanda": ("Netherlands", "Países Bajos"), "Países Baixos": ("Netherlands", "Países Bajos"), "Suíça": ("Switzerland", "Suiza"),
    "Áustria": ("Austria", "Austria"), "Uruguai": ("Uruguay", "Uruguay"), "Peru": ("Peru", "Perú"), "Grécia": ("Greece", "Grecia"),
}


def descricao_lang(f, lang):
    k = 0 if lang == "en" else 1
    pais = ", ".join(PAISES.get(x.strip(), (x.strip(), x.strip()))[k] for x in (f.get("pais") or "").split(",") if x.strip())
    partes = []
    if f.get("titulo_original") and f["titulo_original"].lower() != f["titulo"].lower():
        partes.append(("Original title: " if k == 0 else "Título original: ") + f["titulo_original"] + ".")
    if f.get("direcao"):
        partes.append(("Directed by " if k == 0 else "Dirección de ") + f["direcao"] + ".")
    dados = [x for x in (pais, str(f["ano"]) if f.get("ano") else "", f"{f['duracao_min']} min" if f.get("duracao_min") else "") if x]
    if dados:
        partes.append(", ".join(dados) + ".")
    return " ".join(partes) or ("Film screenings." if k == 0 else "Sesiones de cine.")


def main(edicao, caminho):
    pasta = os.path.join(RAIZ, "dados", "edicoes", edicao)
    ed = json.load(open(os.path.join(pasta, "eventos.json"), encoding="utf-8"))["edicao"]
    p = json.load(open(caminho, encoding="utf-8"))
    ing = p["ingresso"]
    grupos = {}
    for s in ing["sessoes"]:
        if not (ed["inicio"] <= s["data"] <= ed["fim"]) or not s["hora"]:
            continue
        grupos.setdefault((s["cinema_id"], s["filme_id"]), []).append(s)
    fichas = []
    for (cid, fid), ss in sorted(grupos.items(), key=lambda x: (ing["cinemas"][x[0][0]]["nome"], ing["filmes"][x[0][1]]["titulo"])):
        c, f = ing["cinemas"][cid], ing["filmes"][fid]
        ss = sorted(ss, key=lambda s: (s["data"], s["hora"]))
        sess, vistos = [], set()
        for s in ss:
            if (s["data"], s["hora"]) not in vistos:
                vistos.add((s["data"], s["hora"]))
                # link de compra da sessão, limpo (sem o código de parceria que a plataforma acrescenta)
                sess.append({"data": s["data"], "hora": s["hora"]} | (
                    {"compra": f"https://checkout.ingresso.com/?sessionId={s['sessao_id']}"} if s.get("sessao_id", "").isdigit() else {}))
        precos = sorted({s["preco"] for s in ss if isinstance(s.get("preco"), (int, float)) and s["preco"] > 0})
        if precos:
            texto = reais(precos[0]) if len(precos) == 1 else f"{reais(precos[0])} a {reais(precos[-1])}"
            pmin, pmax = precos[0], precos[-1]
        else:
            texto, pmin, pmax = "", None, None
        trecho = f"Ingresso.com · {c['nome']} · {f['titulo']} · " + "; ".join(
            f"{s['data']} {s['hora']} {s.get('sala','')} {reais(s['preco']) if s.get('preco') else ''}".strip() for s in ss)
        fichas.append(dict(
            titulo=f["titulo"], areas=["Cinema"], tipo="evento", local=c["nome"], endereco=c["endereco"],
            bairro=c["bairro"], regiao=c["regiao"], sessoes=sess, cartaz=None,
            preco_texto=(texto + " (preço da plataforma)") if texto else "", preco_min=pmin, preco_max=pmax,
            gratis=False, classificacao=f.get("classificacao", ""), acessibilidade="", na_rua=False,
            sinopse=descricao(f), sinopse_en=descricao_lang(f, "en"), sinopse_es=descricao_lang(f, "es"), fonte="Ingresso.com (extração do Todos os Rios)",
            link=f.get("link") or c.get("site") or "", link_espaco=c.get("site", ""),
            trecho_fonte=trecho[:600],
            nota_redacao="Ficha montada automaticamente a partir dos dados da Ingresso.com, sem redação de IA.",
            automatica=True, id=f"{edicao}-cine-{cid}-{fid}"))
    json.dump({"feito_em": p.get("feito_em"), "fichas": fichas},
              open(os.path.join(pasta, "cinema.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(fichas), "fichas de cinema,", sum(len(x["sessoes"]) for x in fichas), "sessões")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
