<?php
try {
    $pdo = new PDO('pgsql:host=db;port=5432;dbname=foodtech_db', 'foodtech_user', 'your_strong_password');
    echo "PDO_SUCCESS\n";
} catch (Exception $e) {
    echo "PDO_ERROR: " . $e->getMessage() . "\n";
}
