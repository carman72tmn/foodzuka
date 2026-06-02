# Инвентаризация инфраструктуры VPS сервера FoodZuka

Данный документ содержит полный перечень ПО, установленного на сервере, с указанием версий и назначения.

**Дата последнего обновления:** 01.05.2026

---

## 1. Операционная система и Ядро
| Компонент | Значение |
| :--- | :--- |
| **Дистрибутив** | Ubuntu 24.04.4 LTS (Noble) |
| **Ядро** | Linux 6.8.0-110-generic x86_64 |
| **Архитектура** | x86_64 |

## 2. Среда выполнения и Контейнеризация
| Инструмент | Версия | Примечание |
| :--- | :--- | :--- |
| **Docker Engine** | 28.2.2 | Основная среда запуска сервисов |
| **Docker Compose** | 2.37.1 | Управление стеком через `docker-compose.yml` |

## 3. Список Docker Контейнеров (Стек)
| Имя контейнера | Образ (Image) | Назначение | Версия ПО |
| :--- | :--- | :--- | :--- |
| `foodtech-nginx` | `nginx:alpine` | Реверс-прокси, SSL, статика | Nginx 1.29.7 |
| `foodtech-db` | `postgres:15-alpine` | Основная БД PostgreSQL | PostgreSQL 15.10 |
| `foodtech-redis` | `redis:alpine` | Кэш и брокер Celery | Redis 7.2.4 |
| `foodtech-backend` | `foodzuka-backend` | API на FastAPI (Python) | Python 3.12 |
| `foodtech-worker` | `foodzuka-worker` | Фоновые задачи Celery | Celery 5.3.6 |
| `foodtech-admin` | `foodzuka-admin` | Админ-панель (Laravel/PHP) | PHP 8.4.20, Laravel 11.36.1 |
| `foodtech-frontend` | `foodzuka-frontend` | Фронтенд (Vue.js) | Vite + Vue 3 |
| `foodtech-bot` | `foodzuka-bot` | Telegram Bot | Python 3.12 |
| `foodtech-certbot` | `certbot/certbot` | Автопродление SSL | Latest |

## 4. Языки и Системные инструменты (Хост)
| Инструмент | Версия |
| :--- | :--- |
| **Python** | 3.12.3 |
| **Node.js** | v20.20.2 |
| **npm** | 10.8.2 |

## 5. Основные библиотеки и фреймворки

### Backend (Python/FastAPI)
- **FastAPI**: 0.109.2
- **SQLAlchemy**: 2.0.27
- **Pydantic**: 2.6.1
- **Httpx**: 0.27.0
- **Pandas**: 2.2.0

### Admin Panel (Frontend/Vue)
- **Vue.js**: 3.5.13
- **Vuetify**: 3.7.5
- **Pinia**: 2.3.0
- **Vite**: 5.4.11

## 6. Конфигурационные файлы
- **docker-compose.yml**: `/root/foodzuka/docker-compose.yml`
- **Nginx Config**: `/root/foodzuka/configs/nginx/default.conf`
- **Environment**: `/root/foodzuka/.env`, `/root/foodzuka/backend/.env`, `/root/foodzuka/admin/.env`

## 7. Ресурсы системы
- **Диск**: (проверено через `df -h`) — система установлена на основном разделе `/`.
- **Память**: (проверено через `free -h`) — доступный объем используется для работы Docker-контейнеров.

---
> [!NOTE]
> Все изменения в инфраструктуре (обновления версий, добавление модулей) должны фиксироваться в данном документе.
