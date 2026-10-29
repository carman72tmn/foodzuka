"""
Модель настроек бота активности ВКонтакте
"""
from typing import Optional
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel, Column, JSON


class VkActivitySettings(SQLModel, table=True):
    """Таблица настроек начисления баллов за активность ВК"""
    __tablename__ = "vk_activity_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    vk_bot_connection_id: int = Field(index=True, unique=True, description="ID подключения бота VK")
    is_active: bool = Field(default=True, description="Статус работы бота активности")
    
    # Настройки баллов за лайки
    points_like: int = Field(default=5, description="Баллы за лайк поста")
    points_like_first_n: int = Field(default=10, description="Баллы первым N лайкнувшим")
    like_first_n_count: int = Field(default=5, description="Кол-во первых лайкнувших пользователей")
    points_like_fast: int = Field(default=8, description="Баллы за быстрый лайк")
    like_fast_seconds: int = Field(default=900, description="Время для быстрого лайка в секундах")
    
    # Настройки баллов за комментарии
    points_comment: int = Field(default=10, description="Баллы за комментарий")
    points_comment_first_n: int = Field(default=15, description="Баллы первым N комментаторам")
    comment_first_n_count: int = Field(default=5, description="Кол-во первых комментаторов")
    points_comment_fast: int = Field(default=12, description="Баллы за быстрый комментарий")
    comment_fast_seconds: int = Field(default=900, description="Время для быстрого комментария в секундах")
    min_comment_length: int = Field(default=5, description="Минимальная длина комментария в символах")
    max_comments_per_post: int = Field(default=3, description="Максимальное количество комментариев под одним постом")
    ignore_consecutive_comments: bool = Field(default=True, description="Игнорировать идущие подряд комментарии от одного пользователя")
    ignore_stickers: bool = Field(default=True, description="Игнорировать комментарии, содержащие только стикеры")
    
    # Настройки баллов за репосты
    points_repost: int = Field(default=20, description="Баллы за репост поста")
    
    # Настройки баллов за опросы
    points_poll: int = Field(default=5, description="Баллы за участие в опросе")
    
    # Настройки баллов за подписку (вступление в группу)
    points_join: int = Field(default=50, description="Баллы за вступление в сообщество")
    
    # Настройки штрафных таймеров
    penalty_duration_seconds: int = Field(default=3600, description="Время действия штрафного таймера в секундах")
    penalty_points: int = Field(default=0, description="Количество баллов, начисляемых за повторное действие во время штрафа")
    msg_penalty: Optional[str] = Field(default=None, description="Текст уведомления о штрафном времени и баллах")
    
    # Период конкурса и давность постов
    period_start_date: Optional[datetime] = Field(default=None, description="Дата старта конкурса активности")
    period_duration_days: int = Field(default=7, description="Продолжительность конкурса в днях (0 - бессрочно)")
    ignored_post_ids: Optional[str] = Field(default=None, description="Список ID постов через запятую, за активности на которых баллы не начисляются")
    post_max_age_days: int = Field(default=7, description="Срок давности постов в днях (0 - без ограничений)")
    override_keywords: Optional[str] = Field(default="", description="Ключевые слова-исключения через запятую (посты с ними участвуют независимо от возраста)")

    # Кастомные сообщения от бота активности
    msg_points_like: Optional[str] = Field(default=None, description="Текст уведомления за лайк")
    msg_points_comment: Optional[str] = Field(default=None, description="Текст уведомления за комментарий")
    msg_points_repost: Optional[str] = Field(default=None, description="Текст уведомления за репост")
    msg_points_poll: Optional[str] = Field(default=None, description="Текст уведомления за опрос")
    msg_points_join: Optional[str] = Field(default=None, description="Текст уведомления за вступление")
    msg_balance_info: Optional[str] = Field(default=None, description="Текст ответа на запрос баланса")
    msg_unlinked_notice: Optional[str] = Field(default=None, description="Текст подсказки для непривязанного пользователя")
    
    # Синхронизация с iikoCard
    sync_with_iiko: bool = Field(default=False, description="Включить синхронизацию баллов с iiko бонусами")
    iiko_conversion_rate: float = Field(default=1.0, description="Курс конвертации (1 балл активности = X бонусов в iiko)")
    iiko_sync_mode: str = Field(default="realtime", description="Режим синхронизации: realtime (в реальном времени) или manual (вручную)")
    iiko_summing_logic: str = Field(default="both", description="Логика суммирования баланса: both (iikoCard + ВК), iiko_only (только iikoCard), vk_only (только ВК)")
    sync_on_verification: bool = Field(default=True, description="Синхронизировать при верификации телефона")
    sync_on_balance_request: bool = Field(default=True, description="Синхронизировать при запросе баланса")
    last_sync_at: Optional[datetime] = Field(default=None, description="Дата и время последней синхронизации с iiko")
    vk_bot_token: Optional[str] = Field(default=None, description="Индивидуальный ключ сообщества для бота")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
