<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Order;
use Illuminate\Http\Request;

class OrderController extends Controller
{
    public function index()
    {
        return Order::with('items.product')->latest()->get();
    }

    public function show($id)
    {
        return Order::with('items.product')->findOrFail($id);
    }
    
    public function update(Request $request, $id)
    {
        $order = Order::findOrFail($id);
        $order->update($request->only('status', 'comment'));
        return $order;
    }

    public function getByIikoId($id)
    {
        return Order::with('items.product')->where('iiko_order_id', $id)->firstOrFail();
    }
}
