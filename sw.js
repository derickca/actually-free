// Actually Free service worker — build 202611171233
const CACHE = "actually-free-202611171233";
const PRECACHE = [
  "/", "/suggest", "/what-is-free", "/manifest.webmanifest",
  "/assets/styles.css", "/assets/app.js", "/assets/config.js",
  "/assets/icon-192.png", "/assets/icon-512.png"
];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});
self.addEventListener("fetch", (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== self.location.origin) return;
  // The Ops surface and the MemberSpark sign-in road are fenced
  // from this cache by construction (issue #32): the worker
  // never answers for them and never stores their answers, so
  // no signed-in face can be served to another request.
  if (u.pathname === "/ops" || u.pathname.startsWith("/ops/") ||
      u.pathname === "/ops-signout" || u.pathname.startsWith("/auth/memberspark/")) return;
  e.respondWith(
    caches.match(e.request).then((hit) => {
      if (hit) return hit;
      return fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      }).catch(() => caches.match("/"));
    })
  );
});
