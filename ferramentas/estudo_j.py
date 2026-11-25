#!/usr/bin/env python3
"""Estudos J (25/11/2026): tipografia sem serifa.

Parte do site publicado (docs/index.html) e troca só as letras:
- Gabarito (aberta, Naipe Foundry) em títulos, horas, dias, etiquetas e rótulos;
- texto miúdo (lugar, sinopse, "por que ir") em Inter (J1) ou Source Sans 3 (J2).
A marca "Rios." continua em Source Serif 4. Paleta e layout não mudam.

Gera prévias separadas em docs/estudo-j1/ e docs/estudo-j2/. Não altera o site.
As fontes (licença SIL OFL) vêm dos pacotes abertos do Fontsource, recorte latino.

Uso: python3 ferramentas/estudo_j.py <pasta com os pacotes @fontsource-variable>
"""
import base64, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FV = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fv"

def face(nome, arq, estilo="normal"):
    dados = base64.b64encode(open(os.path.join(FV, arq), "rb").read()).decode()
    return (f"@font-face{{font-family:'{nome}';font-weight:100 900;font-style:{estilo};font-display:swap;"
            f"src:url(data:font/woff2;base64,{dados}) format('woff2')}}")

TEXTO = {
    "j1": ("Inter", "inter/files/inter-latin-wght-normal.woff2", "inter/files/inter-latin-wght-italic.woff2", 0),
    "j2": ("Source Sans 3", "source-sans-3/files/source-sans-3-latin-wght-normal.woff2",
           "source-sans-3/files/source-sans-3-latin-wght-italic.woff2", 1),
    # J3: J1 com o "por que ir" e a epígrafe no itálico serifado de hoje (Source Serif 4): a voz da redação
    "j3": ("Inter", "inter/files/inter-latin-wght-normal.woff2", "inter/files/inter-latin-wght-italic.woff2", 0),
}
VOZ_SERIFADA = {"j3"}

def css(nome, n, i, mais):
    return "\n".join([
        face("Gabarito J", "gabarito/files/gabarito-latin-wght-normal.woff2"),
        face("Texto J", n), face("Texto J", i, "italic"),
        f"""
/* Estudo J: Gabarito para mostrar, {nome} para ler */
:root{{--serif:"Gabarito J",system-ui,sans-serif;--sans:"Texto J",system-ui,sans-serif}}
body{{font-family:var(--sans)}}
.marca h1{{font-family:"Source Serif 4",Georgia,serif}}
.ev h3,h2.secao,section.bloco h2,.grade h3,.lema{{font-family:var(--serif);font-weight:700;letter-spacing:-0.01em}}
.qb{{font-family:var(--serif);font-weight:800;font-style:normal;letter-spacing:-0.015em}}
.dia b{{font-family:var(--serif);font-weight:700}}
.hora,.quando,.tag,.rotulo,.chip,.btn,.idiomas button,.radar h4,details.filtros>summary{{font-family:var(--serif)}}
.hora{{font-weight:700}}
.porque,.epigrafe p{{font-family:var(--sans);font-style:italic}}
.ev .onde{{font-size:{14+mais}px}}
.mais p,.grade li{{font-size:{15+mais}px}}
.porque{{font-size:{15+mais}px}}
"""])

def main():
    base = open(os.path.join(RAIZ, "docs", "index.html"), encoding="utf-8").read()
    for chave, (nome, n, i, mais) in TEXTO.items():
        pos = base.find("</head>")
        pos = base.rfind("</style>", 0, pos)
        extra = css(nome, n, i, mais)
        if chave in VOZ_SERIFADA:
            extra += '\n.porque,.epigrafe p{font-family:"Source Serif 4",Georgia,serif;font-style:italic;font-size:16px}\n'
        html = base[:pos] + extra + base[pos:]
        html = html.replace("<title>", f"<title>Estudo {chave.upper()} · ", 1)
        html = html.replace('<meta name="robots"', '<meta name="robots"', 1)
        pasta = os.path.join(RAIZ, "docs", f"estudo-{chave}")
        os.makedirs(pasta, exist_ok=True)
        open(os.path.join(pasta, "index.html"), "w", encoding="utf-8").write(html)
        print(chave, nome, len(html) // 1024, "KB")

if __name__ == "__main__":
    main()
