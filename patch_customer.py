
import os

path = r'c:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\services\iiko_sync_service.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
found = False
for line in lines:
    new_lines.append(line)
    if 'phone = clean(o_data.get("phone")' in line and not found:
        found = True
        indent = "            "
        new_lines.append("\n")
        new_lines.append(f"{indent}# Внедрение логики авто-создания клиента\n")
        new_lines.append(f"{indent}if phone:\n")
        new_lines.append(f"{indent}    try:\n")
        new_lines.append(f"{indent}        customer = session.exec(select(Customer).where(Customer.phone == phone)).first()\n")
        new_lines.append(f"{indent}        current_order_time = iiko_creation_time or datetime.now(timezone.utc).replace(tzinfo=None)\n")
        new_lines.append(f"{indent}        order_info = f\"Заказ #{{ext_num or 'б/н'}} от {{current_order_time.strftime('%d.%m.%Y %H:%M')}}\"\n")
        new_lines.append(f"{indent}        total_val = o_data.get(\"sum\") or 0\n")
        new_lines.append(f"{indent}        if total_val: order_info += f\" на сумму {{total_val}} руб.\"\n")
        new_lines.append(f"{indent}        if not customer:\n")
        new_lines.append(f"{indent}            customer = Customer(\n")
        new_lines.append(f"{indent}                phone=phone,\n")
        new_lines.append(f"{indent}                name=c_first or \"Гость\",\n")
        new_lines.append(f"{indent}                surname=c_last,\n")
        new_lines.append(f"{indent}                last_order_date=current_order_time,\n")
        new_lines.append(f"{indent}                notes=f\"Создан автоматически. {{order_info}}\",\n")
        new_lines.append(f"{indent}                updated_at=datetime.now(timezone.utc).replace(tzinfo=None)\n")
        new_lines.append(f"{indent}            )\n")
        new_lines.append(f"{indent}            session.add(customer)\n")
        new_lines.append(f"{indent}            logger.info(f\"Auto-created new customer: {{phone}} ({{full_customer_name}})\")\n")
        new_lines.append(f"{indent}        else:\n")
        new_lines.append(f"{indent}            if not customer.name and c_first: customer.name = c_first\n")
        new_lines.append(f"{indent}            if not customer.surname and c_last: customer.surname = c_last\n")
        new_lines.append(f"{indent}            if not customer.last_order_date or current_order_time > customer.last_order_date: customer.last_order_date = current_order_time\n")
        new_lines.append(f"{indent}            new_note = f\"\\n{{order_info}}\"\n")
        new_lines.append(f"{indent}            if not customer.notes: customer.notes = order_info\n")
        new_lines.append(f"{indent}            elif order_info not in customer.notes:\n")
        new_lines.append(f"{indent}                customer.notes = (customer.notes[-500:] + new_note) if len(customer.notes) > 500 else (customer.notes + new_note)\n")
        new_lines.append(f"{indent}            customer.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)\n")
        new_lines.append(f"{indent}            session.add(customer)\n")
        new_lines.append(f"{indent}        session.flush()\n")
        new_lines.append(f"{indent}        from app.tasks.customer_tasks import sync_single_customer_task\n")
        new_lines.append(f"{indent}        try: sync_single_customer_task.delay(phone)\n")
        new_lines.append(f"{indent}        except Exception as celery_err: logger.warning(f\"Failed to start background customer sync task: {{celery_err}}\")\n")
        new_lines.append(f"{indent}    except Exception as ce: logger.error(f\"Error in auto-creating customer for order {{order_id_iiko}}: {{ce}}\")\n")

if found:
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("SUCCESS")
else:
    print("FAILED")
