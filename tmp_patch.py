import sys
import os

# Source is the UTF-8 converted file
src_path = r'backend\app\services\iiko_sync_service_utf8.py'
# Target is the original file
dst_path = r'backend\app\services\iiko_sync_service.py'

if not os.path.exists(src_path):
    print(f"File not found: {src_path}")
    sys.exit(1)

with open(src_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_content = """        expected_time = parse_time(o_data.get("completeBefore"))
        actual_time = parse_time(o_data.get("actualTime"))
        creation_time = parse_time(o_data.get("creationTime"))
        
        # Расчет опоздания
        delay_minutes = 0
        if expected_time and actual_time and actual_time > expected_time:
            delta = actual_time - expected_time
            delay_minutes = int(delta.total_seconds() // 60)

        # Флаг "на время"
        is_on_time = False
        if creation_time and expected_time:
            # Если время доставки больше чем через 2 часа после создания, считаем что "на время"
            if (expected_time - creation_time).total_seconds() > 7200:
                is_on_time = True

        # Курьер
        courier_name = None
        courier_info = o_data.get("courierInfo")
        if isinstance(courier_info, dict):
            courier = courier_info.get("courier")
            if isinstance(courier, dict):
                courier_name = courier.get("name")

        # Администратор / Кассир
        admin_name = None
        conveyor_details = o_data.get("conveyorDetails")
        if isinstance(conveyor_details, dict):
            cashier = conveyor_details.get("cashier")
            if isinstance(cashier, dict):
                admin_name = cashier.get("name")

        # Адрес и зона доставки
        deliv_point = o_data.get("deliveryPoint", {})
        delivery_address = deliv_point.get("address", {}).get("street", {}).get("name", "")
        house = deliv_point.get("address", {}).get("house", "")
        flat = deliv_point.get("address", {}).get("flat", "")
        if house:
            delivery_address += f", д. {house}"
        if flat:
            delivery_address += f", кв. {flat}"
        
        if not delivery_address:
            delivery_address = o_data.get("address") or o_data.get("deliveryAddress")
            
        delivery_zone = deliv_point.get("externalCartographyId") or deliv_point.get("zone", {}).get("name")

        # Финансы (Суммы и скидки)
        sum_total = Decimal(str(o_data.get("sum", 0)))
        total_with_discount = Decimal(str(o_data.get("totalSum", sum_total)))
        total_discount = sum_total - total_with_discount
        payment_method = None
        payments = o_data.get("payments", [])
        if payments and isinstance(payments, list):
            payment_method = payments[0].get("paymentType", {}).get("name")
            
        order_type = o_data.get("orderType", {}).get("name")
        
        # Бонусы
        bonus_spent = Decimal("0")
        bonus_accrued = Decimal("0")
        if "customer" in o_data:
            cust = o_data["customer"]
            # В iiko API бонусы часто идут в payments как тип "Loyalty"
            for p in payments:
                if p.get("paymentType", {}).get("kind") == "Loyalty":
                    bonus_spent += Decimal(str(p.get("sum", 0)))

        # Поиск customer_id
        customer = session.exec(select(Customer).where(Customer.phone == phone)).first() if phone else None
        if not customer and phone:
            customer = Customer(phone=phone, name=name)
            session.add(customer)
            session.commit()
            session.refresh(customer)

        if not order:
            # Пытаемся найти branch
            terminal_group_id = iiko_order_data.get("terminalGroupId") or o_data.get("terminalGroupId")
            branch_id = None
            if terminal_group_id:
                branch = session.exec(select(Branch).where(Branch.iiko_terminal_id == terminal_group_id)).first()
                if branch:
                    branch_id = branch.id

            order = Order(
                iiko_order_id=order_id_iiko,
                customer_name=name,
                customer_phone=phone,
                customer_id=customer.id if customer else None,
                branch_id=branch_id or 1,
                total_amount=sum_total,
                status=mapped_status,
                order_items_details=o_data.get("items", []),
                discounts_details=o_data.get("discountsInfo", {}),
                customer_info_details=customer_info,
                iiko_creation_time=creation_time,
                expected_time=expected_time,
                actual_time=actual_time,
                delay_minutes=delay_minutes,
                is_on_time=is_on_time,
                admin_name=admin_name,
                order_type=order_type,
                payment_method=payment_method,
                total_with_discount=total_with_discount,
                total_discount=total_discount,
                bonus_spent=bonus_spent,
                bonus_accrued=bonus_accrued,
                courier_name=courier_name,
                delivery_address=delivery_address,
                delivery_zone=delivery_zone
            )
            session.add(order)
            session.flush() # Получаем ID заказа
        else:
            old_status = order.status
            # Обновляем существующий заказ
            order.status = mapped_status
            order.iiko_creation_time = creation_time or order.iiko_creation_time
            order.expected_time = expected_time or order.expected_time
            order.actual_time = actual_time or order.actual_time
            order.delay_minutes = delay_minutes if delay_minutes > 0 else order.delay_minutes
            order.is_on_time = is_on_time
            order.admin_name = admin_name or order.admin_name
            order.payment_method = payment_method or order.payment_method
            order.order_type = order_type or order.order_type
            order.total_amount = sum_total
            order.total_with_discount = total_with_discount
            order.total_discount = total_discount
            order.bonus_spent = bonus_spent if bonus_spent > 0 else order.bonus_spent
            order.bonus_accrued = bonus_accrued if bonus_accrued > 0 else order.bonus_accrued
            order.courier_name = courier_name or order.courier_name
            order.delivery_address = delivery_address or order.delivery_address
            order.delivery_zone = delivery_zone or order.delivery_zone
            order.order_items_details = o_data.get("items", []) or order.order_items_details
            order.discounts_details = o_data.get("discountsInfo", {}) or order.discounts_details
            
            flag_modified(order, "order_items_details")
            flag_modified(order, "discounts_details")
            session.add(order)
        
        # Синхронизация OrderItems
        items_data = o_data.get("items", [])
        if isinstance(items_data, list):
            # Удаляем старые позиции для обновления
            existing_items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
            for ei in existing_items:
                session.delete(ei)
            
            for item_data in items_data:
                product_id_iiko = item_data.get("productId")
                product_name = item_data.get("name", "Unknown Product")
                quantity = int(item_data.get("amount", 1))
                price = Decimal(str(item_data.get("price", 0)))
                total = Decimal(str(item_data.get("sum", price * quantity)))
                
                # Пытаемся найти локальный продукт по iiko_id
                product = None
                if product_id_iiko:
                    product = session.exec(select(Product).where(Product.iiko_id == product_id_iiko)).first()
                
                new_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id if product else 1,
                    product_name=product_name,
                    quantity=quantity,
                    price=price,
                    total=total
                )
                session.add(new_item)
"""

# Find Start and End lines based on context
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'expected_time = parse_time(o_data.get("completeBefore"))' in line:
        start_idx = i
        # Check if it's the right place (line 402 approx)
        if i < 300: # Could be another parse_time
             continue
        break

if start_idx != -1:
    for i in range(start_idx, len(lines)):
        if 'if old_status != mapped_status and order.customer_phone:' in lines[i]:
            # We want to keep this line, so end_idx is i
            end_idx = i
            break

if start_idx != -1 and end_idx != -1:
    # Remove markers correctly
    # The duplicated logic at end should also be removed.
    # We'll just replace everything from start_idx to end_idx-1
    # BUT wait! I saw duplicated logic at 519+ which we want to remove.
    # The marker 'if old_status != mapped_status and order.customer_phone:' appears at line 537.
    # Let's find the FIRST occurrence after start_idx.
    lines[start_idx:end_idx] = [new_content + "\n"]
    with open(dst_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Successfully patched iiko_sync_service.py")
else:
    print(f"Failed to find markers: start={start_idx}, end={end_idx}")
    sys.exit(1)
