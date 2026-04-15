import re
import os

def patch_file(filepath, patterns_replacements):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for pattern, replacement in patterns_replacements:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. Patching schemas/__init__.py
schemas_patch = [
    (
        r'class OrderItemResponse\(BaseModel\):.*?model_config = ConfigDict\(from_attributes=True\)',
        '''class OrderItemResponse(BaseModel):
    """Ответ API с позицией заказа"""
    id: int
    product_id: Optional[int] = None
    product_name: str
    quantity: int
    price: Decimal
    total: Decimal
    size_name: Optional[str] = None
    size_iiko_id: Optional[str] = None
    comment: Optional[str] = None
    modifiers: Optional[List[Dict[str, Any]]] = []

    model_config = ConfigDict(from_attributes=True)'''
    ),
    (
        r'class OrderResponse\(BaseModel\):.*?model_config = ConfigDict\(from_attributes=True\)',
        '''class OrderResponse(BaseModel):
    """Ответ API с заказом"""
    id: int
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    total_amount: Decimal
    bonus_spent: Decimal
    total_discount: Decimal
    total_with_discount: Decimal = Decimal("0.00")
    branch_id: Optional[int] = None
    customer_id: Optional[int] = None
    iiko_order_id: Optional[str] = None
    external_number: Optional[str] = None
    terminal_group_id: Optional[str] = None
    terminal_group_name: Optional[str] = None
    payment_method: Optional[str] = None
    order_type: Optional[str] = None
    courier_name: Optional[str] = None
    delivery_zone: Optional[str] = None
    is_paid: bool = False
    city: Optional[str] = None
    status: OrderStatus
    spam_score: Optional[int] = None
    spam_info: Optional[str] = None
    comment: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[str] = None
    promo_code_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    order_items_details: Optional[List[Dict[str, Any]]] = None
    customer_info_details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)'''
    )
]

# 2. Patching iiko_sync_service.py
sync_service_path = '/root/foodzuka/backend/app/services/iiko_sync_service.py'

NEW_SYNC_MENU = """
    async def sync_menu(self, session: Session) -> Dict[str, Any]:
        \"\"\"Умная синхронизация меню. Использует External Menu API v2 если задан ID меню\"\"\"
        log = SyncLog(sync_type="menu", status="running")
        session.add(log)
        session.commit()
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        org_id = settings_db.organization_id if settings_db else None
        ext_menu_id = settings_db.external_menu_id if settings_db else None
        try:
            if ext_menu_id:
                logger.info(f"Syncing via External Menu API (ID: {ext_menu_id})")
                menu_data = await iiko_service.get_external_menu_by_id(ext_menu_id, api_login=api_login, organization_id=org_id)
                res = await self._sync_from_external_menu(session, menu_data, log)
            else:
                logger.info("Syncing via Legacy Nomenclature API")
                nomenclature = await iiko_service.get_nomenclature(api_login=api_login, organization_id=org_id)
                res = await self._sync_from_nomenclature(session, nomenclature, log)
            session.commit()
            log.status = "success"
            log.categories_count = res.get("categories_synced", 0)
            log.products_count = res.get("products_synced", 0)
            log.details = f"Synced {log.categories_count} categories, {log.products_count} products"
            session.commit()
            return res
        except Exception as e:
            logger.error(f"Menu sync failed: {e}")
            log.status = "error"
            log.details = str(e)
            session.commit()
            raise

    async def _sync_from_external_menu(self, session: Session, menu_data: Dict[str, Any], log: SyncLog) -> Dict[str, Any]:
        categories_synced = 0
        products_synced = 0
        item_categories = menu_data.get("itemCategories", [])
        for iiko_cat in item_categories:
            cat_iiko_id = iiko_cat.get("id")
            if not cat_iiko_id: continue
            category = session.exec(select(Category).where(Category.iiko_id == cat_iiko_id)).first()
            if not category:
                category = Category(name=iiko_cat.get("name", "Без названия"), iiko_id=cat_iiko_id, is_active=True)
                session.add(category)
            else:
                category.name = iiko_cat.get("name", category.name)
                category.is_active = True
                category.updated_at = datetime.utcnow()
            session.flush()
            categories_synced += 1
            for iiko_item in iiko_cat.get("items", []):
                item_iiko_id = iiko_item.get("itemId")
                if not item_iiko_id: continue
                size_prices = iiko_item.get("sizePrices", [])
                base_price = 0
                if size_prices:
                    default_size = next((sp for sp in size_prices if sp.get("isDefault")), size_prices[0])
                    base_price = default_size.get("price", {}).get("currentPrice", 0)
                product = session.exec(select(Product).where(Product.iiko_id == item_iiko_id)).first()
                if not product:
                    product = Product(name=iiko_item.get("name", "Без названия"), description=iiko_item.get("description"),
                                    price=base_price, category_id=category.id, iiko_id=item_iiko_id,
                                    article=iiko_item.get("sku"), is_available=True)
                    session.add(product)
                else:
                    product.name = iiko_item.get("name", product.name)
                    product.description = iiko_item.get("description")
                    product.price = base_price
                    product.category_id = category.id
                    product.article = iiko_item.get("sku")
                    product.is_available = True
                    product.updated_at = datetime.utcnow()
                img = iiko_item.get("buttonImageCroppedUrl") or (iiko_item.get("imageLinks", [None])[0] if iiko_item.get("imageLinks") else None)
                if img: product.image_url = img
                session.flush()
                # Sizes
                for sz in session.exec(select(ProductSize).where(ProductSize.product_id == product.id)).all(): session.delete(sz)
                for sp in size_prices:
                    session.add(ProductSize(product_id=product.id, iiko_id=sp.get("sizeId") or "default",
                                          name=sp.get("name") or "Стандарт", price=sp.get("price", {}).get("currentPrice", 0),
                                          is_default=sp.get("isDefault", False)))
                # Modifiers
                for mg_old in session.exec(select(ProductModifierGroup).where(ProductModifierGroup.product_id == product.id)).all(): session.delete(mg_old)
                for mg_data in iiko_item.get("modifierGroups", []):
                    mg = ProductModifierGroup(product_id=product.id, iiko_id=mg_data.get("modifierGroupId", ""),
                                            name=mg_data.get("name", "Группа модификаторов"),
                                            min_amount=mg_data.get("minQuantity", 0), max_amount=mg_data.get("maxQuantity", 1),
                                            is_required=mg_data.get("required", False))
                    session.add(mg)
                    session.flush()
                    for m_data in mg_data.get("modifiers", []):
                        session.add(ProductModifier(group_id=mg.id, iiko_id=m_data.get("modifierId", ""),
                                                  name=m_data.get("name", "Модификатор"), price=m_data.get("price", 0),
                                                  default_amount=m_data.get("defaultAmount", 0),
                                                  min_amount=m_data.get("minAmount", 0), max_amount=m_data.get("maxAmount", 1)))
                products_synced += 1
        return {"success": True, "categories_synced": categories_synced, "products_synced": products_synced}
"""

