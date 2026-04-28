SELECT id, name, surname, phone FROM customers WHERE surname IS NOT NULL AND length(surname) > 0 LIMIT 10;
