-- Fix shifts
UPDATE shifts SET cancelled_orders_count = 0 WHERE cancelled_orders_count IS NULL;
UPDATE shifts SET deliveries_count = 0 WHERE deliveries_count IS NULL;
UPDATE shifts SET deliveries_revenue = 0 WHERE deliveries_revenue IS NULL;

-- Fix users
UPDATE users SET is_active = TRUE WHERE is_active IS NULL;
UPDATE users SET is_superuser = FALSE WHERE is_superuser IS NULL;

-- Fix custom_polygons (already done but for safety)
UPDATE custom_polygons SET min_order_amount = 0.0 WHERE min_order_amount IS NULL;
UPDATE custom_polygons SET delivery_cost = 0.0 WHERE delivery_cost IS NULL;
UPDATE custom_polygons SET free_delivery_threshold = 0.0 WHERE free_delivery_threshold IS NULL;
UPDATE custom_polygons SET fill_color = '#4caf50' WHERE fill_color IS NULL;
