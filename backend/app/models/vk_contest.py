"""
Модели для проведения конкурсов ВКонтакте (геймификация)
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON

class VkContest(SQLModel, table=True):
    """Настройки конкурса геймификации"""
    __tablename__ = "vk_contests"

    id: Optional[int] = Field(default=None, primary_key=True)
    vk_bot_connection_id: int = Field(
        foreign_key="vk_bot_connections.id", 
        index=True, 
        description="Ссылка на подключение бота ВК"
    )
    is_active: bool = Field(default=False, description="Запущен ли конкурс в данный момент")
    title: str = Field(description="Название конкурса")
    rules_text: str = Field(default="", description="Описание правил конкурса")
    
    # roulette, safe, knb, chests, seabattle, battle
    game_type: str = Field(default="roulette", description="Тип игры конкурса")
    penalty_percent: int = Field(default=10, description="Процент штрафных клеток (0-50%)")
    bonus_percent: int = Field(default=20, description="Процент бонусных клеток (0-50%)")
    post_id: Optional[int] = Field(default=None, description="ID опубликованного поста в ВК")
    
    # Список призов: [{"id": 1, "name": "Пицца", "qty": 5, "won_count": 0}, ...]
    prizes: List[Dict[str, Any]] = Field(
        default=[],
        sa_column=Column(JSON),
        description="JSON-список призов с лимитами"
    )

    # Настройки попыток
    start_attempts: int = Field(default=3, description="Начальное число попыток для каждого подписчика")
    max_attempts: int = Field(default=10, description="Максимально возможное число попыток")
    delay_between_moves: int = Field(default=60, description="Задержка между ходами в секундах")
    
    # Условия выдачи бонусных попыток
    repost_attempts: int = Field(default=3, description="Бонусных попыток за репост")
    subscribe_attempts: int = Field(default=0, description="Бонусных попыток за вступление в группу")
    like_attempts: int = Field(default=1, description="Бонусных попыток за лайк к посту")

    # Специфичные настройки игр
    safe_code: Optional[str] = Field(default=None, description="Код для игры Сейф (из 4 цифр)")
    
    # Сетка игрового поля (для сундуков/морского боя):
    # {"A1": {"prize_id": 1, "hit": False}, "B5": {"prize_id": None, "hit": True}, ...}
    game_field_data: Dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON),
        description="JSON-сетка ячеек игрового поля"
    )

    # Шаблоны сообщений бота
    msg_miss: str = Field(
        default="🎰 {name}, увы! Этот сектор оказался пустым. Попробуйте еще раз!",
        description="Шаблон при промахе"
    )
    msg_win: str = Field(
        default="🎉 Поздравляем, {name}! Вы выиграли приз: {prize}! Инструкция по получению отправлена в ЛС.",
        description="Шаблон при выигрыше"
    )
    msg_out_of_attempts: str = Field(
        default="❌ {name}, у вас закончились попытки!",
        description="Шаблон, когда попытки закончились"
    )
    msg_cooldown: str = Field(
        default="⌛ {name}, вы делаете ходы слишком часто! Пожалуйста, подождите еще {cooldown} сек.",
        description="Шаблон при кулдауне ходов"
    )
    msg_subscribe_needed: str = Field(
        default="⚠️ {name}, вы не подписаны на наше сообщество! Для участия в конкурсе обязательно подпишитесь на группу.",
        description="Шаблон при отсутствии подписки"
    )
    msg_like_needed: str = Field(
        default="❤️ {name}, для участия необходимо поставить лайк к этому посту!",
        description="Шаблон при отсутствии лайка"
    )
    msg_repost_needed: str = Field(
        default="📢 {name}, для участия необходимо сделать репост этого поста на свою страницу!",
        description="Шаблон при отсутствии репоста"
    )
    msg_invalid_format: str = Field(
        default="❓ {name}, я не понял ваш ход. Пожалуйста, напишите правильный формат ходов (например, {example}).",
        description="Шаблон при неверном формате хода"
    )
    msg_pm_congratulations: str = Field(
        default="🎉 Здравствуйте, {name}!\n\nВы выиграли в конкурсе «{title}» приз:\n🎁 {prize}!\n\n🔑 Ваш уникальный промокод для заказа: {code}\n\nВведите его в корзине при оформлении заказа на сайте или назовите оператору.",
        description="Шаблон ЛС-поздравления с промокодом"
    )

    # Продвинутые настройки игры
    can_win_once: bool = Field(default=True, description="Можно выиграть только один раз")
    help_draw_prizes: bool = Field(default=True, description="Ускорять выдачу призов, если конкурс затянулся")
    black_list: List[str] = Field(default=[], sa_column=Column(JSON), description="Черный список ID пользователей")
    white_list: List[str] = Field(default=[], sa_column=Column(JSON), description="Белый список ID пользователей")
    remind_winner_pm: bool = Field(default=False, description="Включить напоминание о незабранном призе в ЛС")
    remind_attempts: bool = Field(default=True, description="Включить напоминания о попытках")
    remind_attempts_count: int = Field(default=3, description="Количество напоминаний о попытках (1-3)")
    remind_attempts_quiet_from: int = Field(default=22, description="Тихий час от (часы по Москве)")
    remind_attempts_quiet_to: int = Field(default=8, description="Тихий час до (часы по Москве)")
    anti_prize_hunters: bool = Field(default=False, description="Включить защиту от призоловов")
    draw_type: str = Field(default="probability", description="Тип розыгрыша: probability или duration")
    draw_probability_interval: int = Field(default=100, description="Выпадать примерно каждую N попытку")
    vk_bot_token: Optional[str] = Field(default=None, description="Индивидуальный ключ сообщества для бота")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class VkContestPlayer(SQLModel, table=True):
    """Информация об участниках конкурса и их попытках"""
    __tablename__ = "vk_contest_players"

    id: Optional[int] = Field(default=None, primary_key=True)
    contest_id: int = Field(
        foreign_key="vk_contests.id", 
        index=True, 
        description="Ссылка на конкурс"
    )
    vk_user_id: int = Field(index=True, description="ID пользователя ВКонтакте")
    first_name: str = Field(description="Имя игрока")
    last_name: str = Field(description="Фамилия игрока")
    
    attempts_left: int = Field(default=3, description="Оставшееся число попыток")
    attempts_used: int = Field(default=0, description="Использованное число попыток")
    
    repost_done: bool = Field(default=False, description="Получен ли бонус за репост")
    subscribe_done: bool = Field(default=False, description="Получен ли бонус за вступление")
    like_done: bool = Field(default=False, description="Получен ли бонус за лайк")
    reminders_sent: int = Field(default=0, description="Количество отправленных напоминаний о попытках")
    penalties_hit: int = Field(default=0, description="Количество попаданий на штрафные клетки")
    is_game_over: bool = Field(default=False, description="Закончилась ли игра для участника (GAME OVER)")
    
    last_move_at: Optional[datetime] = Field(default=None, description="Время совершения последнего хода")


class VkContestWinner(SQLModel, table=True):
    """Список победителей и выданных промокодов"""
    __tablename__ = "vk_contest_winners"

    id: Optional[int] = Field(default=None, primary_key=True)
    contest_id: int = Field(
        foreign_key="vk_contests.id", 
        index=True, 
        description="Ссылка на конкурс"
    )
    vk_user_id: int = Field(index=True, description="ID пользователя ВКонтакте")
    first_name: str = Field(description="Имя победителя")
    last_name: str = Field(description="Фамилия победителя")
    
    prize_name: str = Field(description="Название выигранного приза")
    win_code: str = Field(index=True, description="Уникальный промокод (WIN-XXXXXX) для получения в iiko")
    won_at: datetime = Field(default_factory=utc_now, description="Время выигрыша")
    
    is_activated: bool = Field(default=False, description="Активирован ли промокод")
    activated_at: Optional[datetime] = Field(default=None, description="Время активации промокода")
    order_id: Optional[str] = Field(default=None, description="ID заказа, где применили промокод")


class VkContestAction(SQLModel, table=True):
    """История всех ходов и действий участников конкурсов"""
    __tablename__ = "vk_contest_actions"

    id: Optional[int] = Field(default=None, primary_key=True)
    contest_id: int = Field(
        foreign_key="vk_contests.id", 
        index=True, 
        description="Ссылка на конкурс"
    )
    vk_user_id: int = Field(index=True, description="ID пользователя ВКонтакте")
    first_name: str = Field(description="Имя игрока")
    last_name: str = Field(description="Фамилия игрока")
    
    # move, repost, like, subscribe, reminder, system
    action_type: str = Field(description="Тип действия")
    detail: str = Field(description="Детали действия")
    created_at: datetime = Field(default_factory=utc_now, description="Время совершения действия")
