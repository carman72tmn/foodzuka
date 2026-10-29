"""
Сервис управления резервным копированием, автоматизацией, ротацией архивов
и системными ИИ-протоколами
"""
import os
import shutil
import subprocess
import glob
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from app.core.database import engine
from app.models.backup_settings import BackupSettings, AiPromptInstruction
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

BACKUP_DIR = os.getenv("BACKUP_DIR", "/app/backups")
PROJECT_ROOT = os.getenv("PROJECT_ROOT", "/app")
DOCS_DIR = os.getenv("DOCS_DIR", "/app/../Service_info") if os.path.exists("/app/../Service_info") else "/app/Service_info"

# Резервные пути для локальной разработки
if not os.path.exists(BACKUP_DIR):
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
    except Exception:
        pass


class BackupService:
    """Управление резервными копиями, дисковым пространством и ИИ-инструкциями"""

    def __init__(self, backup_dir: str = BACKUP_DIR):
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def get_disk_info(self) -> Dict[str, Any]:
        """Возвращает информацию о свободном дисковом пространстве на сервере"""
        try:
            total, used, free = shutil.disk_usage(self.backup_dir)
            total_gb = round(total / (1024 ** 3), 2)
            used_gb = round(used / (1024 ** 3), 2)
            free_gb = round(free / (1024 ** 3), 2)
            used_pct = round((used / total) * 100, 1) if total > 0 else 0
            return {
                "total_gb": total_gb,
                "used_gb": used_gb,
                "free_gb": free_gb,
                "used_pct": used_pct,
                "path": self.backup_dir
            }
        except Exception as e:
            logger.error(f"Ошибка получения инфо о диске: {e}")
            return {"total_gb": 30.0, "used_gb": 13.0, "free_gb": 17.0, "used_pct": 43.0, "error": str(e)}

    def list_backups(self) -> List[Dict[str, Any]]:
        """Список существующих резервных копий с метаданными"""
        items = []
        if not os.path.exists(self.backup_dir):
            return items

        files = glob.glob(os.path.join(self.backup_dir, "*"))
        for fpath in files:
            if not os.path.isfile(fpath):
                continue
            fname = os.path.basename(fpath)
            if not (fname.endswith(".sql.gz") or fname.endswith(".tar.gz") or fname.endswith(".sql") or fname.endswith(".zip")):
                continue

            try:
                stat = os.stat(fpath)
                size_bytes = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).replace(tzinfo=None)

                # Определение типа бэкапа
                if "db_" in fname or fname.endswith(".sql.gz") or fname.endswith(".sql"):
                    b_type = "db"
                    type_label = "База данных (PostgreSQL)"
                elif "code_" in fname or "foodzuka_" in fname:
                    b_type = "code"
                    type_label = "Код и конфигурации"
                else:
                    b_type = "full"
                    type_label = "Архив системы"

                # Форматирование размера
                if size_bytes >= 1024 ** 3:
                    size_human = f"{round(size_bytes / (1024 ** 3), 2)} ГБ"
                elif size_bytes >= 1024 ** 2:
                    size_human = f"{round(size_bytes / (1024 ** 2), 1)} МБ"
                else:
                    size_human = f"{round(size_bytes / 1024, 1)} КБ"

                items.append({
                    "filename": fname,
                    "type": b_type,
                    "type_label": type_label,
                    "size_bytes": size_bytes,
                    "size_human": size_human,
                    "created_at": mtime.isoformat(),
                    "created_at_human": mtime.strftime("%d.%m.%Y %H:%M:%S")
                })
            except Exception as e:
                logger.warning(f"Ошибка чтения файла бэкапа {fname}: {e}")

        # Сортировка по дате (свежие сверху)
        items.sort(key=lambda x: x["created_at"], reverse=True)
        return items

    def create_backup(self, backup_type: str = "db_and_code") -> Dict[str, Any]:
        """
        Создание резервной копии:
        - db_only: дамп БД
        - code_only: тарбол кода (бэкенд, фронтенд, конфиги, Service_info)
        - db_and_code: и база данных, и код
        - full_with_media: полный архив включая загруженные медиа
        """
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        created_files = []

        try:
            # 1. Дамп базы данных PostgreSQL
            if backup_type in ("db_only", "db_and_code", "full_with_media"):
                db_filename = f"db_backup_{timestamp}.sql.gz"
                db_filepath = os.path.join(self.backup_dir, db_filename)

                # Запуск pg_dump внутри docker окружения
                cmd = (
                    f"PGPASSWORD=postgres pg_dump -h db -U foodtech_user -d foodtech_db "
                    f"| gzip > '{db_filepath}'"
                )
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if res.returncode != 0:
                    raise RuntimeError(f"Ошибка pg_dump: {res.stderr}")

                if os.path.exists(db_filepath) and os.path.getsize(db_filepath) > 0:
                    created_files.append(db_filename)
                else:
                    raise RuntimeError("Файл дампа базы данных пуст или не был создан.")

            # 2. Архив кода и настроек
            if backup_type in ("code_only", "db_and_code", "full_with_media"):
                code_filename = f"code_backup_{timestamp}.tar.gz"
                code_filepath = os.path.join(self.backup_dir, code_filename)

                # Исключения для экономии места
                excludes = [
                    "--exclude=node_modules",
                    "--exclude=venv",
                    "--exclude=__pycache__",
                    "--exclude=.git",
                    "--exclude=build",
                    "--exclude=backups/*.tar.gz",
                    "--exclude=backups/*.sql.gz",
                    "--exclude=trash"
                ]
                if backup_type != "full_with_media":
                    excludes.append("--exclude=media/img")

                exclude_str = " ".join(excludes)
                # Архивируем директории бэкенда, фронтенда и документации
                parent_dir = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))
                target_dir = os.path.basename(parent_dir) if os.path.exists(parent_dir) else "foodzuka"

                cmd = f"tar {exclude_str} -czf '{code_filepath}' -C '{parent_dir}' {target_dir}"
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if res.returncode == 0 and os.path.exists(code_filepath) and os.path.getsize(code_filepath) > 0:
                    created_files.append(code_filename)
                else:
                    logger.warning(f"Архивация родительского каталога завершилась с кодом {res.returncode}, пробуем локальный app")
                    cmd_fallback = f"tar {exclude_str} -czf '{code_filepath}' -C '{PROJECT_ROOT}' ."
                    res_fb = subprocess.run(cmd_fallback, shell=True, capture_output=True, text=True)
                    if res_fb.returncode == 0 and os.path.exists(code_filepath):
                        created_files.append(code_filename)

            # Обновление статуса в БД
            with Session(engine) as session:
                st = self.get_or_create_settings(session)
                st.last_backup_at = datetime.now(timezone.utc).replace(tzinfo=None)
                st.last_backup_status = "success"
                st.last_backup_message = f"Созданы: {', '.join(created_files)}"
                session.add(st)
                session.commit()

            # Применение политики ротации (автоудаление)
            self.apply_retention_policy()

            return {
                "status": "success",
                "message": f"Бэкап успешно создан: {', '.join(created_files)}",
                "files": created_files
            }

        except Exception as e:
            logger.error(f"Сбой создания бэкапа: {e}", exc_info=True)
            with Session(engine) as session:
                st = self.get_or_create_settings(session)
                st.last_backup_status = "error"
                st.last_backup_message = str(e)
                session.add(st)
                session.commit()
            return {"status": "error", "message": f"Ошибка создания бэкапа: {str(e)}"}

    def delete_backup(self, filename: str) -> Dict[str, Any]:
        """Удаление конкретного файла бэкапа с валидацией имени"""
        # Защита от path traversal
        clean_name = os.path.basename(filename)
        target = os.path.join(self.backup_dir, clean_name)

        if not os.path.exists(target):
            return {"status": "error", "message": "Файл не найден"}

        try:
            os.remove(target)
            return {"status": "success", "message": f"Бэкап {clean_name} удален"}
        except Exception as e:
            logger.error(f"Ошибка удаления бэкапа {clean_name}: {e}")
            return {"status": "error", "message": str(e)}

    def apply_retention_policy(self) -> Dict[str, Any]:
        """
        Автоматическое удаление старых бэкапов:
        1. Удаление файлов старше retention_days
        2. Ограничение по max_backup_count
        3. Защита при нехватке места (min_disk_free_gb)
        """
        deleted_count = 0
        try:
            with Session(engine) as session:
                settings_obj = self.get_or_create_settings(session)
                retention_days = settings_obj.retention_days
                max_count = settings_obj.max_backup_count
                min_free_gb = settings_obj.min_disk_free_gb

            backups = self.list_backups()
            now = datetime.now()

            # 1. Удаление по возрасту
            cutoff_date = now - timedelta(days=retention_days)
            remaining = []
            for b in backups:
                b_date = datetime.fromisoformat(b["created_at"])
                if b_date < cutoff_date:
                    fpath = os.path.join(self.backup_dir, b["filename"])
                    if os.path.exists(fpath):
                        os.remove(fpath)
                        deleted_count += 1
                        logger.info(f"Ротация: удален устаревший бэкап {b['filename']} ({b['created_at']})")
                else:
                    remaining.append(b)

            # 2. Ограничение по максимальному количеству
            if len(remaining) > max_count:
                # Удаляем самые старые сверх лимита
                to_delete = remaining[max_count:]
                for b in to_delete:
                    fpath = os.path.join(self.backup_dir, b["filename"])
                    if os.path.exists(fpath):
                        os.remove(fpath)
                        deleted_count += 1
                        logger.info(f"Ротация: удален бэкап {b['filename']} сверх лимита {max_count}")

            # 3. Проверка минимального места на диске
            disk = self.get_disk_info()
            if disk["free_gb"] < min_free_gb:
                logger.warning(f"Критический уровень диска: свободно {disk['free_gb']} ГБ < {min_free_gb} ГБ")
                current = self.list_backups()
                # Удаляем от самых старых к новым, пока не освободится место
                for b in reversed(current):
                    fpath = os.path.join(self.backup_dir, b["filename"])
                    if os.path.exists(fpath):
                        os.remove(fpath)
                        deleted_count += 1
                        logger.info(f"Экстренная очистка: удален бэкап {b['filename']}")
                        disk = self.get_disk_info()
                        if disk["free_gb"] >= min_free_gb:
                            break

            return {"status": "success", "deleted_count": deleted_count}

        except Exception as e:
            logger.error(f"Ошибка выполнения ротации бэкапов: {e}")
            return {"status": "error", "message": str(e)}

    def get_or_create_settings(self, session: Session) -> BackupSettings:
        """Получить текущие настройки бэкапов или создать дефолтные"""
        st = session.exec(select(BackupSettings)).first()
        if not st:
            st = BackupSettings(
                auto_backup_enabled=True,
                schedule_interval="daily_night",
                backup_type="db_and_code",
                retention_days=14,
                max_backup_count=10,
                min_disk_free_gb=3.0,
                notify_admin_panel=True
            )
            session.add(st)
            session.commit()
            session.refresh(st)
        return st

    # ------------------ Управление ИИ-протоколами и документацией ------------------

    def get_ai_instructions(self, session: Session) -> List[Dict[str, Any]]:
        """Получить список системных регламентов и промптов для ИИ"""
        instructions = session.exec(select(AiPromptInstruction).order_by(AiPromptInstruction.priority)).all()
        if not instructions:
            # Инициализация дефолтных протоколов
            default_protocols = [
                {
                    "title": "Главный системный протокол работы ИИ",
                    "code": "system_protocol",
                    "priority": 1,
                    "content": (
                        "# Системный протокол работы ИИ-ассистента\n\n"
                        "Перед началом выполнения любой задачи строго читай документацию по проекту: system_faq.md, sql_faq.md, sitenav.md.\n\n"
                        "1. Базовые принципы:\n"
                        "- Язык: Строго русский язык для всех ответов, рассуждений, планов и комментариев в коде.\n"
                        "- Среда: Рабочий проект находится на VPS в папке foodzuka (ssh vezuroll).\n"
                        "- Запрет слепого затирания: ЗАПРЕЩЕНО полностью перезаписывать ключевые файлы (main.py, __init__.py, NavItems.vue, routes.js). Изменения вносятся точечно и деликатно!\n"
                        "- Перед загрузкой на VPS: обязательно сверять файлы на VPS через `diff -u` или `sha256sum`. Если на сервере код свежее — объединять (merge), а не перезаписывать.\n"
                        "- После деплоя: проверять `py_compile`, перезапускать контейнеры и тестировать live-эндпоинты.\n"
                    )
                },
                {
                    "title": "Чеклист проверки перед выгрузкой на VPS (Pre-flight Guard)",
                    "code": "preflight_checklist",
                    "priority": 2,
                    "content": (
                        "# Чеклист безопасной выгрузки на сервер\n\n"
                        "1. [ ] Проверить diff локального файла с версией на VPS (`diff -u`).\n"
                        "2. [ ] Убедиться, что не затираются подключенные роутеры и пункты меню.\n"
                        "3. [ ] Проверить кодировку (строго UTF-8 без BOM).\n"
                        "4. [ ] Проверить синтаксис Python (`python -m py_compile`).\n"
                        "5. [ ] Выгрузить файл на VPS и сверить контрольную сумму SHA-256.\n"
                        "6. [ ] Перезапустить целевой контейнер (`docker restart foodtech-backend`).\n"
                        "7. [ ] Проверить ответ HTTP-эндпоинта (`curl -k https://vezuroll.ru/...`).\n"
                    )
                },
                {
                    "title": "Правила роутинга и целостности меню админки",
                    "code": "routes_and_navigation_rules",
                    "priority": 3,
                    "content": (
                        "# Правила меню и маршрутизации админки\n\n"
                        "- Все маршруты должны быть описаны в `admin/resources/js/plugins/router/routes.js`.\n"
                        "- Меню в `NavItems.vue` строится с учетом прав `hasPermission(...)`.\n"
                        "- Каждый модуль бэкенда регистрируется в `backend/app/api/__init__.py` и `backend/main.py`.\n"
                        "- Запрещено удалять существующие пункты меню без явной команды пользователя.\n"
                    )
                }
            ]
            for p in default_protocols:
                inst = AiPromptInstruction(
                    title=p["title"],
                    code=p["code"],
                    priority=p["priority"],
                    content=p["content"],
                    is_active=True
                )
                session.add(inst)
            session.commit()
            instructions = session.exec(select(AiPromptInstruction).order_by(AiPromptInstruction.priority)).all()

        return [inst.dict() for inst in instructions]

    def save_ai_instruction(self, session: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        """Сохранение или обновление ИИ-инструкции"""
        code = data.get("code")
        inst = session.exec(select(AiPromptInstruction).where(AiPromptInstruction.code == code)).first()
        if not inst:
            inst = AiPromptInstruction(
                title=data.get("title", "Новый регламент"),
                code=code,
                content=data.get("content", ""),
                is_active=data.get("is_active", True),
                priority=data.get("priority", 10)
            )
        else:
            inst.title = data.get("title", inst.title)
            inst.content = data.get("content", inst.content)
            inst.is_active = data.get("is_active", inst.is_active)
            inst.priority = data.get("priority", inst.priority)
            inst.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        session.add(inst)
        session.commit()
        session.refresh(inst)
        return inst.dict()

    def get_document(self, doc_name: str) -> Dict[str, Any]:
        """Получить содержимое markdown-документа (system_faq, sitenav, sql_faq)"""
        # Поиск файла документации в возможных путях
        doc_filename = f"{doc_name}.md" if not doc_name.endswith(".md") else doc_name
        search_paths = [
            os.path.join(PROJECT_ROOT, "..", "Service_info", doc_filename),
            os.path.join(PROJECT_ROOT, "Service_info", doc_filename),
            f"/root/foodzuka/Service_info/{doc_filename}",
            os.path.join(DOCS_DIR, doc_filename)
        ]

        found_path = None
        for p in search_paths:
            if os.path.exists(p):
                found_path = p
                break

        if not found_path:
            return {"status": "error", "message": f"Документ {doc_filename} не найден", "content": ""}

        try:
            with open(found_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "status": "success",
                "doc_name": doc_name,
                "path": found_path,
                "content": content
            }
        except Exception as e:
            logger.error(f"Ошибка чтения {doc_filename}: {e}")
            return {"status": "error", "message": str(e), "content": ""}

    def save_document(self, doc_name: str, content: str) -> Dict[str, Any]:
        """Сохранить обновленное содержимое документа"""
        doc_filename = f"{doc_name}.md" if not doc_name.endswith(".md") else doc_name
        search_paths = [
            os.path.join(PROJECT_ROOT, "..", "Service_info", doc_filename),
            os.path.join(PROJECT_ROOT, "Service_info", doc_filename),
            f"/root/foodzuka/Service_info/{doc_filename}",
            os.path.join(DOCS_DIR, doc_filename)
        ]

        target_path = None
        for p in search_paths:
            if os.path.exists(p):
                target_path = p
                break

        if not target_path:
            target_path = search_paths[0]

        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "message": f"Документ {doc_filename} успешно сохранен"}
        except Exception as e:
            logger.error(f"Ошибка сохранения {doc_filename}: {e}")
            return {"status": "error", "message": str(e)}


backup_service = BackupService()
