#!/usr/bin/env python3
"""Fichas automáticas da rede pública, tiradas da Sympla sem IA.

Equipamentos da Prefeitura (arenas, areninhas, lonas, teatros, centros culturais) vendem ou distribuem
ingressos pela Sympla, com o organizador "Município do Rio de Janeiro". Esses eventos chegam com nome,
local, endereço, dia e hora. O robô transforma em ficha só o que é seguro:
  - organizador público (Município do Rio de Janeiro);
  - evento de um dia só, com hora (temporadas sem os dias da semana ficam para a redação);
  - local que o robô reconhece (aprendido das fichas da redação ou do cadastro de locais);
  - nada que a triagem da Sympla descarte (cursos, esporte, negócios etc.);
  - título que indique a área (música, teatro, infantil...) e não tenha cara de apresentação de escola;
  - nada que a redação já tenha publicado (mesmo dia, mesmo local, título parecido) ou vetado.
A ficha traz só fatos. A linha descritiva é montada dos fatos; a redação pode trocá-la por uma
sinopse própria entregando uma correção com o mesmo código.

Desde 22/11/2026, também da Fever: só os eventos dos palcos públicos que vendem por lá (Theatro Municipal,
Sala Mário Tavares, Sala Cecília Meireles), com dia e hora tirados dos dados estruturados de cada evento,
local que o robô reconhece e área clara no título. Visitas guiadas, oficinas e o resto da Fever ficam para a redação.

Grava dados/robo.json, refeito a cada ronda.
Uso: python3 ferramentas/robo_sympla.py <plataformas.json>
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "coleta"))
import base  # noqa: E402
import triagem_sympla as tri  # noqa: E402

ARQ_ROBO = os.path.join(base.DADOS, "robo.json")
ARQ_LOCAIS = os.path.join(base.DADOS, "locais.json")
ARQ_VETOS = os.path.join(base.DADOS, "vetos.json")
ESCOLA = re.compile(r"\b(alunos|alunas|academia|escola de danca|formatura|encerramento|mostra cpa|projeto social|turma|"
                    r"festival de danca|danc|bailarin|ballet|circo|oficina|escolar|final de ano|musical de natal|\b20\d\d\b|"
                    r"solidari|vida ativa|terceira idade|reuniao|assembleia|audiencia)")
# Teatro sem indicação clara só entra sozinho quando o palco é profissional (teatros municipais);
# nas arenas e areninhas, "espetáculo" costuma ser apresentação de escola: fica para a redação.
COMEDIA = re.compile(r"\b(stand.?up|comedia|humor)\b")
PUBLICO = re.compile(r"^\s*munic[ií]pio d[eo] rio de janeiro", re.I)
VAZIAS = set("de do da dos das e a o arena areninha cultural carioca centro teatro municipal espaco rio janeiro lona "
             "casa sala museu biblioteca cidade".split())

AREAS = [  # (área, padrão no título, sem acento)
    ("Infantil", r"\b(infantil|crianca|criancas|kids|contacao|fantoches|bonecos|palhac|reino encantado|domingo das criancas)"),
    ("Cinema", r"\b(cinema|cineclube|filme|curta|documentario|sessao de cinema|mostra de cinema)\b"),
    ("Livros & Debates", r"\b(sarau|poesia|slam|livro|leitura|lancamento|debate|palestra|roda de conversa|seminario|bate-papo)\b"),
    ("Festas & Feiras", r"\b(baile|festa|feira|charme|bloco|cortejo|arraia)\b"),
    ("Artes Visuais", r"\b(exposicao|mostra de arte|galeria|vernissage|fotografia)\b"),
    ("Música", r"\b(show|samba|choro|pagode|roda|forro|jazz|blues|mpb|rap|funk|rock|concerto|orquestra|tributo|musical|cantor|cantora|banda|sertanej|reggae|homenagem)\b"),
    ("Teatro", r"\b(teatro|peca|espetaculo|danca|circo|comedia|stand.?up|monologo|performance|humor|ballet|bale|opera)\b"),
]


def chave_local(nome):
    return frozenset(t for t in base.slug(nome).split("-") if t not in VAZIAS and len(t) > 1)


def aprender_locais(fichas):
    """Cadastro de locais: nome -> endereço, bairro, região. Vem das fichas da redação e de dados/locais.json."""
    locais = {}
    for f in fichas:
        if f.get("endereco") and f.get("bairro") and f.get("regiao"):
            locais.setdefault(chave_local(f["local"]), {k: f[k] for k in ("local", "endereco", "bairro", "regiao")})
    for l in base.ler(ARQ_LOCAIS, {"locais": []})["locais"]:  # cadastro manual tem preferência
        locais[chave_local(l["local"])] = l
        for apelido in l.get("apelidos", []):
            locais[chave_local(apelido)] = l
    return {k: v for k, v in locais.items() if k}


def achar_local(nome, locais):
    k = chave_local(nome)
    if k in locais:
        return locais[k]
    melhor, nota = None, 0
    for chave, l in locais.items():
        comum = len(k & chave)
        if comum and comum == min(len(k), len(chave)) and comum > nota:  # um nome contém o outro
            melhor, nota = l, comum
    return melhor


def areas_de(titulo):
    t = tri.n(titulo)
    return [a for a, p in AREAS if re.search(p, t)][:2]


def parecido(a, b):
    ta = set(base.slug(a).split("-")) - VAZIAS
    tb = set(base.slug(b).split("-")) - VAZIAS
    return bool(ta & tb)


def main(plataformas):
    p = base.ler(plataformas, {})
    eventos = p.get("sympla", {}).get("eventos", [])
    fichas = base.ler(base.ARQ_FICHAS, {"fichas": []})["fichas"]
    locais = aprender_locais(fichas)
    ja = {}
    for f in fichas:
        for s in f.get("sessoes", []):
            ja.setdefault(s["data"], []).append(f)

    saida, sem_local, repetidos, outros, escola, sem_area, vetados = {}, {}, 0, 0, 0, 0, 0
    vetos = {v["id"] for v in base.ler(ARQ_VETOS, {"vetos": []})["vetos"]}
    for e in eventos:
        if not PUBLICO.search(e.get("organizador") or ""):
            continue
        d_ini, h_ini = tri.hora_rio(e["inicio"])
        d_fim, _ = tri.hora_rio(e["fim"])
        if d_ini != d_fim or not h_ini:
            outros += 1; continue
        alvo = tri.n(" ".join([e["titulo"], e["local"], e["organizador"]]))
        titulo_n = tri.n(e["titulo"])
        if re.search(tri.CULTURA, titulo_n):
            fora = re.search(tri.FORA[0][1], titulo_n)
        else:
            fora = any(re.search(r, alvo) for _, r in tri.FORA)
        if fora:
            outros += 1; continue
        if ESCOLA.search(titulo_n):
            escola += 1; continue
        areas = areas_de(e["titulo"])
        if not areas:
            sem_area += 1; continue
        l = achar_local(e["local"], locais)
        if l and areas == ["Teatro"] and not (re.search(r"\bteatro\b", tri.n(l["local"])) or COMEDIA.search(titulo_n)):
            escola += 1; continue
        if not l:
            sem_local[e["local"]] = sem_local.get(e["local"], 0) + 1; continue
        if any(f["local"] == l["local"] and (parecido(f["titulo"], e["titulo"])
               or h_ini in {x["hora"] for x in f["sessoes"] if x["data"] == d_ini}) for f in ja.get(d_ini, [])):
            repetidos += 1; continue
        titulo = re.sub(r"\s+", " ", e["titulo"]).strip()
        if titulo.isupper():
            titulo = titulo.title()
        fid = base.novo_id(titulo, l["local"])
        if fid in saida:  # mesmo evento em outro dia: junta as sessões
            saida[fid]["sessoes"].append({"data": d_ini, "hora": h_ini})
            continue
        if fid in vetos:
            vetados += 1; continue
        saida[fid] = dict(
            id=fid, titulo=titulo, areas=areas, tipo="evento", local=l["local"], endereco=l["endereco"],
            bairro=l["bairro"], regiao=l["regiao"], sessoes=[{"data": d_ini, "hora": h_ini}], cartaz=None,
            preco_texto="Ingresso pela Sympla", preco_min=None, preco_max=None, gratis=False,
            classificacao="", acessibilidade="", na_rua=False,
            sinopse=f"Programação de {l['local']}, equipamento cultural da Prefeitura, em {l['bairro']}.",
            fonte="Sympla (extração do Todos os Rios)", link=e["link"],
            trecho_fonte=f"Sympla · {e['titulo']} · {d_ini} {h_ini} · {e['local']}, {e['endereco']} · organizador: {e['organizador']}",
            nota_redacao="Ficha automática, montada dos dados da Sympla sem redação de IA. A Sympla não informa o preço nesta listagem.",
            robo=True)
    n_fever = fever(p, locais, ja, vetos, saida, sem_local)
    for f in saida.values():
        f["sessoes"].sort(key=lambda s: (s["data"], s["hora"]))
    base.gravar(ARQ_ROBO, {"feito_em": p.get("feito_em"), "fichas": sorted(saida.values(), key=lambda f: f["sessoes"][0]["data"]),
                           "sem_local": dict(sorted(sem_local.items(), key=lambda x: -x[1]))})
    print(f"Robô da Sympla: {len(saida)} fichas da rede municipal; {repetidos} já estavam na redação; "
          f"{sum(sem_local.values())} em {len(sem_local)} locais que o robô ainda não conhece; {sem_area} sem área clara e "
          f"{escola} com cara de apresentação de escola ou atividade não cultural (ficam para a redação); "
          f"{vetados} vetados pela redação; {outros} temporadas ou fora dos critérios. Fever (palcos públicos): {n_fever} fichas")


PALCO_PUBLICO_FEVER = re.compile(r"theatro municipal|sala mario tavares|sala cecilia meireles")
FORA_FEVER = re.compile(r"\b(visita|oficina|tour|cartao-presente|workshop|aula)")


def fever(p, locais, ja, vetos, saida, sem_local):
    """Fichas automáticas dos palcos públicos que vendem pela Fever. Devolve quantas fichas fez."""
    feitos = 0
    for e in p.get("fever", {}).get("eventos", []):
        local_n = tri.n(e.get("local", ""))
        titulo_n = tri.n(e.get("titulo", ""))
        if not PALCO_PUBLICO_FEVER.search(local_n) or FORA_FEVER.search(titulo_n):
            continue
        if any(re.search(r, titulo_n) for _, r in tri.FORA):
            continue
        areas = areas_de(e["titulo"])
        if not areas:
            continue
        # sessões: dos dados estruturados de cada evento ("AAAA-MM-DD HH:MM, HH:MM"); sem elas, só evento de um dia
        sessoes = []
        for d in e.get("datas", []):
            m = re.match(r"(\d{4}-\d{2}-\d{2})\s+(.*)", d)
            if m:
                sessoes += [{"data": m.group(1), "hora": h.strip()} for h in m.group(2).split(",") if re.fullmatch(r"\d{2}:\d{2}", h.strip())]
        if not sessoes:
            d_ini, h_ini = tri.hora_rio(e.get("inicio", ""))
            d_fim, _ = tri.hora_rio(e.get("fim", ""))
            if d_ini == d_fim and h_ini:
                sessoes = [{"data": d_ini, "hora": h_ini}]
        if not sessoes:
            continue
        l = achar_local(e["local"], locais)
        if not l:
            sem_local[e["local"]] = sem_local.get(e["local"], 0) + 1; continue
        sessoes = [s for s in sessoes if not any(f["local"] == l["local"] and (parecido(f["titulo"], e["titulo"])
                   or s["hora"] in {x["hora"] for x in f["sessoes"] if x["data"] == s["data"]}) for f in ja.get(s["data"], []))]
        if not sessoes:
            continue
        titulo = re.sub(r"\s+", " ", e["titulo"]).strip(" -–")
        titulo = titulo[:1].upper() + titulo[1:]
        fid = base.novo_id(titulo, l["local"])
        if fid in vetos or fid in saida:
            continue
        saida[fid] = dict(
            id=fid, titulo=titulo, areas=areas, tipo="evento", local=l["local"], endereco=l["endereco"],
            bairro=l["bairro"], regiao=l["regiao"], sessoes=sorted({(s["data"], s["hora"]) for s in sessoes}), cartaz=None,
            preco_texto="Ingresso pela Fever", preco_min=None, preco_max=None, gratis=False,
            classificacao="", acessibilidade="", na_rua=False,
            sinopse=f"Programação de {l['local']}, palco público, em {l['bairro']}.",
            fonte="Fever (extração do Todos os Rios)", link=e["link"],
            trecho_fonte=f"Fever · {e['titulo']} · {'; '.join(e.get('datas', [])) or e.get('inicio', '')} · {e['local']}, {e.get('endereco', '')}",
            nota_redacao="Ficha automática, montada dos dados estruturados da Fever sem redação de IA. O preço da Fever ('a partir de') pode ser de setor especial: não é publicado.",
            robo=True)
        saida[fid]["sessoes"] = [{"data": d, "hora": h} for d, h in saida[fid]["sessoes"]]
        feitos += 1
    return feitos


if __name__ == "__main__":
    main(sys.argv[1])
