#!/usr/bin/env python3
"""Estudo I (24/11/2026): ajustes de uso, sem mudar a identidade visual.

Gera uma prévia separada em docs/estudo-i/index.html a partir do site publicado
(docs/index.html). Não altera o site principal. Só em português.

O que muda em relação ao site:
  3. etiqueta "Preço não informado" sai; a ficha aberta diz "Preço: consulte a fonte oficial";
  4. filtros numa faixa só, no topo: Grátis, Até R$ 40, Na rua, as áreas e "Região";
  5. "As boas do mês", "Em cartaz" e "Escolher data" numa linha própria; a faixa só com dias,
     com setas no computador;
  6. computador: duas colunas; à direita, fixo, um painel de navegação com o calendário dos dois meses,
     "As boas do mês", "Em cartaz" e todos os filtros à vista; "A cidade inteira" sai da página;
     sem a etiqueta "a confirmar" nas fichas;
  7. grade dos cinemas recolhida numa linha, com os cinemas agrupados por região;
  8. linha de apresentação sob a marca;
  9b. lista sem fios entre os eventos (botão na faixa da prévia alterna com e sem).

Uso: python3 ferramentas/estudo_i.py
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def troca(html, velho, novo, n=1):
    achados = html.count(velho)
    if achados != n:
        raise SystemExit(f"Esperava {n} ocorrência(s), achei {achados}: {velho[:90]!r}")
    return html.replace(velho, novo)


CSS = """
/* ---------- Estudo I (24/11/2026): ajustes de uso; ver documentos/guia-de-design.md ---------- */
.previa{font:500 13px/1.4 var(--sans);background:var(--papel2);color:var(--tinta2);padding:8px 12px;border-radius:10px;margin:10px 0 0;display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.previa button{font:600 13px var(--sans);border:1px solid var(--tinta2);background:transparent;color:var(--tinta);border-radius:999px;padding:6px 12px;cursor:pointer}
.lema-topo{font:400 15px/1.45 var(--sans);color:var(--tinta2);margin:8px 0 0;max-width:42em}
/* 4. filtros numa faixa só */
.faixa-filtros{align-items:center}
.faixa-filtros .sep{flex:0 0 1px;align-self:stretch;background:var(--linha);margin:4px 3px}
.chip.reg[aria-expanded=true]{border-color:var(--tinta)}
#fRegioes{margin:-2px 0 10px}
#fRegioes[hidden]{display:none}
/* 5. modos e faixa de dias */
.modos-caixa{position:relative}
.modos{display:flex;gap:8px;flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;margin:2px -18px 2px 0;padding:2px 18px 2px 0}
.modos::-webkit-scrollbar{display:none}
.modo{border:1px solid var(--linha);background:transparent;color:var(--tinta);border-radius:999px;padding:6px 13px;
  font:600 14px var(--serif);cursor:pointer;display:inline-flex;align-items:center;gap:6px;flex:0 0 auto;white-space:nowrap}
.modo.mes::before{content:"";width:.45em;height:.45em;border-radius:50%;background:var(--sol)}
.modo[aria-pressed=true]{background:var(--sel);border-color:var(--sel);color:var(--sel-texto)}
.modo[aria-pressed=true].mes::before{background:var(--sel-texto)}
#qdata{position:absolute;left:0;bottom:0;width:1px;height:1px;opacity:0;pointer-events:none;border:0;padding:0}
.trilho-caixa{position:sticky;top:0;z-index:5;background:var(--papel);display:flex;align-items:center;gap:4px}
.trilho-caixa .trilho{position:static;flex:1;min-width:0}
.seta{display:none;flex:0 0 36px;height:44px;border:1px solid var(--linha);border-radius:12px;background:var(--papel);color:var(--tinta);
  font:600 22px/1 var(--serif);cursor:pointer;align-items:center;justify-content:center}
.seta:hover{border-color:var(--tinta)}
@media (hover:hover) and (pointer:fine) and (min-width:720px){ .seta{display:flex} }
/* 7. grade dos cinemas recolhida */
details.grade-toda{border-top:1px solid var(--linha);margin-top:28px;padding-top:4px}
details.grade-toda>summary{list-style:none;cursor:pointer;padding:12px 0}
details.grade-toda>summary::-webkit-details-marker{display:none}
details.grade-toda>summary h3{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
details.grade-toda>summary h3::after{content:"Ver ▾";font:600 14px var(--sans);color:var(--acento)}
details.grade-toda[open]>summary h3::after{content:"Fechar ▴"}
details.grade-toda>summary p{margin:0;font-size:14px;color:var(--tinta2)}
.grade-reg{font:600 12px var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--tinta2);margin:18px 0 2px}
.lado{display:none}
.nav-cal{border:1px solid var(--linha);border-radius:var(--raio);padding:12px 12px 8px}
.nav-cal .cab{display:flex;align-items:center;justify-content:space-between;margin:0 0 6px}
.nav-cal .cab b{font:600 18px var(--serif)}
.nav-cal .cab button{border:1px solid var(--linha);background:transparent;color:var(--tinta);border-radius:10px;width:36px;height:36px;font:600 18px var(--serif);cursor:pointer}
.nav-cal .cab button:disabled{opacity:.3;cursor:default}
.grade-mes{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:2px;text-align:center}
.grade-mes .sem{font:600 11px var(--sans);color:var(--tinta2);padding:4px 0;letter-spacing:.04em}
.grade-mes button,.grade-mes span.fora{height:35px;border:0;border-radius:10px;background:transparent;color:var(--tinta);font:600 15px var(--serif);position:relative}
.grade-mes button{cursor:pointer}
.grade-mes button:hover{background:var(--papel2)}
.grade-mes span.fora{color:var(--tinta2);opacity:.35;line-height:35px}
.grade-mes button.hoje{text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:2px}
.grade-mes button.boa::after{content:"";position:absolute;left:50%;bottom:4px;width:5px;height:5px;margin-left:-2.5px;border-radius:50%;background:var(--sol)}
.grade-mes button[aria-pressed=true]{background:var(--sel);color:var(--sel-texto)}
.grade-mes button[aria-pressed=true].boa::after{background:var(--sel-texto)}
.nav-cal .leg{font-size:12px;color:var(--tinta2);margin:6px 2px 0;display:flex;align-items:center;gap:6px}
.nav-cal .leg i{width:6px;height:6px;border-radius:50%;background:var(--sol);display:inline-block}
.nav-modos{display:flex;gap:8px;margin:12px 0 0}
.nav-modos .modo{flex:1;justify-content:center}
.nav-grupo{margin:16px 0 0}
.nav-grupo .rotulo{margin:0 0 6px}
.nav-grupo .chips{margin:0}
.nav-limpa{margin:14px 0 0;border:0;background:transparent;color:var(--acento);font:600 14px var(--sans);cursor:pointer;padding:6px 0;text-decoration:underline;text-underline-offset:3px}
/* 9b. sem fios entre os eventos */
body.sem-linhas .ev{border-bottom:none;padding:10px 0 16px}
body.sem-linhas .hora{border-bottom:none;padding-bottom:0;margin-top:24px}
/* 6. computador: duas colunas */
@media (min-width:1080px){
  .wrap{max-width:1180px}
  .colunas{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:56px;align-items:start}
  .lado{display:block;position:sticky;top:12px;max-height:calc(100vh - 24px);overflow-y:auto;padding:2px 2px 12px;scrollbar-width:thin}
  /* no computador, a navegação mora na coluna lateral: some da coluna principal */
  .principal #filtrosTopo,.principal #fRegioes,.principal .modos-caixa,.principal .trilho-caixa{display:none!important}
  #sobre,footer,#calendario{max-width:760px}
}
"""

NOVO_MEIO = """<div class="colunas">
<main class="principal">
<div class="busca">
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
  <input id="q" type="search" autocomplete="off" data-tp="busca" placeholder="Buscar: artista, lugar, bairro…" aria-label="Buscar">
</div>
<div class="chips secoes faixa-filtros" id="filtrosTopo">
  <div id="fGratis" style="display:contents"></div><span class="sep" aria-hidden="true"></span>
  <div id="fAreas" style="display:contents"></div><span class="sep" aria-hidden="true"></span>
  <button class="chip reg" id="regBtn" type="button" aria-expanded="false" aria-controls="fRegioes"><span data-t="regiao">Região</span> <span id="nfiltros"></span> ▾</button>
</div>
<div class="chips" id="fRegioes" hidden></div>

<div class="modos-caixa"><div class="modos" id="modos"></div>
<input type="date" id="qdata" tabindex="-1" aria-hidden="true"></div>
<div class="trilho-caixa">
  <button class="seta" id="setaEsq" type="button" aria-label="Dias anteriores">‹</button>
  <nav class="trilho" id="dias" aria-label="Dias"></nav>
  <button class="seta" id="setaDir" type="button" aria-label="Próximos dias">›</button>
</div>

<section id="boa">
  <h2 class="qb">A boa de hoje</h2>
  <p class="nota-boa"><a href="#criterios" data-t="como">Como escolhemos</a></p>
  <ul class="lista" id="destaques"></ul>
</section>

<h2 class="secao" id="tituloToda" data-t="toda">Toda a programação</h2>

<div class="contagem">
  <span id="contagem"></span>
  <button class="btn" id="baixar" data-t="baixar">＋ Levar para minha agenda</button>
</div>

<div id="resultados"><ul class="lista" id="lista"></ul>
<div id="grade"></div>
<div id="radar"></div></div>
</main>
<aside class="lado" aria-label="Navegação">
"""

JS_EXTRA = """
<script>
// Estudo I: setas da faixa de dias, região, escolher data, grade recolhida, com e sem linhas
(function(){
  var tr=document.querySelector("#dias");
  document.querySelector("#setaEsq").onclick=function(){tr.scrollBy({left:-tr.clientWidth*.8,behavior:"smooth"})};
  document.querySelector("#setaDir").onclick=function(){tr.scrollBy({left:tr.clientWidth*.8,behavior:"smooth"})};
  var rb=document.querySelector("#regBtn"), fr=document.querySelector("#fRegioes");
  rb.onclick=function(){fr.hidden=!fr.hidden; rb.setAttribute("aria-expanded",!fr.hidden)};
  var qd=document.querySelector("#qdata"); qd.min=DIAS[0]; qd.max=DIAS[DIAS.length-1];
  document.addEventListener("click",function(ev){ if(ev.target.closest("#escData")){ qd.value=(DIAS.includes(S.dia)?S.dia:DIAS[0]);
    try{qd.showPicker()}catch(e){qd.style.pointerEvents="auto";qd.focus();} }});
  qd.addEventListener("change",function(){ if(DIAS.includes(qd.value)){S.dia=qd.value;S.aberto=null;render.rolou=false;render();} });
  document.addEventListener("toggle",function(ev){ if(ev.target.classList&&ev.target.classList.contains("grade-toda")) S.gradeAberta=ev.target.open; },true);
  // painel de navegação do computador: calendário dos dois meses + modos + filtros (reaproveita os mesmos botões do site)
  var MESES=[...new Set(DIAS.map(function(d){return d.slice(0,7)}))], M=0, ultimoDia=null;
  var BOAS=new Set(); (D.destaques_mes||[]).forEach(function(d){var e=E.find(function(x){return x.id===d.id}); if(e&&e.sessoes) e.sessoes.forEach(function(s){BOAS.add(s.data)})});
  var SEM=t("sem");
  function mesNome(ym){var x=new Date(ym+"-15T12:00:00Z").toLocaleDateString(S.lang==="pt"?"pt-BR":S.lang,{month:"long",year:"numeric",timeZone:"UTC"}); return x.charAt(0).toUpperCase()+x.slice(1)}
  function lado(){
    var box=document.querySelector("#ladoNav"); if(!box) return;
    if(S.dia!==ultimoDia){ ultimoDia=S.dia; if(DIAS.includes(S.dia)) M=Math.max(0,MESES.indexOf(S.dia.slice(0,7))); }
    var ym=MESES[M], ini=new Date(ym+"-01T12:00:00Z"), nd=new Date(Date.UTC(ini.getUTCFullYear(),ini.getUTCMonth()+1,0)).getUTCDate();
    var cel=SEM.map(function(x){return '<span class="sem">'+x+'</span>'}).join("");
    for(var i=0;i<ini.getUTCDay();i++) cel+='<span></span>';
    for(var d=1;d<=nd;d++){ var iso=ym+"-"+String(d).padStart(2,"0");
      if(DIAS.includes(iso)) cel+='<button data-dia="'+iso+'" aria-pressed="'+(S.dia===iso)+'" class="'+(iso===hojeISO?"hoje ":"")+(BOAS.has(iso)?"boa":"")+'" aria-label="'+iso.split("-").reverse().join("/")+(BOAS.has(iso)?" · "+t("boaMes"):"")+'">'+d+'</button>';
      else cel+='<span class="fora">'+d+'</span>'; }
    var ch=function(attr,val,on,txt,cls){return '<button class="chip'+(cls||"")+'" '+attr+'="'+val+'" aria-pressed="'+on+'">'+txt+'</button>'};
    var areas=AREAS.filter(function(a){return E.some(function(e){return e.areas.includes(a)})});
    var algum=S.areas.length||S.regioes.length||S.gratis||S.popular||S.rua;
    box.innerHTML='<div class="nav-cal"><div class="cab"><button type="button" id="mAnt" aria-label="'+t("mesAnt")+'"'+(M===0?" disabled":"")+'>‹</button><b>'+mesNome(ym)+'</b><button type="button" id="mProx" aria-label="'+t("mesProx")+'"'+(M===MESES.length-1?" disabled":"")+'>›</button></div>'
      +'<div class="grade-mes">'+cel+'</div>'+(BOAS.size?'<p class="leg"><i></i> '+t("legBoas")+'</p>':'')+'</div>'
      +'<div class="nav-modos">'+((D.destaques_mes||[]).length?'<button class="modo mes" data-dia="mes" aria-pressed="'+(S.dia==="mes")+'">'+t("boaMes")+'</button>':'')+'<button class="modo" data-dia="cartaz" aria-pressed="'+(S.dia==="cartaz")+'">'+t("cartaz")+'</button></div>'
      +'<div class="nav-grupo"><p class="rotulo">'+t("navPreco")+'</p><div class="chips">'+ch("data-f","gratis",S.gratis,t("gratis")," g")+ch("data-f","popular",S.popular,t("popular")," g")+ch("data-f","rua",S.rua,t("rua")," g")+'</div></div>'
      +'<div class="nav-grupo"><p class="rotulo">'+t("navSecoes")+'</p><div class="chips">'+areas.map(function(a){return ch("data-area",a,S.areas.includes(a),esc(tA(a)))}).join("")+'</div></div>'
      +'<div class="nav-grupo"><p class="rotulo">'+t("regiao")+'</p><div class="chips">'+REGIOES.map(function(r){return ch("data-reg",r,S.regioes.includes(r),esc(tR(r)))}).join("")+'</div></div>'
      +(algum?'<button type="button" class="nav-limpa" id="limpa">'+t("limpa")+'</button>':'');
  }
  var _render=render; render=function(){_render(); lado();}; render.rolou=_render.rolou; render.ultimoDia=_render.ultimoDia; render.atual=_render.atual;
  document.addEventListener("click",function(ev){
    if(ev.target.closest("#mAnt")){M=Math.max(0,M-1);lado();}
    else if(ev.target.closest("#mProx")){M=Math.min(MESES.length-1,M+1);lado();}
    else if(ev.target.closest("#limpa")){Object.assign(S,{areas:[],regioes:[],gratis:false,popular:false,rua:false});
      ["areas","regioes"].forEach(function(k){guarda.set(k,[])}); ["gratis","popular","rua"].forEach(function(k){guarda.set(k,false)}); render();}
    else if(ev.target.closest(".lado [data-dia]")){var pr=document.querySelector(".principal"); if(pr.getBoundingClientRect().top<0) pr.scrollIntoView({behavior:"smooth"});}
  });
  lado();
  var lb=document.querySelector("#linhas");
  function pl(){var s=document.body.classList.contains("sem-linhas"); lb.textContent=s?"Ver com linhas":"Ver sem linhas";}
  lb.onclick=function(){document.body.classList.toggle("sem-linhas"); pl();}; pl();
})();
</script>
"""


TEXTOS = """Object.assign(T.pt,{lemaTopo:"A cidade inteira, de hoje a dois meses à frente. Aberta, gratuita, sem cadastro.",escData:"Escolher data",precoFonte:"Preço: consulte a fonte oficial.",navPreco:"Preço e lugar",navSecoes:"Seções",limpa:"Limpar filtros",legBoas:"dias com uma das boas do mês",mesAnt:"Mês anterior",mesProx:"Próximo mês",sem:["D","S","T","Q","Q","S","S"]});
Object.assign(T.en,{lemaTopo:"The whole city, from today to two months ahead. Open, free, no sign-up.",escData:"Pick a date",precoFonte:"Price: check the official source.",navPreco:"Price & place",navSecoes:"Sections",limpa:"Clear filters",legBoas:"days with a book-ahead pick",mesAnt:"Previous month",mesProx:"Next month",sem:["S","M","T","W","T","F","S"]});
Object.assign(T.es,{lemaTopo:"Toda la ciudad, de hoy a dos meses. Abierta, gratuita, sin registro.",escData:"Elegir fecha",precoFonte:"Precio: consulta la fuente oficial.",navPreco:"Precio y lugar",navSecoes:"Secciones",limpa:"Borrar filtros",legBoas:"días con algo de «Lo bueno del mes»",mesAnt:"Mes anterior",mesProx:"Mes siguiente",sem:["D","L","M","X","J","V","S"]});"""


def aplicar(html, previa):
    if previa:
        html = previa_de(html)
    else:
        html = troca(html, "</head>", "<style>%s</style>\n</head>" % CSS)
        html = troca(html, "<body>\n", '<body class="sem-linhas">\n')
    return ajustes(html, previa)


def previa_de(html):
    # prévia: fora dos buscadores, caminhos a partir da subpasta, sem instalar como aplicativo
    html = troca(html, "</head>", '<meta name="robots" content="noindex">\n<style>%s</style>\n</head>' % CSS)
    html = troca(html, "<title>", "<title>Prévia · Estudo I · ")
    for velho in ['href="manifest.webmanifest"', 'href="icones/', 'href="dados/eventos.csv"', 'href="dados/eventos.json"']:
        html = html.replace(velho, velho.replace('href="', 'href="../'))
    html = troca(html, 'new URL("calendarios/', 'new URL("../calendarios/')
    html = troca(html, '{pt:"",en:"en/",es:"es/"}', '{pt:"../",en:"../en/",es:"../es/"}')
    html = troca(html, "<script>if('serviceWorker' in navigator)", "<script>if(false)")
    return troca(html, '<body>\n<div class="wrap">', '<body class="sem-linhas">\n<div class="wrap">\n<div class="previa"><span>Prévia · Estudo I. Não é o site publicado.</span><button id="linhas" type="button">Ver com linhas</button></div>')


def ajustes(html, previa):
    # 8. linha de apresentação sob a marca
    html = troca(html, '<p class="sub" data-t="sub">Agenda cultural do Rio de Janeiro</p>',
                 '<p class="sub" data-t="sub">Agenda cultural do Rio de Janeiro</p>\n  <p class="lema-topo" data-t="lemaTopo"></p>')

    # 4, 5, 6: nova ordem da parte de cima e colunas
    ini = html.index('<div class="busca">')
    fim = html.index('<div id="radar"></div></div>') + len('<div id="radar"></div></div>')
    html = html[:ini] + NOVO_MEIO + html[fim:].lstrip("\n")
    # 6. coluna lateral do computador = painel de navegação (calendário dos dois meses + filtros).
    #    "A cidade inteira" sai da página (a métrica continua nos relatórios internos).
    a = html.index('<section class="bloco" id="calendario">')
    b = html.index('</section>', a) + len('</section>')
    cal = html[a:b]
    html = html[:a] + html[b:].lstrip("\n")
    a = html.index('<section class="bloco">\n  <h2 data-t="terrTit">')
    b = html.index('</section>', a) + len('</section>')
    html = html[:a] + html[b:].lstrip("\n")
    html = troca(html, '<section class="bloco" id="sobre">',
                 '<div id="ladoNav"></div>\n</aside>\n</div>\n\n' + cal + '\n\n<section class="bloco" id="sobre">')
    html = troca(html, 'document.querySelector("#barras").innerHTML =', 'if(document.querySelector("#barras")) document.querySelector("#barras").innerHTML =')

    # fichas sem a etiqueta "a confirmar" (o aviso de temporada sem dias já cumpre esse papel)
    html = troca(html, '${e.status==="a_confirmar"?`<span class="tag conf">${t("aconf")}</span>`:""}', '')

    # textos novos, nas três línguas
    html = troca(html, "const AREA_T = {", TEXTOS + "\nconst AREA_T = {")

    # 3. sem etiqueta de preço quando a fonte não informa; a ficha aberta avisa
    html = troca(html, 'return `<span class="tag">${esc(e.preco_texto||t("naoinf"))}</span>`;',
                 'return e.preco_texto?`<span class="tag">${esc(e.preco_texto)}</span>`:"";')
    html = troca(html, '${e.classificacao||e.acessibilidade?`<p class="extra">',
                 '${!e.gratis&&!e.preco_texto?`<p class="extra">${t("precoFonte")}</p>`:""}${e.classificacao||e.acessibilidade?`<p class="extra">')

    # 5. modos fora da faixa; a faixa fica só com os dias
    a = html.index('document.querySelector("#dias").innerHTML =')
    b = html.index("+ DIAS.map(", a) + len("+ DIAS.map(")
    html = html[:a] + ('document.querySelector("#modos").innerHTML ='
        ' ((D.destaques_mes||[]).length?`<button class="modo mes" data-dia="mes" aria-pressed="${S.dia==="mes"}">${t("boaMes")}</button>`:"")'
        ' + `<button class="modo" data-dia="cartaz" aria-pressed="${S.dia==="cartaz"}">${t("cartaz")}</button>`'
        ' + `<button class="modo" id="escData" type="button">${t("escData")}</button>`;\n'
        '  document.querySelector("#dias").innerHTML = DIAS.map(') + html[b:]

    # 4. contador do botão Região e logo
    html = troca(html, "const nf=S.areas.length+S.regioes.length;", "const nf=S.regioes.length; if(nf) document.querySelector(\"#fRegioes\").hidden=false;")
    html = troca(html, 'document.querySelector("#filtros").open=false;', 'document.querySelector("#fRegioes").hidden=true;')

    # 7. grade dos cinemas recolhida, por região
    html = troca(html, "const cines=Object.values(porCine).sort((a,b)=>a.e.local.localeCompare(b.e.local));",
                 "const cines=Object.values(porCine).sort((a,b)=>(REGIOES.indexOf(a.e.regiao)-REGIOES.indexOf(b.e.regiao))||a.e.local.localeCompare(b.e.local));")
    html = troca(html, 'g=`<section class="grade"><h3>${t("gradeTit")}</h3><p>${t("gradeTxt")(cines.length,nf)}</p>`+cines.map(c=>',
                 'g=`<details class="grade grade-toda"${S.gradeAberta||S.areas.includes("Cinema")?" open":""}><summary><h3>${t("gradeTit")}</h3><p>${t("gradeTxt")(cines.length,nf).replace(/\\.\\s.*$/,".")}</p></summary>`+cines.map((c,i)=>(i===0||cines[i-1].e.regiao!==c.e.regiao?`<p class="grade-reg">${esc(tR(c.e.regiao))}</p>`:"")+')
    html = troca(html, '`</ul></details>`).join("")+`</section>`; }\n  }\n  document.querySelector("#grade")',
                 '`</ul></details>`).join("")+`</details>`; }\n  }\n  document.querySelector("#grade")')

    # região selecionada aparece só na própria linha de regiões, sem chip repetido
    html = troca(html, '+S.regioes.map(r=>`<button class="chip" data-reg="${r}" aria-pressed="true">${esc(tR(r))} ✕</button>`).join("");', ';')

    js = JS_EXTRA if previa else JS_EXTRA[:JS_EXTRA.index('  var lb=document.querySelector("#linhas");')] + "})();\n</script>\n"
    return troca(html, "</body>", js + "</body>")


def main():
    if "--site" in sys.argv:
        caminho = os.path.join(RAIZ, "ferramentas", "modelo.html")
        html = open(caminho, encoding="utf-8").read()
        if "Estudo I (24/11/2026)" in html:
            raise SystemExit("O modelo já tem os ajustes do Estudo I.")
        open(caminho, "w", encoding="utf-8").write(aplicar(html, previa=False))
        print("ok:", caminho)
        return
    html = aplicar(open(os.path.join(RAIZ, "docs", "index.html"), encoding="utf-8").read(), previa=True)
    pasta = os.path.join(RAIZ, "docs", "estudo-i")
    os.makedirs(pasta, exist_ok=True)
    open(os.path.join(pasta, "index.html"), "w", encoding="utf-8").write(html)
    print("ok:", os.path.join(pasta, "index.html"))


if __name__ == "__main__":
    main()