NEW_PROCESS_ORDER = """
    async def process_iiko_order(self, session: Session, iiko_order_data: Dict[str, Any], organization_id: str, iiko_card_data: Optional[Dict[str, Any]] = None):
        order_id_iiko = iiko_order_data.get("id")
        if not order_id_iiko: return
        if not hasattr(self, "_terminal_groups_cache"): self._terminal_groups_cache = {}
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        if not self._terminal_groups_cache:
            try:
                tgs = await iiko_service.get_terminal_groups(api_login=api_login, organization_id=organization_id)
                for tg_entry in tgs:
                    for tg in tg_entry.get("items", []): self._terminal_groups_cache[tg["id"]] = tg["name"]
            except: pass
        order = session.exec(select(Order).where(Order.iiko_order_id == order_id_iiko)).first()
        o_data = iiko_order_data.get("order", iiko_order_data)
        iiko_status = iiko_order_data.get("creationStatus") or o_data.get("status", "")
        status_map = {"New": OrderStatus.NEW, "Unconfirmed": OrderStatus.NEW, "WaitCooking": OrderStatus.CONFIRMED,
                      "ReadyForCooking": OrderStatus.CONFIRMED, "CookingStarted": OrderStatus.COOKING,
                      "CookingCompleted": OrderStatus.READY, "Waiting": OrderStatus.READY, "OnWay": OrderStatus.DELIVERING,
                      "Delivered": OrderStatus.DELIVERED, "Cancelled": OrderStatus.CANCELLED, "Error": OrderStatus.CANCELLED}
        mapped_status = status_map.get(str(iiko_status), OrderStatus.CONFIRMED)
        cancel_info = o_data.get("cancellationInfo")
        c_reason = cancel_info.get("message") if cancel_info else None
        sum_total = Decimal(str(o_data.get("sum", 0)))
        total_with_discount = Decimal(str(o_data.get("totalSum", sum_total)))
        phone = o_data.get("phone") or (o_data.get("customer") or {}).get("phone", "")
        customer = session.exec(select(Customer).where(Customer.phone == phone)).first() if phone else None
        source = o_data.get("sourceKey") or o_data.get("source")
        comment = o_data.get("comment")
        if not order:
            order = Order(iiko_order_id=order_id_iiko, status=mapped_status, total_amount=sum_total,
                         total_with_discount=total_with_discount, cancellation_reason=c_reason, 
                         customer_id=customer.id if customer else None, order_items_details=o_data.get("items", []),
                        comment=comment, source=source, branch_id=1)
            session.add(order)
        else:
            order.status = mapped_status
            order.total_amount = sum_total
            order.total_with_discount = total_with_discount
            order.cancellation_reason = c_reason or order.cancellation_reason
            order.comment = comment or order.comment
            order.order_items_details = o_data.get("items", [])
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(order, "order_items_details")
            session.add(order)
        session.flush()
        items_data = o_data.get("items", [])
        if isinstance(items_data, list):
            for ei in session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all(): session.delete(ei)
            for item in items_data:
                mods = [{"name": m.get("name"), "amount": m.get("amount"), "sum": m.get("sum")} for m in item.get("modifiers", [])]
                session.add(OrderItem(order_id=order.id, product_name=item.get("name"), quantity=int(item.get("amount", 1)),
                                    price=Decimal(str(item.get("price", 0))), total=Decimal(str(item.get("sum", 0))),
                                    size_name=item.get("size", {}).get("name") if isinstance(item.get("size"), dict) else None,
                                    comment=item.get("comment"), modifiers=mods))
        session.commit()
"""

print("Patching schemas...")
patch_file('/root/foodzuka/backend/app/schemas/__init__.py', schemas_patch)

print("Patching iiko_sync_service.py...")
with open(sync_service_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace sync_menu and inject helpers
content = content.replace("    async def sync_menu(self, session: Session) -> Dict[str, Any]:", 
                        "    async def _sync_from_nomenclature(self, session: Session, nomenclature: Dict[str, Any], log: SyncLog) -> Dict[str, Any]:")
content = content.replace("class IikoSyncService:", "class IikoSyncService:\\n" + NEW_SYNC_MENU)

# 2. Replace process_iiko_order
content = re.sub(r"    async def process_iiko_order\(self, session: Session,.*?    async def sync_order_by_id", 
                NEW_PROCESS_ORDER + "\\n\\n    async def sync_order_by_id", content, flags=re.DOTALL)

with open(sync_service_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done.")
