#!/usr/bin/env python3
"""Triagem automática dos eventos da Sympla, sem IA.

Lê plataformas.json (saída de plataformas.py) e separa:
  FPLAT_sympla.txt        candidatos, em ordem de prioridade, lidos pela peneira e pela redação diária
  sympla-descartados.txt  o que a regra descartou, com o motivo (para auditoria)
Regras (critérios editoriais do plano diretor, seção 4):
  - descarta cursos, treinamentos, eventos corporativos e de negócios, esporte, gastronomia sem programação
    cultural, turismo e transporte, cultos e conferências religiosas, festas de boate e balada;
  - dá prioridade a equipamentos públicos e a espaços culturais (teatro, arena, areninha, centro cultural,
    museu, biblioteca, galeria) e a palavras de programação cultural (show, samba, choro, peça, espetáculo,
    sarau, exposição, lançamento, roda, contação);
  - o resto fica como candidato comum. A decisão final é da redação (com os mesmos critérios).
Uso: python3 triagem_sympla.py <pasta da ronda>
"""
import datetime as dt, json, os, re, sys, unicodedata


def n(s):
    return unicodedata.normalize("NFD", (s or "").lower()).encode("ascii", "ignore").decode()


FORA = [  # (motivo, padrão aplicado a título + local + organizador, sem acento)
    ("curso ou treinamento", r"\b(curso|treinamento|capacitacao|workshop|mentoria|imersao|masterclass|aula pratica|formacao profissional|certificacao|bootcamp)\b"),
    ("negócios ou corporativo", r"\b(empresa|empresarial|empreendedor|vendas|comercial|contabilidade|investimento|marketing|lideranca|networking|revenda|distribuidora|parceiros|b2b|startup|summit|congresso|day\b|feira de negocios)"),
    ("saúde, terapia ou autoajuda", r"\b(terapia|constelacao|bioenergia|coaching|autoconhecimento|meditacao guiada|biomed|saude|clinica|nutri)"),
    ("religioso", r"\b(igreja|culto|conferencia profetica|ministerio|retiro espiritual|louvor)\b"),
    ("esporte", r"\b(corrida|treino|futebol|estadio|beach tennis|campeonato|torneio|crossfit|jiu)\b"),
    ("gastronomia", r"\b(degustacao|risotto|brunch|rodizio|menu|jantar harmonizado|supermercado|steakhouse|churrasco)\b"),
    ("turismo ou transporte", r"\b(transporte|excursao|traslado|viagens|day use|passeio de barco)\b"),
    ("festa de boate ou balada", r"\b(club\b|boate|balada|after\b|open bar|camarote|pride\b.*\b23h|night\b|psytrance|rave)"),
    ("encontro social", r"\b(encontros casuais|speed dating|solteiros|karaoke)\b"),
    ("apresentação interna de escola", r"\b(encerramento \d{4}|turmas de|formatura|recital de alunos|mostra de alunos)\b"),
]
PUBLICO = r"\b(municipio|prefeitura|secretaria|governo do estado|funarj|ufrj|uerj|unirio|fiocruz|biblioteca|arena cultural|areninha|centro cultural|museu|memorial)\b"
CULTURA = r"\b(show|jazz das|samba|choro|pagode|roda|forro|jazz|blues|mpb|sarau|poesia|slam|teatro|peca|espetaculo|musical|danca|circo|exposicao|mostra|festival|lancamento|livro|contacao|cinema|cineclube|concerto|orquestra|tributo|homenagem|batalha|baile|jongo|maracatu|bloco)\b"


def hora_rio(iso):
    try:
        t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(dt.timezone(dt.timedelta(hours=-3)))
        return t.strftime("%Y-%m-%d"), t.strftime("%H:%M")
    except ValueError:
        return iso[:10], ""


def main(pasta):
    p = json.load(open(os.path.join(pasta, "plataformas.json"), encoding="utf-8"))
    eventos = p["sympla"]["eventos"]
    cand, fora = [], []
    for e in eventos:
        alvo = n(" ".join([e["titulo"], e["local"], e["organizador"]]))
        titulo = n(e["titulo"])
        if re.search(CULTURA, titulo):  # título com cara de programação cultural: só curso/treinamento no título descarta
            motivo = FORA[0][0] if re.search(FORA[0][1], titulo) else None
        else:
            motivo = next((m for m, r in FORA if re.search(r, alvo)), None)
        if not motivo and ("local a definir" in n(e["local"]) or not e["local"].strip()):
            motivo = "sem local definido"
        if not motivo:
            try:
                dias = (dt.date.fromisoformat(e["fim"][:10]) - dt.date.fromisoformat(e["inicio"][:10])).days
            except ValueError:
                dias = 0
            # temporada longa de teatro, dança ou circo entra (decisão de 22/11/2026): a redação lista de quinta a
            # domingo e põe o aviso de conferir os dias; o resto que só traz um período longo continua de fora
            if dias > 45 and not re.search(r"\b(teatro|peca|espetaculo|musical|danca|circo|comedia|stand.?up|monologo|opera)\b", alvo):
                motivo = "período longo, sem data precisa"
        if motivo:
            fora.append((motivo, e)); continue
        prio = 2 if re.search(PUBLICO, alvo) else 1 if re.search(CULTURA, alvo) or re.search(r"\bteatro\b", alvo) else 0
        cand.append((prio, e))
    cand.sort(key=lambda x: (-x[0], x[1]["inicio"]))
    rotulo = {2: "PRIORIDADE: equipamento público ou espaço cultural", 1: "cultural", 0: "verificar"}
    hoje = dt.date.today()
    quarta = hoje + dt.timedelta(days=(2 - hoje.weekday()) % 7)
    with open(os.path.join(pasta, "FPLAT_sympla.txt"), "w", encoding="utf-8") as f:
        f.write("FPLAT_sympla | Sympla (extração e triagem automática do Todos os Rios) | https://www.sympla.com.br/eventos/rio-de-janeiro-rj\n")
        for nivel in (2, 1, 0):
            f.write(f"## {rotulo[nivel]}\n")
            for pr, e in cand:
                if pr != nivel:
                    continue
                di, hi = hora_rio(e["inicio"]); df, hf = hora_rio(e["fim"])
                # temporada em andamento: a data da quarta faz a peneira enxergá-la toda semana enquanto durar
                temporada = f" | TEMPORADA em cartaz na semana até {quarta.isoformat()}: dias não informados" if di < hoje.isoformat() and df > di else ""
                f.write(f"{di} {hi} até {df} {hf} | {e['titulo']} | {e['local']}, {e['endereco']} {e['bairro']} | "
                        f"organizador: {e['organizador']} | {e['link']}{temporada}\n")
    with open(os.path.join(pasta, "sympla-descartados.txt"), "w", encoding="utf-8") as f:
        for m, e in sorted(fora, key=lambda x: x[0]):
            f.write(f"{m} | {e['inicio'][:10]} | {e['titulo']} | {e['local']} | {e['organizador']}\n")
    resumo = {k: sum(1 for pr, _ in cand if pr == k) for k in (2, 1, 0)}
    print(f"Sympla: {len(eventos)} eventos · {len(fora)} descartados pela regra · candidatos: "
          f"{resumo[2]} prioritários, {resumo[1]} culturais, {resumo[0]} a verificar")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "coleta-bruta")
