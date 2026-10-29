"""
Модели для ботов поздравления именинников ВКонтакте
"""
from typing import Optional
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel

class VkBirthdayBot(SQLModel, table=True):
    """Настройки бота поздравления именинников ВК"""
    __tablename__ = "vk_birthday_bots"

    id: Optional[int] = Field(default=None, primary_key=True)
    vk_bot_connection_id: int = Field(
        foreign_key="vk_bot_connections.id", 
        index=True, 
        description="Ссылка на подключение бота ВК"
    )
    is_active: bool = Field(default=True, description="Активен ли бот")
    
    # Контент поздравления
    message_template: str = Field(
        default="Поздравляем с днем рождения наших подписчиков: {names}! 🎉 Желаем отличного настроения и приятного аппетита! 🎂🍕", 
        description="Текст шаблона с тегом {names}"
    )
    image_url: Optional[str] = Field(default=None, description="Путь или URL картинки для поздравления")
    
    # Настройки отображения имен
    include_names: bool = Field(default=True, description="Указывать ли имена именинников в посте")
    name_format: str = Field(default="fullname", description="Формат имени: fullname (Имя Фамилия) или name_only (Имя)")
    make_links: bool = Field(default=True, description="Делать ли имя ссылкой на профиль ВК")
    
    # Настройки времени публикации
    publish_time: str = Field(default="10:00", description="Время автопубликации (ЧЧ:ММ)")
    last_run_date: Optional[str] = Field(default=None, description="Дата последнего запуска (ГГГГ-ММ-ДД), чтобы не дублировать")
    
    # Настройки удаления
    delete_mode: str = Field(default="interval", description="Режим удаления: interval (через промежуток) или exact_time (в определенное время)")
    delete_interval_minutes: int = Field(default=720, description="Интервал автоудаления в минутах (для режима interval)")
    delete_time: Optional[str] = Field(default="22:00", description="Время удаления в тот же день (ЧЧ:ММ) (для режима exact_time)")
    vk_bot_token: Optional[str] = Field(default=None, description="Индивидуальный ключ сообщества для бота")
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class VkBirthdayPost(SQLModel, table=True):
    """Посты поздравлений именинников, опубликованные на стене и ожидающие удаления"""
    __tablename__ = "vk_birthday_posts"

    id: Optional[int] = Field(default=None, primary_key=True)
    birthday_bot_id: int = Field(
        foreign_key="vk_birthday_bots.id", 
        index=True, 
        description="Ссылка на настройки бота"
    )
    vk_group_id: int = Field(description="ID группы ВКонтакте")
    post_id: int = Field(description="ID опубликованного поста на стене")
    
    created_at: datetime = Field(default_factory=utc_now, description="Время публикации")
    delete_at: datetime = Field(index=True, description="Когда нужно удалить пост")
    is_deleted: bool = Field(default=False, description="Удален ли пост из ВКонтакте")
