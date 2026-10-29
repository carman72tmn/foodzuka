"""
Периодические задачи Celery для Т-Банк T-API
"""
import logging
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
import httpx
import tempfile
import os
import json
import asyncio

from app.core.celery_app import celery_app
from app.core.database import engine
from app.models.tbank_settings import TBankSettings, TBankAccountStatement
from app.models.payment_type import PaymentType
from app.core.tbank_utils import get_terminal_display_name

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.tbank_tasks.sync_tbank_statements_task")
def sync_tbank_statements_task():
    """
    Периодическая задача Celery для автоматической синхронизации банковских выписок за последние 3 дня
    """
    logger.info("Starting automatic T-Bank statement synchronization task")
    
    with Session(engine) as db:
        settings_rec = db.exec(select(TBankSettings)).first()
        if not settings_rec or not settings_rec.is_active or not settings_rec.token:
            logger.info("T-Bank integration not active or token missing, skipping task")
            return "Skipped: integration not active"
            
        # Запрашиваем расчетные счета компании
        from app.api.tbank import get_tbank_accounts
        try:
            accounts = get_tbank_accounts(db)
        except Exception as e:
            logger.error(f"Failed to fetch accounts during auto-sync: {str(e)}")
            return f"Error: failed to fetch accounts - {str(e)}"
            
        if not accounts or isinstance(accounts, list) and len(accounts) == 0:
            logger.warning("No active bank accounts found for T-Bank")
            return "No accounts found"
            
        # Устанавливаем период сверки: последние 3 дня
        from_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        till_date = datetime.now().strftime("%Y-%m-%d")
        
        # Схемы для импорта выписок
        from app.api.tbank import TBankSyncStatementRequestSchema, sync_tbank_statement
        
        results = []
        for acc in accounts:
            acc_num = acc.get("accountNumber")
            if not acc_num:
                continue
                
            logger.info(f"Syncing T-Bank statement for account: {acc_num} from {from_date} to {till_date}")
            try:
                # Симулируем/вызываем сверку выписки для этого счета
                req_data = TBankSyncStatementRequestSchema(
                    account_number=acc_num,
                    from_date=from_date,
                    till_date=till_date
                )
                
                # Запускаем сверку (она сама сопоставляет платежи и делает коммит в БД)
                res = sync_tbank_statement(req_data, db, current_user=None)
                results.append({
                    "account": acc_num,
                    "processed": res.get("processed_operations", 0),
                    "added": res.get("new_operations_added", 0),
                    "matched": res.get("orders_automatically_matched", 0)
                })
            except Exception as e:
                logger.error(f"Error during auto-sync of account {acc_num}: {str(e)}")
                results.append({"account": acc_num, "error": str(e)})
                
        return f"Completed auto-sync. Results: {results}"

