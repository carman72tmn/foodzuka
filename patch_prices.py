import re
import os
from datetime import datetime

def patch_file(filepath, patterns_replacements):
    if not os.path.exists(filepath):
        print(f'File not found: {filepath}')
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for pattern, replacement in patterns_replacements:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

sync_service_path = '/root/foodzuka/backend/app/services/iiko_sync_service.py'

NEW_SYNC_PRICES = """
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

    # Check if already patched
    if 'async def _sync_prices_from_v1' not in content:
        # Step 1: Replace sync_prices with legacy version
        content = content.replace('async def sync_prices(self, session: Session) -> Dict[str, Any]:', 
                                'async def _sync_prices_from_v1(self, session: Session, nomenclature: Dict[str, Any]) -> int:')
        
        # Step 2: Refactor legacy logic to a helper (return count, remove logs)
        lines = content.split('\\n')
        new_lines = []
        skip = False
        for line in lines:
            if 'log = SyncLog(sync_type="prices"' in line: continue
            if 'session.add(log)' in line: continue
            if 'session.commit()' in line and not skip: continue
            if 'return {' in line and 'success' in line:
                new_lines.append('            return updated')
                continue
            new_lines.append(line)
        content = '\\n'.join(new_lines)
        
        # Step 3: Inject new sync_prices at class level
        content = content.replace('class IikoSyncService:', 'class IikoSyncService:\\n' + NEW_SYNC_PRICES)

    with open(sync_service_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Price sync updated to v2.")
