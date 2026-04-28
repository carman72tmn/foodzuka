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
        Schema::table('customers', function (Blueprint $table) {
            // Риски
            if (!Schema::hasColumn('customers', 'is_high_risk')) {
                $table->boolean('is_high_risk')->default(false)->after('is_risk');
            }
            if (!Schema::hasColumn('customers', 'risk_reason')) {
                $table->string('risk_reason')->nullable()->after('is_high_risk');
            }
            if (!Schema::hasColumn('customers', 'iiko_notes')) {
                $table->text('iiko_notes')->nullable()->after('notes');
            }

            // Статистика (если нет)
            if (!Schema::hasColumn('customers', 'total_purchases_sum')) {
                $table->decimal('total_purchases_sum', 12, 2)->default(0)->after('total_orders_amount');
            }
            if (!Schema::hasColumn('customers', 'last_iiko_order_id')) {
                $table->string('last_iiko_order_id')->nullable()->after('last_order_id_iiko');
            }
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('customers', function (Blueprint $table) {
            $table->dropColumn(['is_high_risk', 'risk_reason', 'iiko_notes', 'total_purchases_sum', 'last_iiko_order_id']);
        });
    }
};
