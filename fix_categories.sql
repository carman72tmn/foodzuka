UPDATE customers 
SET loyalty_categories = (
    SELECT string_agg(cat->>'name', ', ') 
    FROM jsonb_array_elements(
        CASE 
            WHEN loyalty_categories ~ '^\[.*\]$' THEN loyalty_categories::jsonb 
            ELSE '[]'::jsonb 
        END
    ) AS cat
) 
WHERE loyalty_categories ~ '^\[.*\]$';

UPDATE customers SET categories = loyalty_categories WHERE categories ~ '^\[.*\]$';
