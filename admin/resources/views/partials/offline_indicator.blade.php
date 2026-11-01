<!-- Offline Network Status Indicator -->
<div id="offline-network-banner" style="display: none; position: fixed; top: 0; left: 0; right: 0; z-index: 9999999; background: linear-gradient(90deg, #ed6c02, #c62828); color: #ffffff; padding: 10px 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 13.5px; font-weight: 500; text-align: center; box-shadow: 0 4px 16px rgba(0,0,0,0.35); transform: translateY(-100%); transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1), background 0.3s ease;">
  <div style="display: flex; align-items: center; justify-content: center; gap: 10px; flex-wrap: wrap;">
    <span id="offline-banner-dot" style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #ffeb3b; box-shadow: 0 0 8px #ffeb3b; animation: offlineDotPulse 1.5s infinite;"></span>
    <span id="offline-banner-text">⚡ <strong>Автономный режим:</strong> отсутствует прямое подключение к интернету. Отображаются закэшированные данные.</span>
    <button id="offline-banner-btn" onclick="window.checkNetworkConnection && window.checkNetworkConnection(true)" style="margin-left: 8px; background: rgba(255,255,255,0.22); border: 1px solid rgba(255,255,255,0.45); color: #ffffff; padding: 3px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 600; outline: none; transition: background 0.2s;">Проверить связь</button>
  </div>
</div>

<style>
@keyframes offlineDotPulse {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 12px #ffeb3b; }
  100% { transform: scale(0.95); opacity: 0.8; }
}
#offline-banner-btn:hover {
  background: rgba(255,255,255,0.35) !important;
}
</style>

<script>
(function() {
  const banner = document.getElementById('offline-network-banner');
  const bannerText = document.getElementById('offline-banner-text');
  const bannerDot = document.getElementById('offline-banner-dot');
  const bannerBtn = document.getElementById('offline-banner-btn');
  let isOffline = false;
  let restoreTimer = null;
  let pingInterval = null;

  function showOfflineBanner() {
    if (isOffline) return;
    isOffline = true;
    if (restoreTimer) clearTimeout(restoreTimer);

    banner.style.display = 'block';
    banner.style.background = 'linear-gradient(90deg, #ed6c02, #c62828)';
    bannerDot.style.backgroundColor = '#ffeb3b';
    bannerDot.style.boxShadow = '0 0 8px #ffeb3b';
    bannerDot.style.animation = 'offlineDotPulse 1.5s infinite';
    bannerText.innerHTML = '⚡ <strong>Автономный режим:</strong> отсутствует прямое подключение к сети. Отображаются сохраненные данные.';
    bannerBtn.style.display = 'inline-block';
    
    // Плавная анимация выезда
    setTimeout(() => {
      banner.style.transform = 'translateY(0)';
    }, 20);
  }

  function showOnlineBanner() {
    if (!isOffline) return;
    isOffline = false;

    banner.style.background = 'linear-gradient(90deg, #2e7d32, #1b5e20)';
    bannerDot.style.backgroundColor = '#a5d6a7';
    bannerDot.style.boxShadow = '0 0 8px #a5d6a7';
    bannerDot.style.animation = 'none';
    bannerText.innerHTML = '✓ <strong>Подключение восстановлено:</strong> связь с сервером актуализирована.';
    bannerBtn.style.display = 'none';

    if (restoreTimer) clearTimeout(restoreTimer);
    restoreTimer = setTimeout(() => {
      banner.style.transform = 'translateY(-100%)';
      setTimeout(() => {
        if (!isOffline) {
          banner.style.display = 'none';
        }
      }, 400);
    }, 3500);
  }

  window.checkNetworkConnection = function(manualClick) {
    if (manualClick && bannerBtn) {
      bannerBtn.innerText = 'Проверка...';
      bannerBtn.disabled = true;
    }

    // Проверяем легкий локальный ресурс без кэша с таймаутом 3.5 сек
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3500);

    fetch('/favicon.ico?_ping=' + Date.now(), {
      method: 'HEAD',
      cache: 'no-store',
      signal: controller.signal
    }).then(res => {
      clearTimeout(timeoutId);
      if (manualClick && bannerBtn) {
        bannerBtn.innerText = 'Проверить связь';
        bannerBtn.disabled = false;
      }
      if (res.ok || res.status === 304 || res.status === 200) {
        showOnlineBanner();
      } else {
        showOfflineBanner();
      }
    }).catch(err => {
      clearTimeout(timeoutId);
      if (manualClick && bannerBtn) {
        bannerBtn.innerText = 'Проверить связь';
        bannerBtn.disabled = false;
      }
      showOfflineBanner();
    });
  };

  // Нативные события браузера
  window.addEventListener('offline', function() {
    showOfflineBanner();
  });

  window.addEventListener('online', function() {
    window.checkNetworkConnection(false);
  });

  // Первичная проверка при старте
  if (!navigator.onLine) {
    showOfflineBanner();
  } else {
    // Фоновая проверка доступности каждые 25 секунд
    pingInterval = setInterval(() => {
      // Пингуем только если экран активен
      if (!document.hidden) {
        window.checkNetworkConnection(false);
      }
    }, 25000);
  }
})();
</script>
