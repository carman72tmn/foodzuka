<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Cache;
use Carbon\Carbon;

class IikoService
{
    protected $apiKey;
    protected $baseUrl;
    protected $organizationId;

    public function __construct()
    {
        // Приоритет - настройки из базы данных
        $settings = \App\Models\IikoSetting::first();
        
        if ($settings) {
            $this->apiKey = $settings->api_login;
            $this->organizationId = $settings->organization_id;
        } else {
            $this->apiKey = config('services.iiko.api_key');
            $this->organizationId = config('services.iiko.organization_id');
        }

        \Log::debug("IikoService initialized with OrgId: {$this->organizationId}, API Key: " . substr($this->apiKey, 0, 5) . "...");
        
        $this->baseUrl = rtrim(config('services.iiko.base_url', 'https://api-ru.iiko.services'), '/');
    }

    /**
     * Получить токен доступа iiko Cloud
     */
    public function getApiToken()
    {
        return Cache::remember('iiko_cloud_token_' . $this->apiKey, 300, function () {
            $response = Http::post($this->baseUrl . '/api/1/access_token', [
                'apiLogin' => $this->apiKey
            ]);

            if ($response->successful()) {
                return $response->json()['token'];
            }

            throw new \Exception('Ошибка получения токена iiko: ' . $response->body());
        });
    }

    /**
     * Синхронизация истории заказов клиента за указанный период
     */
    public function syncClientOrdersHistory($client, $months = 12)
    {
        $token = $this->getApiToken();
        
        // iiko Cloud требует формат yyyy-MM-dd HH:mm:ss.fff
        $dateFrom = now()->subMonths($months)->format('Y-m-d H:i:s.000');
        $dateTo = now()->format('Y-m-d H:i:s.000');

        // Приоритет: iiko_id (uid), если есть. Иначе - телефон.
        $endpoint = '/api/1/deliveries/history/by_delivery_date_and_phone';
        $payload = [
            "organizationIds" => [$this->organizationId],
            "deliveryDateFrom" => $dateFrom,
            "deliveryDateTo" => $dateTo,
            "rowsCount" => 200
        ];

        if ($client->iiko_id) {
            $endpoint = '/api/1/deliveries/history/by_delivery_date_and_customer_id';
            $payload["customerId"] = $client->iiko_id;
            \Log::debug("Using customerId for iiko history sync: {$client->iiko_id}");
        } else {
            $phone = $client->phone;
            if ($phone && !str_starts_with($phone, '+')) {
                $phone = '+' . $phone;
            }
            $payload["phone"] = $phone;
            \Log::debug("Using phone for iiko history sync: {$phone}");
        }

        \Log::info("Requesting iiko order history", [
            'endpoint' => $endpoint,
            'payload' => $payload
        ]);

        $response = Http::withToken($token)
            ->timeout(20)
            ->post($this->baseUrl . $endpoint, $payload);

        if (!$response->successful()) {
            \Log::error("Iiko Orders History Error (Status {$response->status()}): " . $response->body());
            throw new \Exception("Ошибка iiko API: " . $response->status() . " " . $response->body());
        }

        if ($response->successful()) {
            $data = $response->json();
            // iiko возвращает массив ordersByOrganizations
            $orgOrders = collect($data['ordersByOrganizations'] ?? [])
                ->where('organizationId', $this->organizationId)
                ->first();
            
            $orders = $orgOrders['orders'] ?? [];
            
            // Получаем ID заказов из iiko
            $iikoOrderIds = collect($orders)->pluck('id')->toArray();
            
            // Проверяем наличие этих заказов в нашей локальной базе
            $localOrders = \App\Models\Order::whereIn('iiko_order_id', $iikoOrderIds)
                ->pluck('iiko_order_id')
                ->toArray();

            // Форматируем новые заказы
            $newFormattedOrders = collect($orders)->map(function ($order) use ($localOrders) {
                // Извлекаем блюда
                $items = collect($order['order']['items'] ?? [])->map(function($item) {
                    return [
                        'productId' => $item['productId'] ?? '',
                        'name' => $item['name'] ?? 'Неизвестное блюдо',
                        'amount' => $item['amount'] ?? 0,
                        'sum' => $item['sum'] ?? 0,
                    ];
                })->toArray();

                return [
                    'id' => $order['id'],
                    'number' => $order['order']['number'] ?? 'б/н',
                    'sum' => $order['order']['sum'] ?? 0,
                    'status' => $order['order']['status'] ?? '—',
                    'date' => isset($order['order']['created']['date']) 
                        ? Carbon::parse($order['order']['created']['date'])->format('Y-m-d H:i:s') 
                        : null,
                    'details' => $items,
                    'exists_locally' => in_array($order['id'], $localOrders)
                ];
            });

            // Получаем текущую историю из БД клиента (jsonb)
            $currentHistory = collect($client->orders_history ?? []);

            // Объединяем старые и новые заказы, предотвращая дубликаты по ID
            // Используем keyBy('id') для эффективного слияния
            $mergedHistory = $currentHistory->keyBy('id')->merge($newFormattedOrders->keyBy('id'));

            // Упорядочиваем по ID заказа (как просил пользователь)
            // Примечание: iiko ID — это UUID, но мы следуем инструкции по сортировке
            $finalHistory = $mergedHistory->values()->sortBy('id')->values()->toArray();

            // Сохраняем в БД клиента для кэша
            $client->orders_history = $finalHistory;
            $client->save();

            return $finalHistory;
        }

        throw new \Exception('Ошибка iiko API (Orders History): ' . $response->body());
    }

