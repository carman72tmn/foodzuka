<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Client extends Model
{
    use HasFactory;

    protected $table = 'customers';

    protected $fillable = [
        'phone',
        'name',
        'surname',
        'first_name',
        'last_name',
        'email',
        'birthday',
        'bonus_points',
        'uid',
        'iiko_id',
        'iiko_customer_id',
        'is_high_risk',
        'risk_reason',
        'iiko_notes',
        'iiko_categories',
        'additional_phones',
        'total_purchases_sum',
        'total_orders_count',
        'last_order_date',
        'last_iiko_order_id',
        'is_new_guest',
        'gender',
        'is_marketing_consented',
        'is_system_notifications_consented',
        'consent_status',
        'marketing_consents',
        'vk_user_id',
    ];

    protected $casts = [
        'birthday' => 'date',
        'last_order_date' => 'datetime',
        'is_high_risk' => 'boolean',
        'is_new_guest' => 'boolean',
        'is_marketing_consented' => 'boolean',
        'is_system_notifications_consented' => 'boolean',
        'bonus_points' => 'decimal:2',
        'total_purchases_sum' => 'decimal:2',
        'iiko_categories' => 'array',
        'additional_phones' => 'array',
        'orders_history' => 'array',
        'marketing_consents' => 'array',
    ];

    protected $appends = ['vk_link'];

    /**
     * Ссылка на профиль ВК
     */
    public function getVkLinkAttribute()
    {
        return $this->vk_user_id ? "https://vk.com/id{$this->vk_user_id}" : null;
    }

    /**
     * История адресов
     */
    public function addresses()
    {
        return $this->hasMany(ClientAddressHistory::class, 'client_id');
    }

    /**
     * История бонусов
     */
    public function bonuses()
    {
        return $this->hasMany(ClientBonusHistory::class, 'client_id');
    }

    /**
     * Заказы (локальные)
     */
    public function orders()
    {
        return $this->hasMany(Order::class, 'customer_id');
    }
}
