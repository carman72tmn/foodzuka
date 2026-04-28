<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class IikoSetting extends Model
{
    protected $table = 'iiko_settings';

    protected $fillable = [
        'api_login',
        'organization_id',
        'resto_url',
        'resto_login',
        'resto_password',
        'address_format',
    ];

    public $timestamps = true;
}
