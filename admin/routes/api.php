<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\ProductController;
use App\Http\Controllers\Api\CategoryController;
use App\Http\Controllers\Api\OrderController;

use App\Http\Controllers\Api\ClientController;

Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');

Route::apiResource('products', ProductController::class);
Route::apiResource('categories', CategoryController::class);
Route::get('orders/by-iiko-id/{id}', [OrderController::class, 'getByIikoId']);
Route::apiResource('orders', OrderController::class);

Route::get('clients', [ClientController::class, 'index']);
Route::get('loyalty-categories', [ClientController::class, 'categories']);
Route::delete('clients/delete-all-force', [ClientController::class, 'destroyAll']);
Route::get('clients/{id}', [ClientController::class, 'show']);
Route::put('clients/{id}', [ClientController::class, 'update']);
Route::post('clients/{id}/sync-iiko-orders', [ClientController::class, 'syncIikoOrders']);
Route::post('clients/{id}/sync-bonus-history', [ClientController::class, 'syncBonusHistory']);
Route::post('clients/{id}/sync-full', [ClientController::class, 'syncFull']);
Route::post('clients/{id}/bonus-operation', [ClientController::class, 'handleBonusOperation']);
Route::put('clients/{id}/addresses/{address_id}/toggle', [ClientController::class, 'toggleAddressStatus']);


    // Proxy requests to the FastAPI backend
    Route::any('v1/{path}', function (Request $request, $path) {
        $backendUrl = env('BACKEND_URL', 'http://backend:8000/api/v1/');
        $url = rtrim($backendUrl, '/') . '/' . trim($path, '/') . '/';
    // Get query parameters string
    $queryString = $request->getQueryString();
    if ($queryString) {
        $url .= '?' . $queryString;
    }

    $headers = collect($request->header())->mapWithKeys(function ($values, $key) {
        return [$key => $values[0]];
    })->except(['host', 'content-length', 'content-type'])->toArray();

    // Adding Content-Type manually if present
    if ($request->header('Content-Type')) {
        $headers['Content-Type'] = $request->header('Content-Type');
    }

    // Proxy the request using Laravel HTTP client
    try {
        $response = \Illuminate\Support\Facades\Http::withOptions([
            'allow_redirects' => true,
        ])
        ->withHeaders($headers)
        ->send($request->method(), $url, [
            'body' => $request->getContent()
        ]);

        return response($response->body(), $response->status())
            ->withHeaders($response->headers());
            
    } catch (\Exception $e) {
        return response()->json([
            'error' => 'Backend connection failed',
            'message' => $e->getMessage()
        ], 502);
    }
})->where('path', '.*');
