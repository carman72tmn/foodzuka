"""
Настройка подключения к базе данных PostgreSQL
Использует SQLModel (построен на SQLAlchemy 2.0)
"""
from sqlmodel import Session, create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

# Создание движка базы данных
# echo=True выводит SQL запросы в консоль (только для отладки)
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,          # Отключаем вывод SQL в stdout во избежание блокировок I/O и переполнения логов
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_size=15,        # Базовый пул 15 соединений
    max_overflow=25,     # Запас соединений до 25 (макс 40 из 100 доступных в Postgres)
    pool_timeout=30,     # 30с таймаут ожидания соединения
    pool_recycle=1800    # Пересоздавать соединения каждые 30 минут
)

# Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session
)


def get_session():
    """
    Dependency для получения сессии базы данных в FastAPI endpoints
    Автоматически откатывает незавершенные транзакции и закрывает сессию после завершения запроса,
    предотвращая накопление открытых транзакций (idle in transaction) и утечки памяти
    """
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        try:
            session.rollback()
        except Exception:
            pass
        session.close()

from contextlib import contextmanager

@contextmanager
def get_session_sync():
    """
    Контекстный менеджер для получения сессии базы данных в синхронном коде.
    Использование: with get_session_sync() as session: ...
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
