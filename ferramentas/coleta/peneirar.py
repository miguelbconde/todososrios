# Peneira da ronda: separa, do texto bruto de cada fonte, só os trechos que falam de datas
# da semana da edição (com algumas linhas de contexto), para a redação das fichas.
# Uso: python3 peneirar.py <pasta com os F*.txt> <início AAAA-MM-DD> <fim AAAA-MM-DD> <arquivo de saída> [vistos.json]
# Com o quinto argumento, a peneira vira "só o que mudou": mostra apenas os trechos com alguma linha que
# não estava nas rondas anteriores (a linha nova vem marcada com ★) e grava, ao lado da saída, um arquivo
# <saída>.vistos com a lista atualizada. Esse arquivo guarda só códigos das linhas (não o texto dos sites);
# depois de redigir as fichas, copie-o por cima de dados/coleta/vistos.json.
import re, sys, os, glob, datetime, json, hashlib

MESES = "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split()
ABR = [m[:3] for m in MESES]

def padroes(inicio, fim):
    dias = []
    d = inicio
    while d <= fim:
        dias.append(d); d += datetime.timedelta(days=1)
    ps = []
    for d in dias:
        dd, m = d.day, d.month
        ps += [r"\b0?%d\s*[/.]\s*0?%d\b" % (dd, m),
               r"\b0?%d\s*/\s*(%s|%s)\b" % (dd, MESES[m-1], ABR[m-1]),   # "25 / nov" (Beco das Garrafas e outros)
               r"\b0?%d(º)?\s*(de\s+)?(%s|%s)\b" % (dd, MESES[m-1], ABR[m-1]),
               r"\b(%s|%s)[a-z]*\.?\s+0?%d\b" % (ABR[m-1], ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"][m-1], dd),
               r"%04d-%02d-%02d" % (d.year, m, dd)]
        # faixas do tipo "20, 21 e 22 de novembro" ou "20 a 22/11"
        ps.append(r"\b0?%d\s*(,|e|a|–|-|até)\s*\d{1,2}(\s*(,|e|a|–|-)\s*\d{1,2})*\s*(/\s*0?%d\b|de\s+%s)" % (dd, m, MESES[m-1]))
    return re.compile("|".join("(?:%s)" % p for p in ps), re.I)

# Períodos que atravessam a janela sem citar nenhum dia dela (exposição de 10/10 a 15/02, por exemplo).
# Sem isto, a peneira deixava de fora as exposições em cartaz abertas antes de hoje e que acabam depois da janela.
_M = {m: i + 1 for i, m in enumerate(ABR)}
_MES = r"(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[a-zç]*\.?"
_DT_TXT = r"(\d{1,2})º?\s*(?:de\s+)?%s(?:\s*(?:de\s+)?(20\d\d))?" % _MES
_DT_NUM = r"(\d{1,2})[/.](\d{1,2})(?:[/.](\d{2,4}))?"
_SEP = r"\s*(?:-|–|—|a|até|>|ao)\s*"
_FAIXAS = [re.compile(_DT_TXT + _SEP + _DT_TXT, re.I), re.compile(_DT_NUM + _SEP + _DT_NUM, re.I)]
_ATE = re.compile(r"\b(?:at[ée]|em cartaz at[ée])\s+(?:o\s+dia\s+|dia\s+)?(?:" + _DT_TXT + "|" + _DT_NUM + ")", re.I)

def _data(d, m, y, ano_ref):
    try:
        m = _M[m[:3].lower()] if not str(m).isdigit() else int(m)
        y = int(y) if y else ano_ref
        if y < 100: y += 2000
        return datetime.date(y, m, int(d))
    except Exception:
        return None

def cobre_janela(linha, inicio, fim):
    """True se a linha traz um período que começa antes do fim da janela e termina depois do início."""
    if len(linha) > 1500:
        return False
    for r in _FAIXAS:
        for x in r.finditer(linha):
            b = _data(x[4], x[5], x[6], inicio.year)
            if b and not x[6] and b < inicio - datetime.timedelta(days=60):
                b = b.replace(year=b.year + 1)          # "até 15/02" visto em novembro é do ano seguinte
            a = _data(x[1], x[2], x[3], b.year if b else inicio.year)
            if a and b and a > b and not x[3]:
                a = a.replace(year=b.year - 1)
            if a and b and a <= fim and b >= inicio and (b - a).days < 500:
                return True
    for x in _ATE.finditer(linha):
        b = _data(x[1], x[2], x[3], inicio.year) if x[1] else _data(x[4], x[5], x[6], inicio.year)
        if b and not (x[3] or x[6]) and b < inicio - datetime.timedelta(days=60):
            b = b.replace(year=b.year + 1)
        folga = 400 if (x[3] or x[6]) else 100   # sem ano, "até 13 de junho" costuma ser texto velho
        if b and fim < b <= fim + datetime.timedelta(days=folga):
            return True   # "até" dentro da janela já é pego pelos padrões dos dias
    return False

_DATA_ANO = re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4}|\d{2})\b|"
                       r"\b(?:(\d{1,2})º?\s+(?:de\s+)?)?(jan|fev|feb|mar|abr|apr|mai|may|jun|jul|ago|aug|set|sep|out|oct|nov|dez|dec)[a-zç]*\.?"
                       r"(?:\s+(\d{1,2}))?,?\s+(?:de\s+)?(20\d\d)\b", re.I)
