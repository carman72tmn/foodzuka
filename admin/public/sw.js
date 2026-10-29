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

self.addEventListener('notificationclick', event => {
  event.notification.close();

  const clickActionUrl = event.notification.data ? event.notification.data.url : '/admin/dashboard';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windowClients => {
      // Ищем открытую вкладку админки или кабинета сотрудника
      for (let i = 0; i < windowClients.length; i++) {
        const client = windowClients[i];
        const hasAdmin = client.url.includes('/admin');
        const hasPers = client.url.includes('/pers');
        if ((hasAdmin || hasPers) && 'focus' in client) {
          // Отправляем сообщение во вкладку, чтобы сменить роут внутри Vue
          client.postMessage({
            type: 'navigate',
            url: clickActionUrl
          });
          return client.focus();
        }
      }
      // Если вкладка закрыта, открываем новое окно
      if (clients.openWindow) {
        return clients.openWindow(clickActionUrl);
      }
    })
  );
});

// Пустой обработчик fetch для соответствия требованиям PWA в Chrome/Android
self.addEventListener('fetch', event => {
  // Браузер требует наличия этого события для генерации beforeinstallprompt
});
