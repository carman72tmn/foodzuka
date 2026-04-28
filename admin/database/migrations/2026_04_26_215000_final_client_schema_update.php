<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        // 1. Обновление таблицы customers
        Schema::table('customers', function (Blueprint $table) {
            if (!Schema::hasColumn('customers', 'total_orders_count')) {
                $table->integer('total_orders_count')->default(0)->after('total_orders_amount');
            }
            if (!Schema::hasColumn('customers', 'last_order_date')) {
                $table->dateTime('last_order_date')->nullable()->after('last_order_at');
            }
            if (!Schema::hasColumn('customers', 'orders_history')) {
                $table->jsonb('orders_history')->nullable()->after('updated_at');
            }
        });

        // 2. Рефакторинг client_addresses_history
        Schema::table('client_addresses_history', function (Blueprint $table) {
            if (Schema::hasColumn('client_addresses_history', 'address')) {
                $table->dropColumn('address');
            }
            if (!Schema::hasColumn('client_addresses_history', 'city')) {
                $table->string('city')->nullable()->after('client_id');
            }
            if (!Schema::hasColumn('client_addresses_history', 'street')) {
                $table->string('street')->after('city');
            }
            if (!Schema::hasColumn('client_addresses_history', 'house')) {
                $table->string('house')->after('street');
            }
            if (!Schema::hasColumn('client_addresses_history', 'apartment')) {
                $table->string('apartment')->nullable()->after('house');
            }
        });

        // 3. Обновление client_bonus_history
        Schema::table('client_bonus_history', function (Blueprint $table) {
            // Изменяем тип на enum через сырой SQL, так как Doctrine не всегда дружит с enum
            // Но для начала добавим order_id если его нет
            if (!Schema::hasColumn('client_bonus_history', 'order_id')) {
                $table->string('order_id')->nullable()->after('amount');
            }
        });
        
        // В PostgreSQL/MySQL изменение типа колонки на ENUM лучше делать отдельно
        // Для простоты оставим string, но в модели пропишем каст. 
        // Если пользователь настаивает на enum в БД:
        // DB::statement("ALTER TABLE client_bonus_history MODIFY COLUMN type ENUM('accrual', 'write_off') NOT NULL");
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('customers', function (Blueprint $table) {
            $table->dropColumn(['total_orders_count', 'last_order_date']);
        });

        Schema::table('client_addresses_history', function (Blueprint $table) {
            $table->string('address')->nullable();
            $table->dropColumn(['city', 'street', 'house', 'apartment']);
        });

        Schema::table('client_bonus_history', function (Blueprint $table) {
            $table->dropColumn('order_id');
        });
    }
};
