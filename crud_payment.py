from db_helper import db
import crud_order

def pay_order(order_id):
    order = crud_order.get_order_by_id(order_id)
    if not order:
        return {"code":404,"msg":"订单不存在"}
    if order["status"] != "created":
        return {"code": 400, "msg": "该订单状态不允许支付"}
    existing_payment = db.execute_query(
        "SELECT id FROM payments WHERE order_id = ? AND status = 'success'",
    (order_id,)
    )
    if existing_payment:
        return {"code": 400, "msg": "该订单已支付，请勿重复支付"}
    
    db.execute_update(
    "INSERT INTO payments (order_id, amount, status) VALUES (?, ?, ?)",
    (order_id, order["total_price"], "success")
    )

    db.execute_update(
    "UPDATE orders SET status = 'paid' WHERE id = ?",
    (order_id,)
    )

    return {"code": 200, "msg": "支付成功", "data": {"order_id": order_id, "status": "paid"}}

def refund_order(order_id):
    """退款（只有已支付的订单才能退款）"""
    order = crud_order.get_order_by_id(order_id)
    if not order:
        return {"code":404,"msg":"订单不存在"}
    if order["status"] != "paid":
        return {"code": 400, "msg": "该订单状态不允许退款"}
    
    payment = db.execute_query(
        "SELECT id FROM payments WHERE order_id = ? AND status = 'success'",
        (order_id,)
        )
    if not payment:
        return {"code": 400, "msg": "该订单没有支付记录，无法退款"}

    
    db.execute_update(
    "UPDATE payments SET status = 'refunded' WHERE order_id = ? AND status = 'success'",
    (order_id,)
    )
    
    db.execute_update(
        "UPDATE orders SET status = 'refunded' WHERE id = ?",
        (order_id,)
        )
    
    return {"code": 200, "msg": "退款成功", "data": {"order_id": order_id, "status": "refunded"}}
    

def get_payment_by_order(order_id):
        """根据订单 ID 查询支付记录"""
        rows = db.execute_query("SELECT id,order_id,amount,status,created_at FROM payments WHERE order_id = ?",(order_id,))
        return rows[0] if rows else None
        