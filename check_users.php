<?php
use App\Models\User;

define('LARAVEL_START', microtime(true));
require __DIR__.'/vendor/autoload.php';
$app = require_once __DIR__.'/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

$users = User::all();
foreach($users as $u) {
    echo "Name: {$u->name} | Login: {$u->login}\n";
}