    /**
     * Синхронизация истории транзакций по бонусам
     */
    public function syncClientBonusHistory($client)
    {
        if (!$client->iiko_customer_id) {
            throw new \Exception('У клиента отсутствует iiko ID');
        }

        $token = $this->getApiToken();
        
        $dateFrom = now()->subMonths(12)->format('Y-m-d 00:00:00.000');
        $dateTo = now()->format('Y-m-d 23:59:59.000');

        $payload = [
            "organizationId" => $this->organizationId,
            "customerId" => $client->iiko_customer_id,
            "dateFrom" => $dateFrom,
            "dateTo" => $dateTo,
            "pageNumber" => 0,
            "pageSize" => 100
        ];

        $response = Http::withToken($token)
            ->timeout(20)
            ->post($this->baseUrl . '/api/1/loyalty/iiko/customer/transactions/by_date', $payload);

        if ($response->successful()) {
            $data = $response->json();
            $transactions = $data['transactions'] ?? [];
            
            // Удаляем старую локальную историю и записываем новую
            \App\Models\ClientBonusHistory::where('client_id', $client->id)->delete();
            
            foreach ($transactions as $tx) {
                $amount = (float)($tx['amount'] ?? 0);
                $type = $amount >= 0 ? 'accrual' : 'deduction';
                
                \App\Models\ClientBonusHistory::create([
                    'client_id' => $client->id,
                    'type' => $type,
                    'amount' => $amount,
                    'transaction_date' => Carbon::parse($tx['date'])->format('Y-m-d H:i:s'),
                    'comment' => $tx['comment'] ?? ''
                ]);
            }
            
            return $transactions;
        }

        throw new \Exception('Ошибка iiko API (Bonus History): ' . $response->body());
    }

    /**
     * Получить все доступные категории клиентов
     */
    public function getLoyaltyCategories()
    {
        $token = $this->getApiToken();
        
        $response = Http::withToken($token)
            ->timeout(20)
            ->post($this->baseUrl . '/api/1/loyalty/iiko/customer_category', [
                'organizationId' => $this->organizationId
            ]);

        if ($response->successful()) {
            return $response->json()['customerCategories'] ?? [];
        }

        throw new \Exception('Ошибка iiko API (Get Categories): ' . $response->body());
    }

