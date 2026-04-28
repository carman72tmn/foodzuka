<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class ClientBonusHistory extends Model
{
    use HasFactory;

    protected $table = 'client_bonus_history';

    protected $fillable = [
        'client_id',
        'type', // accrual, write_off
        'amount',
        'order_id',
        'transaction_date',
    ];

    protected $casts = [
        'transaction_date' => 'datetime',
        'amount' => 'decimal:2',
    ];

    public function client()
    {
        return $this->belongsTo(Client::class, 'client_id');
    }
}