_MES_EN = {"feb": 2, "apr": 4, "may": 5, "aug": 8, "sep": 9, "oct": 10, "dec": 12}

def ano_de_outra_epoca(linha, inicio, fim):
    """True se todas as datas com ano da linha estão fora da janela ("02 de Dezembro de 2019", "13.11 - 13.12.2024",
    "dezembro 13, 2025", "16 de janeiro 2026" visto em novembro de 2026): arquivo de exposições passadas, notícia
    velha. Sem isso, o dia e o mês batiam e a linha passava. Ano solto no texto ("desde 2010") não conta."""
    datas, anos = [], set()
    for m in _DATA_ANO.finditer(linha):
        try:
            if m.group(1):
                a = int(m.group(3)); a = a + 2000 if a < 100 else a
                datas.append(datetime.date(a, int(m.group(2)), int(m.group(1))))
            else:
                a = int(m.group(7)); mes = m.group(5).lower()[:3]
                mes = _M.get(mes) or _MES_EN.get(mes)
                dia = m.group(4) or m.group(6)
                if dia:
                    datas.append(datetime.date(a, mes, int(dia)))
                else:
                    anos.add(a)
        except (ValueError, TypeError):
            continue
    if not datas and not anos:
        return False
    if any(inicio <= d <= fim + datetime.timedelta(days=400) for d in datas):
        return False
    if any(inicio.year <= a <= fim.year for a in anos):
        return False
    return True

def cod(fonte, linha):
    return hashlib.sha1((fonte + "|" + re.sub(r"\s+", " ", linha.strip())).encode("utf-8")).hexdigest()[:12]

def peneirar(pasta, inicio, fim, saida, contexto=4, vistos=None):
    pad = padroes(inicio, fim)
    antigos = set(json.load(open(vistos, encoding="utf-8")).get("linhas", [])) if vistos and os.path.exists(vistos) else set()
    agora = set(); fontes_novas = 0
    with open(saida, "w", encoding="utf-8") as out:
        for caminho in sorted(glob.glob(os.path.join(pasta, "F*.txt"))):
            linhas = open(caminho, encoding="utf-8", errors="replace").read().split("\n")
            cab = linhas[0] if linhas else ""
            fonte = os.path.basename(caminho)
            marcar = set(); pagina = {}; novas = set()
            atual = ""
            for i, l in enumerate(linhas):
                if l.startswith("## "): atual = l
                pagina[i] = atual
                if (pad.search(l) or cobre_janela(l, inicio, fim)) and not ano_de_outra_epoca(l, inicio, fim):
                    c = cod(fonte, l); agora.add(c)
                    if vistos and c in antigos: continue
                    novas.add(i)
                    for j in range(max(0, i-contexto), min(len(linhas), i+contexto+1)): marcar.add(j)
            if not marcar: continue
            fontes_novas += 1
            out.write("\n\n=================== %s\n" % cab)
            vistos = set(); ult = -9; pag_ult = None
            for i in sorted(marcar):
                l = linhas[i].strip()
                if not l or l in vistos: continue
                vistos.add(l)
                if pagina[i] != pag_ult:
                    out.write("\n%s\n" % pagina[i]); pag_ult = pagina[i]
                elif i - ult > 1: out.write("  ...\n")
                out.write(("★ " if vistos and i in novas else "") + l[:1200] + "\n"); ult = i
    if vistos:
        json.dump({"edicao": [str(inicio), str(fim)], "linhas": sorted(antigos | agora)},
                  open(saida + ".vistos", "w", encoding="utf-8"))
    print(f"{fontes_novas} fonte(s) com trechos" + (" novos" if vistos else ""), "->", saida)

if __name__ == "__main__":
    pasta, ini, fim, saida = sys.argv[1:5]
    vistos = sys.argv[5] if len(sys.argv) > 5 else None
    f = lambda s: datetime.date(*map(int, s.split("-")))
    peneirar(pasta, f(ini), f(fim), saida, vistos=vistos)
