#!/usr/bin/env python3
"""Reconhecimento das plataformas de ingresso (teste, 19/11/2026; terceira rodada em 22/11/2026: Fever e Shotgun).

Visita poucas páginas públicas de cada plataforma, sem login, identificando-se como TodosOsRiosBot,
com pausa entre visitas. Guarda as respostas brutas numa pasta temporária, que o fluxo do GitHub
envia a um ramo separado (teste-plataformas), fora do site e da linha principal.
Objetivo: descobrir por onde cada plataforma expõe a programação do Rio (dados estruturados,
dados embutidos na página, interfaces usadas pelo próprio site, mapas do site).
Protocolo do Todos os Rios (plano diretor, seção 5): só fatos sobre eventos, nunca dados de pessoas,
sem login, sem romper barreiras técnicas, sem sobrecarga.
"""
import json, os, re, ssl, time, urllib.request, urllib.error

AGENTE = "Mozilla/5.0 (compatible; TodosOsRiosBot/0.3; agenda cultural aberta do Rio de Janeiro; +https://todososrios.com.br/; abreterio@gmail.com)"
SAIDA = os.environ.get("SAIDA", "saida-plataformas")
PAUSA = 3

ALVOS = {  # décima rodada (25/11/2026): dias das sessões nas páginas de evento da Sympla e do Bileto
    "sympla-evento": [
        "https://www.sympla.com.br/evento/nha-eva/3614258",
        "https://www.sympla.com.br/evento/dia-de-jogo/3653851",
    ],
    "bileto": [
        "https://bileto.sympla.com.br/event/128323",
    ],
}


def baixar(url, limite=3_000_000):
    req = urllib.request.Request(url, headers={
        "User-Agent": AGENTE, "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=60, context=ssl.create_default_context()) as r:
            corpo = r.read(limite)
            return r.status, r.geturl(), r.headers.get("Content-Type", ""), corpo.decode(r.headers.get_content_charset() or "utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            corpo = e.read(200_000).decode("utf-8", "replace")
        except Exception:
            corpo = ""
        return e.code, url, e.headers.get("Content-Type", "") if e.headers else "", corpo
    except Exception as e:
        return 0, url, "", type(e).__name__ + ": " + str(e)[:200]


def sinais(texto):
    ld = re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', texto, re.S | re.I)
    tipos = re.findall(r'"@type"\s*:\s*"([A-Za-z]*Event)"', " ".join(ld))
    return {
        "jsonld_blocos": len(ld),
        "jsonld_eventos": len(tipos),
        "next_data": "__NEXT_DATA__" in texto,
        "nuxt": "__NUXT__" in texto,
        "apis_citadas": sorted(set(re.findall(r'https://[a-z0-9.-]*(?:api|bff|search|discovery)[a-z0-9.-]*\.[a-z.]+', texto)))[:30],
        "parece_bloqueio": bool(re.search(r'captcha|cf-chl|access denied|attention required|perimeterx|datadome', texto[:20000], re.I)),
    }


def main():
    os.makedirs(SAIDA, exist_ok=True)
    resumo = []
    for plataforma, urls in ALVOS.items():
        for i, url in enumerate(urls):
            st, final, tipo, corpo = baixar(url)
            nome = f"{plataforma}-{i:02d}.txt"
            with open(os.path.join(SAIDA, nome), "w", encoding="utf-8") as f:
                f.write(f"URL: {url}\nFINAL: {final}\nSTATUS: {st}\nTIPO: {tipo}\n\n{corpo}")
            item = {"plataforma": plataforma, "url": url, "status": st, "tipo": tipo, "tamanho": len(corpo), "arquivo": nome}
            item.update(sinais(corpo))
            resumo.append(item)
            print(plataforma, st, len(corpo), url, flush=True)
            time.sleep(PAUSA)
    # Bileto é página montada por script: lê os scripts do próprio site para achar o endereço de onde ela puxa as sessões
    st, final, tipo, corpo = baixar("https://bileto.sympla.com.br/event/128323")
    achados = []
    for src in re.findall(r'<script[^>]+src="([^"]+)"', corpo)[:12]:
        url = src if src.startswith("http") else "https://bileto.sympla.com.br" + ("" if src.startswith("/") else "/") + src
        s2, _, _, js = baixar(url, 8_000_000)
        time.sleep(1)
        trechos = set()
        for m in re.finditer(r'(api|session|sess|apresenta|/v[0-9]/)', js):
            trechos.add(js[max(0, m.start() - 120): m.end() + 160])
            if len(trechos) > 400:
                break
        achados.append({"script": url, "status": s2, "tamanho": len(js),
                        "urls": sorted(set(re.findall(r'https?://[a-zA-Z0-9.-]+(?:/[a-zA-Z0-9_./{}:-]*)?', js)))[:200],
                        "trechos": sorted(trechos)[:400]})
    with open(os.path.join(SAIDA, "bileto-scripts.json"), "w", encoding="utf-8") as f:
        json.dump(achados, f, ensure_ascii=False, indent=1)
    with open(os.path.join(SAIDA, "resumo.json"), "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