    /**
     * Добавить категорию клиенту
     */
    public function addCustomerCategory($customerId, $categoryId)
    {
        $token = $this->getApiToken();
        
        $response = Http::withToken($token)
            ->timeout(20)
            ->post($this->baseUrl . '/api/1/loyalty/iiko/customer_category/add', [
                'organizationId' => $this->organizationId,
                'customerId' => $customerId,
                'categoryId' => $categoryId
            ]);

        if ($response->successful()) {
            return $response->json();
        }

        throw new \Exception('Ошибка iiko API (Add Category): ' . $response->body());
    }

    /**
     * Удалить категорию у клиента
     */
    public function removeCustomerCategory($customerId, $categoryId)
    {
        $token = $this->getApiToken();
        
        $response = Http::withToken($token)
            ->timeout(20)
            ->post($this->baseUrl . '/api/1/loyalty/iiko/customer_category/remove', [
                'organizationId' => $this->organizationId,
                'customerId' => $customerId,
                'categoryId' => $categoryId
            ]);

        if ($response->successful()) {
            return $response->json();
        }

        throw new \Exception('Ошибка iiko API (Remove Category): ' . $response->body());
    }

    /**
     * Обновить данные гостя в iiko
     */
    public function updateCustomer($client, $data)
    {
        $token = $this->getApiToken();

        // Transport API ожидает плоскую структуру с organizationId в корне
        $payload = array_merge([
            "organizationId" => $this->organizationId,
            "id" => $client->iiko_customer_id,
            "phone" => $client->phone,
            "name" => $client->name,
            "surName" => $client->surname, // iiko использует surName
            "email" => $client->email,
        ], $data);

        \Log::debug("Iiko updateCustomer payload: " . json_encode($payload));

        $response = Http::withToken($token)
            ->timeout(20)
            ->post($this->baseUrl . '/api/1/loyalty/iiko/customer/create_or_update', $payload);

        if ($response->successful()) {
            return $response->json();
        }

        throw new \Exception('Ошибка iiko API (Update Customer): ' . $response->body());
    }

    /**
     * Запустить полную синхронизацию через Python-бэкенд (FastAPI)
     */
    public function triggerFullSyncOnBackend($client)
    {
        $backendUrl = env('BACKEND_URL', 'http://backend:8000/api/v1/');
        $url = rtrim($backendUrl, '/') . "/customers/{$client->id}/full-sync";

        \Log::info("Triggering full sync on backend for client {$client->id}: {$url}");

        $response = Http::timeout(10)->post($url);

        if ($response->successful()) {
            return $response->json();
        }

        throw new \Exception('Ошибка связи с Python-бэкендом: ' . $response->body());
    }

    /**
     * Начислить бонусы клиенту
     */
    public function topupCustomerWallet($customerId, $amount, $walletId = null, $comment = '')
    {
        $token = $this->getApiToken();
        
        $payload = [
            'organizationId' => $this->organizationId,
            'customerId' => $customerId,
            'amount' => $amount,
            'comment' => $comment
        ];

        if ($walletId) {
            $payload['walletId'] = $walletId;
        }

        $response = Http::withToken($token)
            ->timeout(20)
            ->post($this->baseUrl . '/api/1/loyalty/iiko/customer/wallet/topup', $payload);

        if ($response->successful()) {
            return $response->json();
        }

        throw new \Exception('Ошибка iiko API (Topup): ' . $response->body());
    }

    /**
     * Списать бонусы у клиента
     */
    public function chargeoffCustomerWallet($customerId, $amount, $walletId = null, $comment = '')
    {
        $token = $this->getApiToken();
        
        $payload = [
            'organizationId' => $this->organizationId,
            'customerId' => $customerId,
            'amount' => $amount,
            'comment' => $comment
        ];

        if ($walletId) {
            $payload['walletId'] = $walletId;
        }

        $response = Http::withToken($token)
            ->timeout(20)
            ->post($this->baseUrl . '/api/1/loyalty/iiko/customer/wallet/chargeoff', $payload);

        if ($response->successful()) {
            return $response->json();
        }

        throw new \Exception('Ошибка iiko API (Chargeoff): ' . $response->body());
    }
}
