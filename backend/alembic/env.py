"""
Конфигурация Alembic для миграций базы данных
"""
from logging.config import fileConfig
from sqlmodel import SQLModel
from sqlalchemy import engine_from_config, pool
from alembic import context

# Импортируем все модели для автогенерации миграций
import app.models
from app.core.config import settings

# Конфигурация Alembic
config = context.config

# Устанавливаем URL базы данных из настроек
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Настройка логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для автогенерации
target_metadata = SQLModel.metadata


def include_none_laravel_tables(object, name, type_, reflected, compare_to):
    """
    Фильтр для игнорирования таблиц, управляемых Laravel
    """
    if type_ == "table":
        ignore_tables = [
            "migrations",
            "sessions",
            "password_reset_tokens",
            "cache",
            "cache_locks",
            "jobs",
            "job_batches",
            "failed_jobs",
            "personal_access_tokens",
            "nps_reviews",
            "telegram_bots"
        ]
        return name not in ignore_tables
    return True

def run_migrations_offline() -> None:
    """
    Запуск миграций в 'offline' режиме.
    Генерирует SQL-скрипты без подключения к БД.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_none_laravel_tables
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Запуск миграций в 'online' режиме.
    Выполняет миграции напрямую в БД.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_none_laravel_tables
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
