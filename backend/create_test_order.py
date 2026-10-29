from app.core.database import engine
from sqlmodel import Session, select
from app.models.order import Order, OrderItem, OrderStatus
from app.models.company import Branch
from datetime import datetime, timedelta, timezone

session = Session(engine)

# Находим первый филиал
branch = session.exec(select(Branch)).first()
if not branch:
    print("No branches found in DB. Please seed the DB first.")
    exit(1)

# Создаем тестовый заказ
test_order = Order(
    telegram_user_id=12345678,
    telegram_username="test_user",
    customer_name="Тест Тестович",
    customer_phone="+79999999999",
    delivery_address="ул. Тестовая, д. 1",
    total_amount=1000.0,
    status=OrderStatus.confirmed,  # Подтвержден - должен отобразиться на кухне!
    order_type="Доставка",
    branch_id=branch.id,
    iiko_creation_time=datetime.utcnow(),
    expected_time=datetime.utcnow() + timedelta(minutes=45),
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
)
session.add(test_order)
session.commit()
session.refresh(test_order)

# Создаем позиции для заказа
item1 = OrderItem(
    order_id=test_order.id,
    product_id=332, # Сырная Пицца
    product_name="Сырная Пицца",
    quantity=1,
    price=600.0,
    total=600.0,
    kitchen_status="pending",
    kitchen_zone_id=2 # Кухня
)
item2 = OrderItem(
    order_id=test_order.id,
    product_id=272, #  кольца
    product_name="Луковые кольца 6 шт",
    quantity=2,
    price=190.0,
    total=380.0,
    kitchen_status="pending",
    kitchen_zone_id=2 # Кухня
)

session.add(item1)
session.add(item2)
session.commit()

print(f"Created test order with ID: {test_order.id} and status: {test_order.status} for branch: {branch.name}")
