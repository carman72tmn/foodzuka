# ИСПРАВЛЕНИЕ ОТОБРАЖЕНИЯ СТАТУСА НА ПЛАШКАХ КАРТОЧЕК БОТОВ
Дата: 24.10.2026 21:03 (UTC+5)

1. Проблема:
В шаблоне страницы admin/resources/js/pages/marketing/vk-bots.vue на плашках 6 новых ботов бейдж был захардкожен:
<VChip size= small color=success variant=tonal class=font-weight-bold>Активен</VChip>
Из-за этого при выключении бота в окне настроек и сохранении в БД статус на карточке не менялся.

2. Решение:
1) В скрипт vk-bots.vue добавлено реактивное состояние marketingBotsConfig и метод getMarketingBotStatus(botKey):
   - Если бот активен (is_active === true) -> бейдж Активен (зелёный success).
   - Если бот выключен (is_active === false) -> бейдж Отключен (серый secondary), а карточка визуально приглушается классом disabled-card.
2) Загрузка конфига подключена к watch(selectedConnectionId) и начальному loadData().
3) Событие @saved из VkMarketingBotModal.vue автоматически вызывает повторную загрузку loadMarketingBotsConfig(selectedConnectionId), мгновенно обновляя плашки без перезагрузки страницы.
4) Фронтенд успешно пересобран (npm run build) и развёрнут на VPS.
