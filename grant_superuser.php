<?php
define('LARAVEL_START', microtime(true));
require __DIR__.'/vendor/autoload.php';
$app = require_once __DIR__.'/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use App\Models\User;
use Illuminate\Support\Facades\Hash;

$user = User::where('login', '0001')->first();
if ($user) {
    $user->is_superuser = true;
    $user->is_active = true;
    $user->save();
    echo "User 0001 is now SUPERUSER\n";
} else {
    echo "User 0001 NOT FOUND\n";
}
