<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Client;
use App\Services\IikoService;
use Illuminate\Http\Request;
use Carbon\Carbon;

class ClientController extends Controller
{
    protected $iikoService;

    public function __construct(IikoService $iikoService)
    {
        $this->iikoService = $iikoService;
    }

    /**
     * Список клиентов с пагинацией
     */
    public function index(Request $request)
    {
        $query = Client::query();

        if ($request->has('search')) {
            $search = $request->get('search');
            $query->where(function($q) use ($search) {
                $q->where('phone', 'like', "%{$search}%")
                  ->orWhere('name', 'like', "%{$search}%")
                  ->orWhere('surname', 'like', "%{$search}%")
                  ->orWhere('first_name', 'like', "%{$search}%")
                  ->orWhere('last_name', 'like', "%{$search}%")
                  ->orWhere('email', 'like', "%{$search}%");
            });
        }

        return $query->orderBy('created_at', 'desc')->paginate(20);
    }

    /**
     * Детальная информация о клиенте с расчетом статистики
     */
    public function show($id)
    {
        $client = Client::with(['addresses', 'bonuses'])->findOrFail($id);
        
        return response()->json([
            'client' => $client,
            'orders_history' => $client->orders_history ?? [],
            'statistics' => [
                'total_orders' => (int)$client->total_orders_count,
                'total_sum' => (float)$client->total_purchases_sum,
                'registration_date' => $client->registration_date ? Carbon::parse($client->registration_date)->format('d.m.Y') : ($client->created_at ? $client->created_at->format('d.m.Y') : '—'),
                'last_order' => [
                    'date' => $client->last_order_date ? Carbon::parse($client->last_order_date)->format('d.m.Y, H:i') : '—',
                    'iiko_id' => $client->last_iiko_order_id ?? '—'
                ]
            ],
            'loyalty' => [
                'bonus_points' => (float)$client->bonus_points,
                'categories' => $client->iiko_categories ?? $client->loyalty_categories ?? [],
                'additional_phones' => $client->additional_phones ?? []
            ]
        ]);
    }

