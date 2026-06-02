<?php

use Illuminate\Support\Facades\Route;

/**
 * Универсальный перехватчик роутов.
 * Используем getRequestUri(), так как Laravel может ошибочно определять 
 * /admin или /pers как базовый путь (baseUrl) и выдавать PATH = /
 */
Route::any('{any?}', function() {
    $uri = request()->getRequestUri();
    
    // Если запрос для панели сотрудников
    if (str_starts_with($uri, '/pers')) {
        return view('employee_application');
    }
    
    // Если запрос для основной админки
    if (str_starts_with($uri, '/admin')) {
        return view('application');
    }

    // По умолчанию редирект на основной сайт
    return redirect('https://vezuroll.ru');
})->where('any', '.*');