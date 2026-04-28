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
        // История адресов
        if (!Schema::hasTable('client_addresses_history')) {
            Schema::create('client_addresses_history', function (Blueprint $table) {
                $table->id();
                $table->unsignedBigInteger('client_id');
                $table->string('address');
                $table->timestamp('last_used_at')->nullable();
                $table->integer('orders_count')->default(0);
                $table->timestamps();

                $table->foreign('client_id')->references('id')->on('customers')->onDelete('cascade');
            });
        }

        // История бонусов
        if (!Schema::hasTable('client_bonus_history')) {
            Schema::create('client_bonus_history', function (Blueprint $table) {
                $table->id();
                $table->unsignedBigInteger('client_id');
                $table->string('type'); // accrual, deduction
                $table->decimal('amount', 10, 2);
                $table->timestamp('transaction_date');
                $table->string('comment')->nullable();
                $table->timestamps();

                $table->foreign('client_id')->references('id')->on('customers')->onDelete('cascade');
            });
        }
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('client_bonus_history');
        Schema::dropIfExists('client_addresses_history');
    }
};
