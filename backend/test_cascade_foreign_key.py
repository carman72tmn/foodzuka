import sys
from sqlmodel import Session, select
from app.core.database import engine
from app.models.mailing_cascade import MailingCascade, MailingCascadeStep
from app.models.message_log import CustomerMessageLog

def run_test():
    with Session(engine) as db:
        try:
            print("1. Создаем тестовый каскад...")
            cascade = MailingCascade(
                name="Временный тест FK",
                trigger_event="order_delivered",
                is_active=True,
                order_type="delivery",
                is_system=False
            )
            db.add(cascade)
            db.commit()
            db.refresh(cascade)
            cascade_id = cascade.id
            print(f"Каскад создан, ID: {cascade_id}")

            print("2. Создаем шаг каскада...")
            step = MailingCascadeStep(
                cascade_id=cascade_id,
                channel="vk",
                priority=0,
                delay_minutes=0,
                condition="always",
                template="Тестовый шаблон"
            )
            db.add(step)
            db.commit()
            db.refresh(step)
            step_id = step.id
            print(f"Шаг каскада создан, ID: {step_id}")

            print("3. Создаем лог сообщения, привязанный к шагу...")
            log = CustomerMessageLog(
                cascade_step_id=step_id,
                channel="vk",
                recipient_address="123456",
                text="Тестовое сообщение",
                status="sent"
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            log_id = log.id
            print(f"Лог сообщения создан, ID: {log_id}")

            print("4. Симулируем обновление каскада (удаление старого шага)...")
            db.delete(step)
            db.commit()
            print("Старый шаг успешно удален без ForeignKeyViolation!")

            db.refresh(log)
            print(f"Значение cascade_step_id в логе: {log.cascade_step_id}")
            assert log.cascade_step_id is None, "Ошибка: ссылка не обнулилась!"
            print("Успех: ссылка в логе стала NULL!")

            print("5. Чистим тестовые данные...")
            db.delete(cascade)
            db.delete(log)
            db.commit()
            print("Все тестовые данные удалены успешно!")
            print("--- ТЕСТ ПРОЙДЕН УСПЕШНО ---")
            
        except Exception as e:
            print(f"Ошибка во время теста: {e}")
            db.rollback()
            try:
                c = db.exec(select(MailingCascade).where(MailingCascade.name == "Временный тест FK")).first()
                if c:
                    db.delete(c)
                db.commit()
            except:
                pass
            sys.exit(1)

if __name__ == "__main__":
    run_test()
