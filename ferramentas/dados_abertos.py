"""Dados abertos do Todos os Rios (decisão de 25/11/2026).

Gera, em docs/dados/:
  eventos.json      a base completa, uma ficha por atividade (formato de sempre)
  eventos.csv       uma linha por atividade, separada por ponto e vírgula (abre direto no Excel em português)
  sessoes.csv       uma linha por dia e hora de cada evento: o formato mais fácil para planilhas e programas
  datapackage.json  descrição dos arquivos no padrão Frictionless Data, lido por portais de dados abertos
  index.html        página "Dados abertos": o que há, endereços, campos, como usar, licença e crédito

Ficam de fora dos dados abertos: as notas internas da redação e o trecho copiado da fonte
(texto de terceiros, que não é nosso para licenciar). O link da fonte continua em cada ficha.
"""
import csv, html, json, os, datetime as dt

SITE = "https://todososrios.com.br/"
INTERNOS = ("nota_redacao", "trecho_fonte")

CAMPOS_EVENTOS = [
    ("id", "string", "Identificador estável da ficha"),
    ("titulo", "string", "Título da atividade"),
    ("areas", "string", "Seções, separadas por \" / \": Música, Teatro, Artes Visuais, Cinema, Livros & Debates, Festas & Feiras, Infantil"),
    ("tipo", "string", "\"evento\" (tem dias e horários) ou \"cartaz\" (exposição ou mostra em cartaz)"),
    ("datas_horarios", "string", "Dias e horários (AAAA-MM-DD HH:MM, separados por \" | \") ou período em cartaz"),
    ("local", "string", "Nome do lugar"),
    ("endereco", "string", "Endereço"),
    ("bairro", "string", "Bairro"),
    ("regiao", "string", "Centro, Zona Sul, Zona Sudoeste, Zona Norte ou Zona Oeste"),
    ("preco", "string", "Preço por extenso"),
    ("faixa", "string", "gratis, popular (inteira até R$ 40), ate80, acima80 ou nao_informado"),
    ("classificacao", "string", "Classificação indicativa"),
    ("acessibilidade", "string", "Recursos de acessibilidade informados pela fonte"),
    ("na_rua", "string", "\"sim\" quando acontece ao ar livre, em espaço público"),
    ("sinopse", "string", "Sinopse escrita pela redação (CC BY-SA 4.0)"),
    ("link", "string", "Link oficial da atividade ou da fonte"),
    ("fonte", "string", "De onde veio a informação"),
    ("status", "string", "conferido ou a_confirmar"),
]

CAMPOS_SESSOES = [
    ("id", "string", "Identificador da ficha (o mesmo de eventos.csv e eventos.json)"),
    ("data", "date", "Dia (AAAA-MM-DD)"),
    ("hora", "string", "Hora de início (HH:MM, horário de Brasília)"),
    ("titulo", "string", "Título da atividade"),
    ("areas", "string", "Seções, separadas por \" / \""),
    ("local", "string", "Nome do lugar"),
    ("endereco", "string", "Endereço"),
    ("bairro", "string", "Bairro"),
    ("regiao", "string", "Região da cidade"),
    ("preco", "string", "Preço por extenso"),
    ("gratis", "string", "\"sim\" quando a entrada é gratuita"),
    ("faixa", "string", "gratis, popular, ate80, acima80 ou nao_informado"),
    ("classificacao", "string", "Classificação indicativa"),
    ("na_rua", "string", "\"sim\" quando acontece ao ar livre, em espaço público"),
    ("link", "string", "Link oficial"),
    ("ingresso", "string", "Link de compra daquela sessão, quando houver"),
    ("status", "string", "conferido ou a_confirmar"),
]


def publicos(eventos):
    return [{k: v for k, v in e.items() if k not in INTERNOS} for e in eventos]


