# Лог изменений Gemini
Дата: 10.06.2026
Время: 20:45
Задача: Улучшение UI настроек времени активности подписок VK бота.

## Исходное состояние изменяемого участка в `vk-notifications_utf8.vue`:
### Секция `<script setup>` (строки 180-182):
```javascript
const API_BASE = '/api/v1/vk-bot'
```
*(Сюда мы добавим computed `hoursList`)*

### Шаблон (строки 637-642):
```html
                      <div class="d-flex align-center gap-2 mt-2">
                        <span class="text-caption">Активно:</span>
                        <VTextField :model-value="accountSubscriptions.find(s => s.event_type === event.id).active_start_hour" type="number" min="0" max="23" density="compact" variant="outlined" hide-details style="width: 60px" suffix="ч" @update:model-value="(val) => updateSubscription(event.id, 'interval', accountSubscriptions.find(s => s.event_type === event.id).interval_minutes, parseInt(val), accountSubscriptions.find(s => s.event_type === event.id).active_end_hour)" />
                        <span>-</span>
                        <VTextField :model-value="accountSubscriptions.find(s => s.event_type === event.id).active_end_hour" type="number" min="0" max="23" density="compact" variant="outlined" hide-details style="width: 60px" suffix="ч" @update:model-value="(val) => updateSubscription(event.id, 'interval', accountSubscriptions.find(s => s.event_type === event.id).interval_minutes, accountSubscriptions.find(s => s.event_type === event.id).active_start_hour, parseInt(val))" />
                      </div>
```

## Изменения:
- Будет добавлен `hoursList` в script setup.
- В шаблоне `VTextField` будут заменены на выпадающие списки `VSelect` с форматированными значениями часов.
- Будет добавлено красивое оформление с иконкой часов `mdi-clock-outline`.
