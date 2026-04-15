import re
import os

sync_service_path = '/root/foodzuka/backend/app/services/iiko_sync_service.py'

NEW_SYNC_PRICES_BLOCK = """
    async def sync_prices(self, session: Session) -> Dict[str, Any]:
        \"\"\"Синхронизация только цен из iiko (с поддержкой v2)\"\"\"
        log = SyncLog(sync_type="prices", status="running")
        session.add(log)
        session.commit()
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        org_id = settings_db.organization_id if settings_db else None
        ext_menu_id = settings_db.external_menu_id if settings_db else None
        try:
            if ext_menu_id:
                logger.info("Syncing prices via External Menu API v2")
                menu_data = await iiko_service.get_external_menu_by_id(ext_menu_id, api_login=api_login, organization_id=org_id)
                updated = await self._sync_prices_from_v2(session, menu_data)
            else:
                logger.info("Syncing prices via Legacy Nomenclature API")
                nomenclature = await iiko_service.get_nomenclature(api_login=api_login, organization_id=org_id)
                updated = await self._sync_prices_from_v1(session, nomenclature or {})

            session.commit()
            log.status = "success"
            log.products_count = updated
            log.details = f"Updated prices for {updated} products"
            session.commit()
            return {"success": True, "products_updated": updated, "message": log.details}
        except Exception as e:
            logger.error(f"Price sync failed: {e}")
            log.status = "error"
            log.details = str(e)
            session.commit()
            raise

    async def _sync_prices_from_v1(self, session: Session, nomenclature: Dict[str, Any]) -> int:
        updated = 0
        if "products" in nomenclature:
            from app.models.product import Product
            from sqlalchemy import select
            for iiko_product in nomenclature["products"]:
                product = session.exec(select(Product).where(Product.iiko_id == iiko_product["id"])).first()
                if product:
                    price = 0
                    if iiko_product.get("sizePrices"):
                        price = iiko_product["sizePrices"][0].get("price", {}).get("currentPrice", 0)
                    if product.price != price:
                        product.price = price
                        product.updated_at = datetime.utcnow()
                        updated += 1
        return updated

    async def _sync_prices_from_v2(self, session: Session, menu_data: Dict[str, Any]) -> int:
        updated = 0
        from app.models.product import Product, ProductSize
        from sqlalchemy import select
        for iiko_cat in menu_data.get("itemCategories", []):
            for iiko_item in iiko_cat.get("items", []):
                item_iiko_id = iiko_item.get("itemId")
                if not item_iiko_id: continue
                product = session.exec(select(Product).where(Product.iiko_id == item_iiko_id)).first()
                if product:
                    size_prices = iiko_item.get("sizePrices", [])
                    if size_prices:
                        default_size = next((sp for sp in size_prices if sp.get("isDefault")), size_prices[0])
                        new_price = default_size.get("price", {}).get("currentPrice", 0)
                        if product.price != new_price:
                            product.price = new_price
                            product.updated_at = datetime.utcnow()
                            updated += 1
                        for sp in size_prices:
                            size = session.exec(select(ProductSize).where(ProductSize.product_id == product.id, ProductSize.iiko_id == (sp.get("sizeId") or "default"))).first()
                            if size and size.price != sp.get("price", {}).get("currentPrice", 0):
                                size.price = sp.get("price", {}).get("currentPrice", 0)
                                size.updated_at = datetime.utcnow()
        return updated
"""

if __name__ == '__main__':
    with open(sync_service_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Safely replace the old sync_prices method
    # It starts with '    async def sync_prices' and ends before the next '    async def'
    pattern = r'    async def sync_prices\(self, session: Session\) -> Dict\[str, Any\]:.*?async def sync_stop_lists'
    replacement = NEW_SYNC_PRICES_BLOCK + '\\n\\n    async def sync_stop_lists'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(sync_service_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Price sync updated to v2.")
