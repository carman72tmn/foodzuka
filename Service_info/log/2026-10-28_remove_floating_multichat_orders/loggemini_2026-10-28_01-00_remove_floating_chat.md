# Лог задачи: Удаление плавающей кнопки мультичата со страницы заказов

- **Дата и время**: 28.10.2026 01:00 (UTC+5)
- **Исполнитель**: Antigravity Assistant
- **Статус**: Выполнено успешно (100%)

---

## 1. Описание задачи
Полностью удалить плавающий виджет мультичата (`FloatingMultichat.vue`) со страницы «Заказы» (`/orders`) для существенного ускорения начальной загрузки и рендеринга страницы.

## 2. Внесенные изменения
1. **`admin/resources/js/pages/orders/index.vue`**:
   - Удален импорт `FloatingMultichat from "@/components/FloatingMultichat.vue"`.
   - Добавлен `useRouter` из `vue-router`.
   - Удален тяжелый фоновый запрос `fetchRecentMultichatDialogs()` при монтировании компонента.
   - Удалена ссылка `floatingMultichatRef` и тег `<FloatingMultichat ref="floatingMultichatRef" @view-order="openOrderById" />`.
   - Метод `openCustomerFloatingChat` переписан на `openCustomerChat`: при клике на иконку диалога в строке заказа пользователя перенаправляет в основной раздел Мультичата (`/multichat?search=...`).
   - Удалены все неиспользуемые стили дока и плавающих карточек чата (`.floating-multichat-dock`, `.floating-chats-container`, `.floating-chat-card`).

2. **Сборка и развертывание на VPS**:
   - Файл безопасно передан на сервер с сохранением кодировки UTF-8.
   - Выполнен `npm run build` (Vite 5.4.21).
   - Сформированы свежие ассеты в `admin/public/build/assets/`.
   - Перезапущены контейнеры `foodtech-nginx` и `foodtech-admin`.
   - Проверен статус `https://vezuroll.ru/admin/`: **200 OK**.

## 3. Результаты
- Страница заказов больше не запрашивает массив диалогов мультичата при открытии.
- Значительно снизилось количество одновременно рендеримых DOM-элементов.
- Сохранена вся логика работы со списком заказов, таймерами, модальными окнами и Real-Time обновлениями по WebSocket.
