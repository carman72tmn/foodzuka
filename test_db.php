<?php
try {
    $p = new PDO('pgsql:host=db;dbname=foodtech_db', 'foodtech_user', '123456');
    echo 'OK';
} catch (Exception $e) {
    echo $e->getMessage();
}
?>
