<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Order extends Model
{
    use HasFactory;

    protected $fillable = [
        'telegram_user_id',
        'telegram_username',
        'branch_id',
        'customer_id',
        'customer_name',
        'customer_phone',
        'delivery_address',
        'total_amount',
        'bonus_spent',
        'total_discount',
        'promo_code_id',
        'status',
        'iiko_order_id',
        'comment',
        'bonus_accrued',
        'delivery_zone',
        'iiko_creation_time',
        'expected_time',
        'actual_time',
        'is_on_time',
        'delay_minutes',
        'admin_name',
        'order_type',
        'payment_method',
        'total_with_discount',
        'order_items_details',
        'discounts_details',
        'customer_info_details',
    ];

    protected $casts = [
        'total_amount' => 'decimal:2',
        'bonus_spent' => 'decimal:2',
        'bonus_accrued' => 'decimal:2',
        'total_discount' => 'decimal:2',
        'total_with_discount' => 'decimal:2',
        'iiko_creation_time' => 'datetime',
        'expected_time' => 'datetime',
        'actual_time' => 'datetime',
        'is_on_time' => 'boolean',
        'order_items_details' => 'array',
        'discounts_details' => 'array',
        'customer_info_details' => 'array',
        'created_at' => 'datetime',
    ];

    public function items()
    {
        return $this->hasMany(OrderItem::class);
    }
}
