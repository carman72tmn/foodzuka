const CACHE_NAME = 'foodtech-app-shell-v2';
const STATIC_ASSETS = [
  '/loader.css',
  '/favicon.ico',
  '/manifest.json',
  '/pwa-192.png',
  '/pwa-512.png',
  '/admin',
  '/pers'
];

// Фоновое предкэширование всех чанков Vite бандла из manifest.json
async function precacheViteBundle(cache) {
  try {
    const res = await fetch('/admin/build/manifest.json', { cache: 'no-cache' });
    if (!res.ok) return;
    const manifest = await res.json();
    const urlsToCache = new Set();

    for (const key of Object.keys(manifest)) {
      const entry = manifest[key];
      if (entry && entry.file) {
        urlsToCache.add(`/admin/build/${entry.file}`);
      }
      if (entry && Array.isArray(entry.css)) {
        for (const cssFile of entry.css) {
          urlsToCache.add(`/admin/build/${cssFile}`);
        }
      }
    }

    // Кэшируем пачками по 8 файлов, чтобы не забивать сетевой канал браузера
    const urlArray = Array.from(urlsToCache);
    for (let i = 0; i < urlArray.length; i += 8) {
      const chunk = urlArray.slice(i, i + 8);
      await Promise.all(
        chunk.map(url =>
          cache.add(url).catch(err => {
            console.debug('[SW] Precache asset skipped:', url, err.message);
          })
        )
      );
    }
    console.log(`[SW] Precached ${urlArray.length} assets from Vite manifest successfully`);
  } catch (err) {
    console.warn('[SW] Precache Vite bundle error:', err);
  }
}

// Установка Service Worker и кэширование App Shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async cache => {
      // 1. Быстрое сохранение базовых статических файлов
      try {
        await cache.addAll(STATIC_ASSETS);
      } catch (e) {
        console.warn('[SW] Core assets precache non-critical warning:', e);
      }
      // 2. Фоновое кэширование полной сборки Vite
      precacheViteBundle(cache).catch(() => {});
    }).then(() => self.skipWaiting())
  );
});

// Активация и очистка старых версий кэша
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => clients.claim())
  );
});

// Push-уведомления
self.addEventListener('push', event => {
  if (!event.data) return;

  try {
    const data = event.data.json();
    const title = data.title || 'Новое уведомление';
    const options = {
      body: data.body || '',
      icon: data.icon || '/favicon.ico',
      badge: '/favicon.ico',
      vibrate: [200, 100, 200],
      tag: data.tag,
      data: {
        url: data.url || '/admin/dashboard',
        event_type: data.event_type
      }
    };

    event.waitUntil(
      self.registration.showNotification(title, options)
    );
  } catch (err) {
    console.error('Error parsing push data:', err);
    event.waitUntil(
      self.registration.showNotification('FoodTech Admin', {
        body: event.data.text(),
        icon: '/favicon.ico',
        badge: '/favicon.ico'
      })
    );
  }
});

// Клик по уведомлению
self.addEventListener('notificationclick', event => {
  event.notification.close();

  const clickActionUrl = event.notification.data ? event.notification.data.url : '/admin/dashboard';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windowClients => {
      for (let i = 0; i < windowClients.length; i++) {
        const client = windowClients[i];
        const hasAdmin = client.url.includes('/admin');
        const hasPers = client.url.includes('/pers');
        if ((hasAdmin || hasPers) && 'focus' in client) {
          client.postMessage({
            type: 'navigate',
            url: clickActionUrl
          });
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(clickActionUrl);
      }
    })
  );
});

// Обработка сетевых запросов: Offline Fallback & Cache-First для статики
self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // Пропускаем не-GET запросы и обращения к API / WebSocket
  if (req.method !== 'GET' || url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws')) {
    return;
  }

  // 1. Для сборки Vite (/build/), скриптов, стилей, картинок, шрифтов — Stale-While-Revalidate
  if (
    url.pathname.startsWith('/build/') ||
    url.pathname.startsWith('/admin/build/') ||
    url.pathname.endsWith('.js') ||
    url.pathname.endsWith('.css') ||
    url.pathname.endsWith('.woff2') ||
    url.pathname.endsWith('.woff') ||
    url.pathname.endsWith('.png') ||
    url.pathname.endsWith('.svg') ||
    url.pathname.endsWith('.ico')
  ) {
    event.respondWith(
      caches.open(CACHE_NAME).then(cache => {
        return cache.match(req).then(cachedResponse => {
          const fetchPromise = fetch(req).then(networkResponse => {
            if (networkResponse && networkResponse.status === 200) {
              cache.put(req, networkResponse.clone());
            }
            return networkResponse;
          }).catch(() => cachedResponse);

          return cachedResponse || fetchPromise;
        });
      })
    );
    return;
  }

  // 2. Для HTML навигации (/admin или /pers) — Network-First с мгновенным fallback на закэшированную страницу
  if (req.mode === 'navigate' || req.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(req).then(networkResponse => {
        if (networkResponse && networkResponse.status === 200) {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(req, responseClone);
          });
        }
        return networkResponse;
      }).catch(async () => {
        // При обрыве связи отдаем сохраненный каркас страницы
        const cached = await caches.match(req);
        if (cached) return cached;

        // Fallback: пробуем вернуть точный корень раздела
        if (url.pathname.startsWith('/pers')) {
          const rootPers = await caches.match('/pers');
          if (rootPers) return rootPers;
        } else {
          const rootAdmin = await caches.match('/admin');
          if (rootAdmin) return rootAdmin;
        }

        return new Response(
          '<h3 style="font-family:sans-serif;text-align:center;margin-top:20vh;color:#333;">Автономный режим (Vezuroll)<br><small style="color:gray;">Интерфейс подгружается из кэша устройства...</small></h3>',
          { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
        );
      })
    );
    return;
  }
});