@celery_app.task(name="app.tasks.tbank_tasks.sync_tbank_terminals_task")
def sync_tbank_terminals_task():
    """
    Периодическая задача Celery для опроса оплат по POS-терминалам Т-Банка
    Опрашивает транзакции за последние 2 часа для обеспечения real-time LIVE-монитора
    """
    logger.info("Starting T-Bank POS terminals synchronization task for LIVE monitor")
    
    # Предотвращение одновременного запуска (распределенная блокировка в Redis на 45 секунд)
    try:
        import redis
        from app.core.config import settings as app_settings
        r = redis.from_url(app_settings.REDIS_URL or "redis://redis:6379/0")
        lock_acquired = r.set("tbank_terminal_sync_lock", "locked", ex=45, nx=True)
        if not lock_acquired:
            logger.info("Terminal sync task is already running in another worker, skipping to prevent concurrent API hits")
            return "Skipped: lock already acquired"
    except Exception as lock_err:
        logger.warning(f"Failed to acquire Redis lock for terminal sync: {lock_err}. Proceeding without lock...")

    with Session(engine) as db:
        settings = db.exec(select(TBankSettings)).first()
        if not settings or not settings.is_active or not settings.token:
            logger.info("T-Bank integration not active or token missing, skipping terminal sync task")
            return "Skipped: integration not active"
            
        # Загружаем выбранные терминалы
        terminals = []
        if settings.selected_terminals:
            try:
                parsed = json.loads(settings.selected_terminals)
                if isinstance(parsed, list):
                    terminals = [str(t).strip() for t in parsed if t]
                elif isinstance(parsed, str):
                    terminals = [parsed.strip()]
            except Exception as e:
                logger.error(f"Failed to parse selected_terminals JSON: {e}")
                
        if not terminals and settings.terminal_key:
            terminals = [str(settings.terminal_key).strip()]
            
        # Очищаем список от некорректных значений и булевых констант
        terminals = [t for t in terminals if t and t.lower() not in ["true", "false", "none", "null"]]
        
        # Гарантируем опрос выбранных в настройках терминалов (если заданы)
        if settings.terminal_pickup and settings.terminal_pickup not in terminals:
            terminals.append(str(settings.terminal_pickup).strip())
        if settings.terminal_delivery and settings.terminal_delivery not in terminals:
            terminals.append(str(settings.terminal_delivery).strip())
            
        if not terminals:
            logger.warning("No POS terminals configured for synchronization")
            return "Skipped: no terminals configured"
            
        # TLS Сертификат
        cert_file_path = None
        client = httpx.Client(timeout=10.0, verify=False)
        if settings.certificate_content and settings.certificate_content.strip():
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w", encoding="utf-8") as temp_cert:
                    temp_cert.write(settings.certificate_content.strip())
                    cert_file_path = temp_cert.name
                client.cert = cert_file_path
                logger.info("Using mTLS client certificate for terminal sync")
            except Exception as e:
                logger.error(f"Failed to create temporary cert file: {e}")
                
        headers = {
            "Authorization": f"Bearer {settings.token}",
            "Content-Type": "application/json"
        }
        
        # Динамический опрос списка терминалов из API Т-Банка
        api_terminal_keys = set()
        try:
            term_api_url = "https://business.tbank.ru/openapi/api/v1/tacq/terminals"
            term_resp = client.get(term_api_url, headers=headers, params={"page": 0, "size": 50})
            if term_resp.status_code == 200:
                t_json = term_resp.json()
                active_terms = t_json.get("terminals", []) if isinstance(t_json, dict) else t_json
                if isinstance(active_terms, list):
                    for at in active_terms:
                        if isinstance(at, dict):
                            t_k = str(at.get("key") or at.get("terminalKey") or "").strip()
                            if t_k and t_k.lower() not in ["true", "false", "none", "null"]:
                                api_terminal_keys.add(t_k)
                                if t_k not in terminals:
                                    terminals.append(t_k)
        except Exception as t_disc_err:
            logger.warning(f"Не удалось выгрузить терминалы из API Т-Банка: {t_disc_err}")

        # Фильтруем терминалы: если из API получен список активных, исключаем те, которых в нем гарантированно нет
        if api_terminal_keys:
            # Оставляем только терминалы, присутствующие в API
            valid_terminals = [t for t in terminals if t in api_terminal_keys]
            if valid_terminals:
                terminals = valid_terminals
        
        # Проверяем кэш невалидных терминалов в Redis
        try:
            terminals = [t for t in terminals if not r.get(f"tbank_invalid_term:{t}")]
        except Exception:
            pass
        
        # Задаем временной период: последние 12 часов (в UTC)
        now_utc = datetime.now(timezone.utc)
        from_dt = now_utc - timedelta(hours=12)
        
        from_str = from_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        till_str = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        params = {
            "from": from_str,
            "till": till_str,
            "limit": 100
        }
        
        results = []
        
        try:
            for i, term_key in enumerate(terminals):
                if not term_key:
                    continue
                    
                # Задержка 2 секунды во избежание 429 Too Many Requests от API Т-Банка
                if i > 0:
                    import time
                    time.sleep(2.0)
                    
                url = f"https://business.tbank.ru/openapi/api/v1/tacq/operations/terminal/{term_key}"
                logger.info(f"Requesting operations for terminal {term_key} from {from_str} to {till_str}")
                
                try:
                    response = client.get(url, headers=headers, params=params)
                    if response.status_code != 200:
                        logger.warning(f"T-Bank API returned code {response.status_code} for terminal {term_key}: {response.text[:200]}")
                        if response.status_code == 422:
                            try:
                                r.set(f"tbank_invalid_term:{term_key}", "1", ex=86400)
                            except Exception:
                                pass
                        results.append({"terminal": term_key, "error": f"HTTP status {response.status_code}"})
                        continue
                        
                    api_data = response.json()
                    operations = []
                    if isinstance(api_data, dict):
                        operations = api_data.get("operations", [])
                    elif isinstance(api_data, list):
                        operations = api_data
                        
                    added_count = 0
                    matched_count = 0
                    
                    for op in operations:
                        if not isinstance(op, dict):
                            continue
                            
                        # Исключаем явные возвраты и отмены (Т-Банк для успешных оплат возвращает Debit, Other, Payment и др.)
                        op_type = str(op.get("type") or op.get("operationType") or "").strip()
                        if op_type.lower() in ["refund", "reversal", "credit", "cancel", "возврат"]:
                            continue
                            
                        op_status = str(op.get("status") or "").strip().upper()
                        # Если статус явно передан, пропускаем неуспешные
                        if op_status and op_status not in ["CONFIRMED", "COMPLETED", "PAID", "OK", "SUCCESS", "AUTHORIZED"]:
                            continue
                            
                        # Сумма операции (в копейках)
                        try:
                            amount_rub = float(op.get("amount", 0)) / 100.0
                        except Exception:
                            continue
                            
                        if amount_rub <= 0:
                            continue
                            
                        # Идентификатор транзакции (RRN или внутренний ID)
                        rrn = op.get("rrn")
                        op_id = op.get("id") or op.get("transactionId") or op.get("paymentId")
                        unique_ref = rrn or op_id
                        if not unique_ref:
                            continue
                            
                        # Дата и время транзакции
                        tx_date_str = op.get("transactionDate") or op.get("date") or op.get("chargeDate")
                        try:
                            tx_date = datetime.fromisoformat(tx_date_str.replace("Z", "+00:00"))
                        except Exception:
                            tx_date = datetime.now()
                            
                        # Проверяем, есть ли уже такая операция в tbank_statements
                        existing = db.exec(
                            select(TBankAccountStatement).where(
                                TBankAccountStatement.payer_account == unique_ref,
                                TBankAccountStatement.amount == amount_rub
                            )
                        ).first()
                        if not existing:
                            term_title = get_terminal_display_name(term_key, settings=settings)
                            
                            matched_order_id = None
                            
                            # Попытка автоматического сопоставления с заказом iiko
                            from app.api.tbank_webhooks import find_best_matching_order
                            matched_order = find_best_matching_order(
                                db=db,
                                amount=amount_rub,
                                tx_date=tx_date,
                                terminal_key=term_key,
                                purpose=f"Оплата через {term_title}"
                            )
                                            
                            if matched_order:
                                matched_order_id = matched_order.id
                                matched_count += 1
                                    
                            # Сохраняем транзакцию в БД
                            db_op = TBankAccountStatement(
                                account_number=term_key,
                                charge_date=tx_date,
                                amount=amount_rub,
                                payment_purpose=f"Оплата через {term_title}",
                                payer_name=op.get("cardNumber") or "Физическое лицо (Эквайринг)",
                                payer_account=unique_ref,
                                payer_bank_bic="",
                                payer_inn="",
                                matched_order_id=matched_order_id
                            )
                            db.add(db_op)
                            db.commit()
                            added_count += 1
                            
                            # Отправка real-time WebSocket уведомления
                            try:
                                from app.api.chat import manager
                                ws_payload = {
                                    "type": "new_bank_payment",
                                    "amount": amount_rub,
                                    "method": "Эквайринг",
                                    "terminal": term_title,
                                    "customer": op.get("cardNumber") or "Клиент (Карта)",
                                    "order_id": matched_order_id,
                                    "rrn": unique_ref,
                                    "timestamp": int(datetime.now().timestamp() * 1000)
                                }
                                # Публикация в Redis Pub/Sub (мгновенно уходит во все открытые вкладки)
                                manager.broadcast_sync(ws_payload)
                                
                                # Запуск Push-уведомления
                                try:
                                    loop = asyncio.get_event_loop()
                                except RuntimeError:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    
                                from app.services.iiko_sync_service import iiko_sync_service
                                push_coro = iiko_sync_service.send_admin_push_notification(
                                    session=db,
                                    title="Поступление оплаты!",
                                    body=f"Сумма: {amount_rub:.2f} ₽ ({term_title}) | Карта {op.get('cardNumber') or '---'}",
                                    url="/admin/bank/tbank-payments",
                                    event_type="new_payment",
                                    tag=f"payment-pos-{db_op.id or unique_ref}"
                                )
                                if loop.is_running():
                                    loop.create_task(push_coro)
                                else:
                                    loop.run_until_complete(push_coro)
                                    
                                logger.info(f"WebSocket and Push notifications sent for terminal transaction: {amount_rub} RUB")
                            except Exception as ws_err:
                                logger.error(f"Failed to send websocket payment notification: {ws_err}")
                                
                    results.append({
                        "terminal": term_key,
                        "processed": len(operations),
                        "added": added_count,
                        "matched": matched_count
                    })
                    
                except Exception as term_err:
                    logger.error(f"Error syncing terminal {term_key}: {term_err}")
                    results.append({"terminal": term_key, "error": str(term_err)})
                    
        finally:
            client.close()
            # Удаляем временный файл сертификата
            if cert_file_path and os.path.exists(cert_file_path):
                try:
                    os.unlink(cert_file_path)
                except Exception as e:
                    logger.error(f"Failed to delete temp cert file: {e}")
                    
        # LIVE-синхронизация банковских выписок по расчетным счетам (за сегодня и вчера)
        # Это обеспечивает live-режим для платежей СБП/QR, поступающих на расчетный счет
        try:
            from app.api.tbank import get_tbank_accounts, TBankSyncStatementRequestSchema, sync_tbank_statement
            accounts = get_tbank_accounts(db)
            if accounts and not isinstance(accounts, dict): # проверяем, что вернулся список счетов
                from_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                till_date = datetime.now().strftime("%Y-%m-%d")
                
                for acc in accounts:
                    if not isinstance(acc, dict):
                        continue
                    acc_num = acc.get("accountNumber")
                    if not acc_num:
                        continue
                    
                    req_data = TBankSyncStatementRequestSchema(
                        account_number=acc_num,
                        from_date=from_date,
                        till_date=till_date
                    )
                    # Вызываем синхронизацию выписки
                    sync_tbank_statement(req_data, db, current_user=None)
                    logger.info(f"LIVE statement sync completed for account {acc_num} from {from_date} to {till_date}")
        except Exception as stmt_err:
            logger.error(f"Failed to run LIVE statement sync during terminal task: {stmt_err}")
                    
        return f"Completed terminals sync. Results: {results}"