    /**
     * Прямая синхронизация истории заказов клиента из iiko
     */
    public function syncIikoOrders(Request $request, $id)
    {
        $client = Client::findOrFail($id);
        $months = $request->input('months', 12);
        
        try {
            $orders = $this->iikoService->syncClientOrdersHistory($client, $months);
            return response()->json($orders);
        } catch (\Exception $e) {
            \Log::error("Sync Iiko Orders Error for client {$id}: " . $e->getMessage());
            \Log::error($e->getTraceAsString());
            
            return response()->json([
                'error' => 'Ошибка синхронизации с iiko',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Прямая синхронизация истории бонусов из iiko
     */
    public function syncBonusHistory($id)
    {
        $client = Client::findOrFail($id);
        
        try {
            $this->iikoService->syncClientBonusHistory($client);
            $client->refresh();
            return response()->json($client->bonuses);
        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Ошибка синхронизации бонусов',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Запуск полной фоновой синхронизации через Python-бэкенд
     */
    public function syncFull($id)
    {
        $client = Client::findOrFail($id);
        
        try {
            $result = $this->iikoService->triggerFullSyncOnBackend($client);
            return response()->json([
                'success' => true,
                'message' => 'Задача полной синхронизации запущена',
                'data' => $result
            ]);
        } catch (\Exception $e) {
            \Log::error("Full Sync Error for client {$id}: " . $e->getMessage());
            return response()->json([
                'error' => 'Ошибка запуска полной синхронизации',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Получить справочник всех категорий iiko
     */
    public function categories()
    {
        try {
            $categories = $this->iikoService->getLoyaltyCategories();
            return response()->json($categories);
        } catch (\Exception $e) {
            return response()->json(['error' => $e->getMessage()], 500);
        }
    }

    /**
     * Обновить данные клиента
     */
    public function update(Request $request, $id)
    {
        $client = Client::findOrFail($id);
        
        $validated = $request->validate([
            'name' => 'sometimes|string|max:255|nullable',
            'surname' => 'sometimes|string|max:255|nullable',
            'first_name' => 'sometimes|string|max:255|nullable',
            'last_name' => 'sometimes|string|max:255|nullable',
            'birthday' => 'sometimes|date|nullable',
            'gender' => 'sometimes|string|max:50|nullable',
            'email' => 'sometimes|email|nullable',
            'iiko_categories' => 'sometimes|array',
            'additional_phones' => 'sometimes|array',
            'marketing_consents' => 'sometimes|array',
            'is_high_risk' => 'sometimes|boolean',
            'risk_reason' => 'sometimes|string|nullable',
        ]);

        // Подготовка данных для iiko
        $iikoData = [];
        if (isset($validated['name'])) $iikoData['name'] = $validated['name'];
        if (isset($validated['surname'])) $iikoData['surName'] = $validated['surname'];
        if (isset($validated['email'])) $iikoData['email'] = $validated['email'];
        
        if (isset($validated['birthday'])) {
            $iikoData['birthday'] = $validated['birthday'] 
                ? Carbon::parse($validated['birthday'])->format('Y-m-d H:i:s.000') 
                : null;
        }

        if (isset($validated['gender'])) {
            $genderMap = ["Мужской" => 1, "Женский" => 2, "Не указан" => 0];
            $iikoData['sex'] = $genderMap[$validated['gender']] ?? 0;
        }

        // Маркетинговые согласия
        if (isset($validated['marketing_consents'])) {
            $consents = $validated['marketing_consents'];
            $iikoData['shouldReceivePromoActionsInfo'] = (bool)($consents['promo'] ?? true);
            $iikoData['shouldReceiveLoyaltyInfo'] = (bool)($consents['loyalty'] ?? true);
            $iikoData['shouldReceiveOrderStatusInfo'] = (bool)($consents['order_status'] ?? true);
        }

        try {
            // 1. Обработка категорий (дифф) если есть iiko_customer_id
            if (isset($validated['iiko_categories']) && $client->iiko_customer_id) {
                $oldCategories = collect($client->iiko_categories ?? [])->pluck('id')->toArray();
                $newCategories = collect($validated['iiko_categories'])->pluck('id')->toArray();

                $toAdd = array_diff($newCategories, $oldCategories);
                $toRemove = array_diff($oldCategories, $newCategories);

                foreach ($toAdd as $catId) {
                    $this->iikoService->addCustomerCategory($client->iiko_customer_id, $catId);
                }
                foreach ($toRemove as $catId) {
                    $this->iikoService->removeCustomerCategory($client->iiko_customer_id, $catId);
                }
            }

            // 2. Отправляем основные данные в iiko
            if ($client->iiko_customer_id) {
                // Если есть risk_reason и он изменился, можем добавить его в комментарий iiko
                if (isset($validated['risk_reason']) && $validated['risk_reason'] !== $client->risk_reason) {
                    $iikoData['userData'] = $validated['risk_reason']; // userData часто используется для доп. инфо
                }
                
                $this->iikoService->updateCustomer($client, $iikoData);
            }

            // 3. Сохраняем локально
            $client->update($validated);

            return response()->json([
                'success' => true,
                'client' => $client->fresh()
            ]);
        } catch (\Exception $e) {
            \Log::error("Client Update Error: " . $e->getMessage());
            return response()->json([
                'error' => 'Ошибка при обновлении данных',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Удалить всех клиентов
     */
    public function destroyAll()
    {
        try {
            // Используем нативный TRUNCATE с CASCADE для PostgreSQL, чтобы очистить 
            // таблицу customers и все связанные таблицы (адреса, бонусы и т.д.)
            \DB::statement('TRUNCATE customers RESTART IDENTITY CASCADE');

            return response()->json([
                'success' => true,
                'message' => 'Все клиенты и связанные данные успешно удалены'
            ]);
        } catch (\Exception $e) {
            \Log::error("Error deleting all clients: " . $e->getMessage());
            return response()->json([
                'error' => 'Ошибка при удалении клиентов',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Обработка операций с бонусами (начисление/списание)
     */
    public function handleBonusOperation(Request $request, $id)
    {
        $client = Client::findOrFail($id);
        
        $validated = $request->validate([
            'operation' => 'required|in:topup,chargeoff',
            'amount' => 'required|numeric|min:0.01',
            'comment' => 'required|string|max:255'
        ]);

        if (!$client->iiko_customer_id) {
            return response()->json(['error' => 'У клиента отсутствует iiko ID'], 400);
        }

        try {
            if ($validated['operation'] === 'topup') {
                $this->iikoService->topupCustomerWallet(
                    $client->iiko_customer_id, 
                    $validated['amount'], 
                    null, 
                    $validated['comment']
                );
            } else {
                $this->iikoService->chargeoffCustomerWallet(
                    $client->iiko_customer_id, 
                    $validated['amount'], 
                    null, 
                    $validated['comment']
                );
            }

            // После успешной операции синхронизируем историю бонусов
            $this->iikoService->syncClientBonusHistory($client);
            $client->refresh();

            return response()->json([
                'success' => true,
                'message' => 'Операция успешно выполнена',
                'bonuses' => $client->bonuses
            ]);
        } catch (\Exception $e) {
            \Log::error("Bonus Operation Error for client {$id}: " . $e->getMessage());
            return response()->json([
                'error' => 'Ошибка выполнения операции с бонусами',
                'message' => $e->getMessage()
            ], 500);
        }
    }
    

    /**
     * Переключение статуса активности адреса (Актуальный/Неактуальный)
     */
    public function toggleAddressStatus(Request $request, $id, $address_id)
    {
        $client = Client::findOrFail($id);
        
        $address = \App\Models\ClientAddressHistory::where('client_id', $client->id)
            ->where('id', $address_id)
            ->firstOrFail();

        // Проверяем, есть ли поле is_active (на случай если миграция еще не выполнена на проде)
        if (\Illuminate\Support\Facades\Schema::hasColumn('client_addresses_history', 'is_active')) {
            $address->is_active = !$address->is_active;
            $address->save();
        }

        return response()->json([
            'success' => true,
            'is_active' => $address->is_active ?? true,
        ]);
    }
}
