// Todos os Rios — funcionamento como aplicativo (sem rastreadores, nada de terceiros).
// Páginas: busca sempre a versão mais nova na rede; sem sinal, mostra a última edição guardada no aparelho.
// Ícones e manifesto: guardados no aparelho. Calendários (.ics) e dados abertos passam direto, sem guardar.
const VERSAO = "todososrios-v1";
const BASICO = ["./", "en/", "es/", "manifest.webmanifest", "icones/icone-192.png", "icones/icone-512.png", "icones/icone-180.png", "icones/icone-32.png"];

self.addEventListener("install", (ev) => {
  ev.waitUntil(caches.open(VERSAO).then((c) => c.addAll(BASICO)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (ev) => {
  ev.waitUntil(
    caches.keys()
      .then((nomes) => Promise.all(nomes.filter((n) => n !== VERSAO).map((n) => caches.delete(n))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (ev) => {
  const req = ev.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // páginas do guia: rede primeiro, cópia guardada se estiver sem internet
  if (req.mode === "navigate") {
    ev.respondWith(
      fetch(req)
        .then((resp) => {
          if (resp.ok) {
            const copia = resp.clone();
            caches.open(VERSAO).then((c) => c.put(req, copia));
          }
          return resp;
        })
        .catch(() => caches.match(req, { ignoreSearch: true })
          .then((r) => r || caches.match("./")))
    );
    return;
  }

  // ícones e manifesto: do aparelho, se já estiverem guardados
  if (/\/icones\/|manifest\.webmanifest$/.test(url.pathname)) {
    ev.respondWith(caches.match(req).then((r) => r || fetch(req)));
  }
  // o resto (calendários, dados abertos, estudos) segue direto para a rede
});
