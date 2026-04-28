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
            // Добавляем поля для соответствия архитектурному плану
            if (!Schema::hasColumn('customers', 'first_name')) {
                $table->string('first_name')->nullable()->after('name');
            }
            if (!Schema::hasColumn('customers', 'last_name')) {
                $table->string('last_name')->nullable()->after('surname');
            }
            if (!Schema::hasColumn('customers', 'uid')) {
                $table->string('uid')->nullable()->after('id');
            }
            if (!Schema::hasColumn('customers', 'iiko_id')) {
                $table->string('iiko_id')->nullable()->after('uid');
            }
            if (!Schema::hasColumn('customers', 'iiko_categories')) {
                $table->json('iiko_categories')->nullable()->after('iiko_notes');
            }
            if (!Schema::hasColumn('customers', 'additional_phones')) {
                $table->json('additional_phones')->nullable()->after('phone');
            }
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('customers', function (Blueprint $table) {
            $table->dropColumn([
                'first_name',
                'last_name',
                'uid',
                'iiko_id',
                'iiko_categories',
                'additional_phones'
            ]);
        });
    }
};
