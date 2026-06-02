
import sys
import os
from datetime import datetime, timezone

# Добавляем путь к backend, чтобы можно было импортировать модули приложения
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.role import Role, Permission, RolePermissionLink
from app.models.user import User

PERMISSIONS = [
    # Заказы
    {"name": "Просмотр заказов", "code": "orders_view", "category": "Заказы", "description": "Доступ к списку заказов"},
    {"name": "Редактирование заказов", "code": "orders_edit", "category": "Заказы", "description": "Изменение статусов, состава и данных заказа"},
    {"name": "Удаление заказов", "code": "orders_delete", "category": "Заказы", "description": "Возможность удалять заказы"},
    {"name": "Экспорт заказов", "code": "orders_export", "category": "Заказы", "description": "Выгрузка заказов в Excel/CSV"},
    
    # Меню
    {"name": "Просмотр меню", "code": "menu_view", "category": "Меню", "description": "Просмотр товаров и категорий"},
    {"name": "Управление меню", "code": "menu_edit", "category": "Меню", "description": "Создание, редактирование и удаление товаров"},
    {"name": "Синхронизация меню", "code": "menu_sync", "category": "Меню", "description": "Запуск синхронизации с iiko"},
    
    # Пользователи
    {"name": "Просмотр пользователей", "code": "users_view", "category": "Пользователи", "description": "Доступ к списку сотрудников в админке"},
    {"name": "Управление пользователями", "code": "users_edit", "category": "Пользователи", "description": "Создание и редактирование учетных записей"},
    {"name": "Управление ролями", "code": "roles_manage", "category": "Пользователи", "description": "Настройка прав доступа и создание ролей"},
    
    # Клиенты
    {"name": "Просмотр клиентов", "code": "customers_view", "category": "Клиенты", "description": "Просмотр базы гостей"},
    {"name": "Редактирование клиентов", "code": "customers_edit", "category": "Клиенты", "description": "Изменение данных гостей и баланса бонусов"},
    
    # Отчеты
    {"name": "Просмотр отчетов", "code": "reports_view", "category": "Отчеты", "description": "Общие финансовые отчеты"},
    {"name": "Отчеты курьеров", "code": "courier_reports_view", "category": "Отчеты", "description": "Просмотр логов и статистики курьеров"},
    
    # Настройки
    {"name": "Просмотр настроек", "code": "settings_view", "category": "Настройки", "description": "Доступ к настройкам системы"},
    {"name": "Изменение настроек", "code": "settings_edit", "category": "Настройки", "description": "Редактирование интеграций и параметров сайта"},
]

def seed_rbac():
    with Session(engine) as session:
        print("Starting RBAC seeding...")
        
        # 1. Добавление прав
        db_permissions = []
        for p_data in PERMISSIONS:
            existing = session.exec(select(Permission).where(Permission.code == p_data["code"])).first()
            if not existing:
                p = Permission(**p_data)
                session.add(p)
                db_permissions.append(p)
                print(f"Created permission: {p.code}")
            else:
                existing.name = p_data["name"]
                existing.category = p_data["category"]
                existing.description = p_data["description"]
                session.add(existing)
                db_permissions.append(existing)
        
        session.commit()
        for p in db_permissions:
            session.refresh(p)
            
        # 2. Создание системных ролей
        # Администратор
        admin_role = session.exec(select(Role).where(Role.code == "SUPER_ADMIN")).first()
        if not admin_role:
            admin_role = Role(
                name="Администратор",
                code="SUPER_ADMIN",
                description="Полный доступ ко всем функциям системы",
                is_system=True
            )
            session.add(admin_role)
            print("Created SUPER_ADMIN role")
        else:
            admin_role.is_system = True
            session.add(admin_role)
            
        session.commit()
        session.refresh(admin_role)
        
        # Привязка всех прав к администратору
        admin_role.permissions = db_permissions
        session.add(admin_role)
        session.commit()
        print(f"Assigned {len(db_permissions)} permissions to SUPER_ADMIN")
        
        # 3. Привязка дефолтного пользователя к роли
        default_user = session.exec(select(User).where(User.username == "0001")).first()
        if default_user:
            default_user.role_id = admin_role.id
            default_user.is_superuser = True # На всякий случай оставляем и этот флаг
            session.add(default_user)
            session.commit()
            print("Assigned user '0001' to SUPER_ADMIN role")
        
        print("RBAC seeding completed successfully!")

if __name__ == "__main__":
    seed_rbac()
