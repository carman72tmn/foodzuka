<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class ClientAddressHistory extends Model
{
    use HasFactory;

    protected $table = 'client_addresses_history';

    protected $fillable = [
        'client_id',
        'city',
        'street',
        'house',
        'apartment',
        'last_used_at',
        'is_active',
    ];

    protected $casts = [
        'last_used_at' => 'datetime',
        'is_active' => 'boolean',
    ];

    public function client()
    {
        return $this->belongsTo(Client::class, 'client_id');
    }
}