def escrever(out, ed, eventos, preco_legivel):
    pasta = os.path.join(out, "dados")
    os.makedirs(pasta, exist_ok=True)
    abertos = publicos(eventos)
    agora = dt.datetime.now(dt.timezone(dt.timedelta(hours=-3)))

    json.dump({"edicao": ed, "atualizado_em": agora.isoformat(timespec="minutes"),
               "licenca": "ODbL 1.0 (dados) · CC BY-SA 4.0 (textos)",
               "credito": "Todos os Rios (todososrios.com.br)", "documentacao": SITE + "dados/",
               "eventos": abertos},
              open(os.path.join(pasta, "eventos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    with open(os.path.join(pasta, "eventos.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([c for c, _, _ in CAMPOS_EVENTOS])
        for e in eventos:
            dh = " | ".join(f"{s['data']} {s['hora']}" for s in e["sessoes"]) if e["tipo"] == "evento" else \
                f"em cartaz até {e['cartaz']['fim'] or '—'} · {e['cartaz']['horario']}"
            w.writerow([e["id"], e["titulo"], " / ".join(e["areas"]), e["tipo"], dh, e["local"], e["endereco"],
                        e["bairro"], e["regiao"], preco_legivel(e), e["faixa"], e["classificacao"],
                        e["acessibilidade"], "sim" if e.get("na_rua") else "", e["sinopse"], e["link"], e["fonte"], e["status"]])

    n_sessoes = 0
    with open(os.path.join(pasta, "sessoes.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([c for c, _, _ in CAMPOS_SESSOES])
        linhas = []
        for e in eventos:
            if e["tipo"] != "evento":
                continue
            for s in e["sessoes"]:
                linhas.append([e["id"], s["data"], s["hora"], e["titulo"], " / ".join(e["areas"]), e["local"],
                               e["endereco"], e["bairro"], e["regiao"], preco_legivel(e), "sim" if e["gratis"] else "",
                               e["faixa"], e["classificacao"], "sim" if e.get("na_rua") else "", e["link"],
                               s.get("compra") or "", e["status"]])
        linhas.sort(key=lambda r: (r[1], r[2], r[3]))
        w.writerows(linhas)
        n_sessoes = len(linhas)

    def recurso(nome, arquivo, titulo, campos, fmt="csv"):
        r = {"name": nome, "path": SITE + "dados/" + arquivo, "title": titulo, "format": fmt,
             "mediatype": "text/csv" if fmt == "csv" else "application/json", "encoding": "utf-8"}
        if fmt == "csv":
            r["dialect"] = {"delimiter": ";"}
            r["schema"] = {"fields": [{"name": c, "type": t, "description": d} for c, t, d in campos]}
        return r

    json.dump({
        "name": "todos-os-rios-agenda-cultural-rio",
        "title": "Todos os Rios · Agenda cultural do Rio de Janeiro",
        "description": "Programação cultural do município do Rio de Janeiro, de hoje até dois meses à frente, "
                       "atualizada todos os dias. Música, teatro, artes visuais, cinema, livros e debates, festas "
                       "e feiras, programação infantil, em todas as regiões da cidade.",
        "homepage": SITE, "version": agora.date().isoformat(), "created": agora.isoformat(timespec="minutes"),
        "keywords": ["agenda cultural", "Rio de Janeiro", "eventos", "cultura", "dados abertos"],
        "licenses": [{"name": "ODbL-1.0", "path": "https://opendatacommons.org/licenses/odbl/1-0/", "title": "Dados"},
                     {"name": "CC-BY-SA-4.0", "path": "https://creativecommons.org/licenses/by-sa/4.0/deed.pt-br", "title": "Textos"}],
        "contributors": [{"title": "Todos os Rios · Palavra Comunicação", "email": "abreterio@gmail.com", "role": "publisher"}],
        "resources": [
            recurso("sessoes", "sessoes.csv", "Uma linha por dia e hora de cada evento", CAMPOS_SESSOES),
            recurso("eventos", "eventos.csv", "Uma linha por atividade", CAMPOS_EVENTOS),
            recurso("eventos-json", "eventos.json", "Base completa, uma ficha por atividade", None, "json"),
        ],
    }, open(os.path.join(pasta, "datapackage.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    n_ev = len(eventos)
    open(os.path.join(pasta, "index.html"), "w", encoding="utf-8").write(
        pagina(ed, agora, n_ev, n_sessoes, os.path.getsize(os.path.join(pasta, "sessoes.csv"))))
    return n_ev, n_sessoes


def _tabela(campos):
    return "".join(f"<tr><th scope=row><code>{c}</code></th><td>{html.escape(d)}</td></tr>" for c, _, d in campos)


def pagina(ed, agora, n_ev, n_sessoes, tam_sessoes):
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
             "outubro", "novembro", "dezembro"]
    quando = f"{agora.day} de {meses[agora.month - 1]} de {agora.year}, às {agora:%H:%M}"
    fim = dt.date.fromisoformat(ed["fim"])
    ate = f"{fim.day} de {meses[fim.month - 1]} de {fim.year}"
    mb = f"{tam_sessoes / 1_000_000:.1f}".replace(".", ",")
    u = SITE + "dados/"
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dados abertos · Todos os Rios</title>
<meta name="description" content="Toda a programação cultural do Rio de Janeiro do Todos os Rios em dados abertos: CSV, JSON e calendários, atualizados todos os dias, sem cadastro.">
<link rel="icon" href="../icones/icone.svg" type="image/svg+xml">
<link rel="alternate" type="text/csv" href="{u}sessoes.csv" title="Sessões (CSV)">
<link rel="alternate" type="application/json" href="{u}eventos.json" title="Eventos (JSON)">
<link rel="describedby" type="application/json" href="{u}datapackage.json">
<style>
:root{{--papel:#f8f4ec;--papel2:#eee7d9;--tinta:#2a2623;--tinta2:#5f574e;--linha:#dbd2c1;--acento:#1b4e8f}}
@media (prefers-color-scheme:dark){{:root{{--papel:#143b70;--papel2:#0f2e59;--tinta:#fbf7ee;--tinta2:#c9d6ea;--linha:#3a629e;--acento:#ffb469}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--papel);color:var(--tinta);font:17px/1.55 "Source Serif 4",Georgia,serif}}
main{{max-width:760px;margin:0 auto;padding:28px 18px 60px}}
h1,h2,h3,th,.marca,nav,.botao,table{{font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}}
.marca{{font-weight:800;color:var(--tinta);text-decoration:none;font-size:15px;letter-spacing:.04em}}
h1{{font-size:30px;line-height:1.15;margin:18px 0 8px}}
h2{{font-size:20px;margin:36px 0 10px;padding-top:14px;border-top:1px solid var(--linha)}}
a{{color:var(--acento)}}
.sub{{color:var(--tinta2);margin:0 0 20px}}
.arquivos{{display:grid;gap:12px;margin:18px 0}}
.arq{{background:var(--papel2);border:1px solid var(--linha);border-radius:10px;padding:14px 16px}}
.arq h3{{margin:0 0 4px;font-size:17px}}
.arq p{{margin:4px 0}}
.url{{font:14px/1.4 ui-monospace,Menlo,Consolas,monospace;word-break:break-all;background:var(--papel);border:1px solid var(--linha);border-radius:6px;padding:6px 8px;display:block;margin:8px 0}}
.botao{{display:inline-block;font-size:14px;font-weight:600;padding:6px 12px;border-radius:999px;border:1px solid var(--acento);text-decoration:none;margin:4px 6px 0 0}}
code{{font:14px ui-monospace,Menlo,Consolas,monospace}}
pre{{background:var(--papel2);border:1px solid var(--linha);border-radius:8px;padding:10px 12px;overflow-x:auto;font-size:14px;white-space:pre-wrap;word-break:break-all}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{text-align:left;vertical-align:top;padding:6px 8px;border-bottom:1px solid var(--linha)}}
th{{white-space:nowrap;font-weight:600}}
details{{margin:10px 0}}
summary{{cursor:pointer;font-family:system-ui,sans-serif;font-weight:600}}
footer{{margin-top:40px;font-size:14px;color:var(--tinta2)}}
</style>
</head>
<body>
<main>
<a class="marca" href="../">TODOS OS RIOS</a>
<h1>Dados abertos</h1>
<p class="sub">A programação cultural do Rio é um bem comum. Tudo o que está no site está aqui, em arquivos que qualquer pessoa pode baixar, ler num programa ou ligar direto numa planilha, sem cadastro, sem chave e sem pedir licença.</p>
<p>Agora: <strong>{n_ev} atividades</strong> e <strong>{n_sessoes} sessões</strong>, de hoje até {ate}. Atualizado em {quando}. Os arquivos mudam todos os dias, sempre no mesmo endereço.</p>

<div class="arquivos">
 <div class="arq">
  <h3>Sessões · CSV</h3>
  <p>Uma linha por dia e hora de cada evento. O formato mais simples para planilhas, mapas e programas.</p>
  <code class="url">{u}sessoes.csv</code>
  <a class="botao" href="sessoes.csv" download>Baixar ({mb} MB)</a>
 </div>
 <div class="arq">
  <h3>Atividades · CSV</h3>
  <p>Uma linha por atividade, com todos os horários juntos numa coluna. Inclui as exposições em cartaz.</p>
  <code class="url">{u}eventos.csv</code>
  <a class="botao" href="eventos.csv" download>Baixar</a>
 </div>
 <div class="arq">
  <h3>Base completa · JSON</h3>
  <p>Uma ficha por atividade, com sessões, preços em número, links de ingresso e sinopses em português, inglês e espanhol.</p>
  <code class="url">{u}eventos.json</code>
  <a class="botao" href="eventos.json" download>Baixar</a>
 </div>
 <div class="arq">
  <h3>Calendários · iCalendar (.ics)</h3>
  <p>Para assinar no celular ou ler em qualquer programa de agenda.</p>
  <code class="url">{SITE}calendarios/todososrios-geral.ics</code>
  <code class="url">{SITE}calendarios/todososrios-destaques.ics</code>
 </div>
</div>

<h2>Como usar</h2>
<details open><summary>No Google Planilhas (atualiza sozinho)</summary>
<p>Cole numa célula vazia. A planilha busca a versão do dia sempre que é aberta:</p>
<pre>=IMPORTDATA("{u}sessoes.csv"; ";")</pre>
</details>
<details><summary>No Excel</summary>
<p>Baixe o arquivo e abra com dois cliques: as colunas já vêm separadas. Para manter ligado ao site, use <em>Dados › Obter dados › Da Web</em> e cole o endereço do arquivo.</p>
</details>
<details><summary>Em programas e sites</summary>
<p>Os arquivos são estáticos, em UTF-8, e podem ser lidos de qualquer página ou programa, inclusive direto do navegador. Não há limite de acesso. Por exemplo, em Python:</p>
<pre>import pandas as pd
sessoes = pd.read_csv("{u}sessoes.csv", sep=";", encoding="utf-8-sig")</pre>
<p>A descrição técnica de cada arquivo, no padrão Frictionless Data, está em <a href="datapackage.json">datapackage.json</a>.</p>
</details>

<h2>Licença e crédito</h2>
<p>Os dados estão sob a licença <a href="https://opendatacommons.org/licenses/odbl/1-0/">ODbL 1.0</a> e os textos (sinopses) sob <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.pt-br">CC BY-SA 4.0</a>. Você pode copiar, adaptar e republicar, inclusive com fins comerciais, desde que:</p>
<ul>
<li>dê o crédito: <em>“Fonte: Todos os Rios (todososrios.com.br)”</em>, com link;</li>
<li>mantenha aberto, sob a mesma licença, o que fizer a partir destes dados.</li>
</ul>
<p>Cada atividade traz o link da fonte original. Preços e horários podem mudar: confira no link antes de sair de casa.</p>

<h2>Campos</h2>
<details><summary>sessoes.csv</summary><table>{_tabela(CAMPOS_SESSOES)}</table></details>
<details><summary>eventos.csv</summary><table>{_tabela(CAMPOS_EVENTOS)}</table></details>
<details><summary>eventos.json</summary>
<p>Os mesmos campos de <code>eventos.csv</code>, mais: <code>sessoes</code> (lista com <code>data</code>, <code>hora</code> e, quando há, <code>compra</code>), <code>cartaz</code> (período e horário das exposições), <code>preco_min</code> e <code>preco_max</code> (em reais), <code>gratis</code> e <code>na_rua</code> (verdadeiro ou falso), <code>preco_texto</code>, <code>sinopse_en</code>, <code>sinopse_es</code> e <code>entrou_em</code> (dia em que a ficha entrou na agenda).</p>
</details>

<footer>
<p>Usou estes dados num projeto? Achou um erro? Conte para a gente: <a href="mailto:abreterio@gmail.com">abreterio@gmail.com</a>.</p>
<p><a href="../">Voltar à agenda</a> · Todos os Rios · Palavra Comunicação</p>
</footer>
</main>
</body>
</html>
"""
