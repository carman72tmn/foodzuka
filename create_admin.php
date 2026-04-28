<?php
define('LARAVEL_START', microtime(true));
require __DIR__.'/vendor/autoload.php';
$app = require_once __DIR__.'/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use App\Models\User;
use Illuminate\Support\Facades\Hash;

// Проверяем, существует ли уже
$existing = User::where('login', '0001')->first();
if ($existing) {
    $existing->password = Hash::make('121212');
    $existing->save();
    echo "User 0001 updated successfully\n";
} else {
    $user = new User();
    $user->login = '0001';
    $user->password = Hash::make('121212');
    $user->name = 'SuperAdmin';
    $user->email = 'admin@72roll.ru';
    $user->save();
    echo "User 0001 created successfully\n";
}
