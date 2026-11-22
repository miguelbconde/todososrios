"""Peças comuns ao robô (montar.py) e à entrega das fichas (entregar.py).

A programação mora numa base permanente, dados/fichas.json: uma ficha por evento ou exposição, com
todas as sessões que a fonte informou. A edição da semana (quinta a quarta) não é escrita à mão:
o robô a monta todo dia a partir da base, cortando o que já passou.
"""
import datetime as dt
import hashlib
import json
import os
import re
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "dados")
ARQ_FICHAS = os.path.join(DADOS, "fichas.json")
ARQ_CONF = os.path.join(DADOS, "conferencia.json")
ARQ_DEST = os.path.join(DADOS, "destaques.json")
ARQ_ENTREGAS = os.path.join(DADOS, "entregas.json")
BRT = dt.timezone(dt.timedelta(hours=-3))  # Rio, sem horário de verão
MESES = "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split()


def hoje():
    """Data de hoje no Rio (AAAA-MM-DD). A variável HOJE permite simular outro dia nos testes."""
    return os.environ.get("HOJE") or dt.datetime.now(BRT).date().isoformat()


JANELA_DIAS = 60  # decisão de 22/11/2026: o site mostra até dois meses à frente, não mais uma edição semanal


def edicao_de(dia):
    """Programação no ar: de hoje até JANELA_DIAS à frente (decisão de 22/11/2026).
    O identificador continua sendo a quinta da semana, só para nomear a pasta de trabalho."""
    d = dt.date.fromisoformat(dia)
    semana = d - dt.timedelta(days=(d.weekday() - 3) % 7)
    fim = d + dt.timedelta(days=JANELA_DIAS)
    titulo = f"Programação de hoje até {fim.day} de {MESES[fim.month - 1]} de {fim.year}"
    return {"id": semana.isoformat(), "inicio": d.isoformat(), "fim": fim.isoformat(), "titulo": titulo}


def slug(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def novo_id(titulo, local):
    return "f-" + hashlib.sha1((slug(titulo) + "|" + slug(local)).encode()).hexdigest()[:10]


def ler(caminho, padrao):
    return json.load(open(caminho, encoding="utf-8")) if os.path.exists(caminho) else padrao


def gravar(caminho, obj):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":  # python3 ferramentas/base.py  -> hoje e a edição de hoje
    e = edicao_de(hoje())
    print(hoje(), e["id"], e["inicio"], e["fim"])
